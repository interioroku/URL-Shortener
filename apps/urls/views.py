from django.views import View
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.response import Response
from apps.urls.models import ShortURL
from apps.urls.serializers import ShortURLSerializer
from apps.urls.services import URLShortenerService, RedirectService
from core.ratelimit import rate_limit
from core.cache import delete_short_url_cache

class ShortURLViewSet(viewsets.ModelViewSet):
    queryset = ShortURL.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = ShortURLSerializer

    @method_decorator(rate_limit(limit=10, period=60))
    def create(self, request, *args, **kwargs):
        """
        Creates a shortened URL. Rate limited to 10 requests per minute.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        original_url = serializer.validated_data["original_url"]
        expires_at = serializer.validated_data.get("expires_at")
        
        # Link logged-in user if authenticated
        user = request.user if request.user.is_authenticated else None
        
        short_url_obj = URLShortenerService.shorten_url(
            original_url=original_url,
            user=user,
            expires_at=expires_at
        )
        
        response_serializer = self.get_serializer(short_url_obj)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """
        Soft deletes the short URL and evicts it from the Redis cache.
        """
        instance.is_active = False
        instance.save()
        delete_short_url_cache(instance.short_code)


class RedirectView(View):
    """
    Performance-critical view that redirects short codes to their original URL (302 Found).
    Uses caching and dispatches click analytics tracking to Celery.
    """
    def get(self, request, short_code):
        # Clean up short code (strip trailing slash if matched)
        short_code = short_code.rstrip("/")
        
        # Parse telemetry data from request headers
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR", "")
            
        request_meta = {
            "ip_address": ip_address,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "referrer": request.META.get("HTTP_REFERER", ""),
        }
        
        # Resolve short code using RedirectService
        original_url = RedirectService.resolve_short_code(short_code, request_meta)
        if not original_url:
            raise Http404("Shortened URL not found or has expired.")
            
        # Return 302 Found redirect
        return HttpResponseRedirect(original_url)
