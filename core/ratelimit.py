import time
import logging
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

def rate_limit(limit: int = 10, period: int = 60):
    """
    Simple cache-based fixed-window rate limiting decorator for API views.
    limit: Max requests allowed in the period.
    period: Time window in seconds.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Resolve client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR', 'unknown')
            
            # Construct a cache key based on IP and the view name
            key = f"ratelimit:{view_func.__name__}:{ip}"
            
            try:
                requests_data = cache.get(key, [])
            except Exception as e:
                # If cache is down, fail-open to ensure service availability
                logger.warning(f"Cache access failed during rate limiting, failing open: {e}")
                return view_func(request, *args, **kwargs)
                
            current_time = time.time()
            
            # Filter requests within the window period
            requests_data = [t for t in requests_data if current_time - t < period]
            
            if len(requests_data) >= limit:
                return Response(
                    {"error": "Too many requests. Rate limit exceeded. Please try again later."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            requests_data.append(current_time)
            try:
                cache.set(key, requests_data, timeout=period)
            except Exception as e:
                logger.warning(f"Failed to save rate limit data to cache: {e}")
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
