from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
import datetime

from apps.urls.models import ShortURL, ClickEvent
from apps.urls.services import URLShortenerService, RedirectService

class URLShortenerServiceTest(TestCase):
    def test_encode_base62(self):
        self.assertEqual(URLShortenerService.encode_base62(0), "0")
        self.assertEqual(URLShortenerService.encode_base62(10), "A")
        self.assertEqual(URLShortenerService.encode_base62(61), "z")
        self.assertEqual(URLShortenerService.encode_base62(62), "10")

    def test_generate_short_code(self):
        url = "https://google.com"
        code = URLShortenerService.generate_short_code(url)
        self.assertEqual(len(code), 7)

    def test_shorten_url_deduplication(self):
        url = "https://google.com"
        obj1 = URLShortenerService.shorten_url(url)
        obj2 = URLShortenerService.shorten_url(url)
        self.assertEqual(obj1.id, obj2.id)
        self.assertEqual(obj1.short_code, obj2.short_code)

    @patch("apps.urls.services.URLShortenerService.generate_short_code")
    def test_shorten_url_collision_handling(self, mock_generate):
        salt = getattr(settings, "URL_SHORTENER_SALT", "")
        # Force a collision for the first code: return 'aaaaaaa', then 'aaaaaaa', then 'bbbbbbb'
        mock_generate.side_effect = ["aaaaaaa", "aaaaaaa", "bbbbbbb"]
        
        # Shorten first URL
        obj1 = URLShortenerService.shorten_url("https://url1.com")
        self.assertEqual(obj1.short_code, "aaaaaaa")
        
        # Shorten second URL (which would collide with 'aaaaaaa' on the first try)
        obj2 = URLShortenerService.shorten_url("https://url2.com")
        self.assertEqual(obj2.short_code, "bbbbbbb")
        
        # Verify it was called with incrementing counter and active settings salt
        mock_generate.assert_any_call("https://url2.com", salt, 0)
        mock_generate.assert_any_call("https://url2.com", salt, 1)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class RedirectServiceTest(TestCase):
    @patch("apps.urls.services.log_click_event.delay")
    def test_resolve_short_code_success(self, mock_log_task):
        ShortURL.objects.create(
            original_url="https://github.com",
            short_code="githubb"
        )
        
        meta = {"ip_address": "192.168.1.1", "user_agent": "Mozilla", "referrer": ""}
        resolved_url = RedirectService.resolve_short_code("githubb", meta)
        
        self.assertEqual(resolved_url, "https://github.com")
        mock_log_task.assert_called_once_with(
            short_code="githubb",
            ip_address="192.168.1.1",
            user_agent="Mozilla",
            referrer=""
        )

    def test_resolve_short_code_expired(self):
        ShortURL.objects.create(
            original_url="https://expired.com",
            short_code="expired",
            expires_at=timezone.now() - datetime.timedelta(seconds=10)
        )
        meta = {}
        resolved_url = RedirectService.resolve_short_code("expired", meta)
        self.assertIsNone(resolved_url)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class APIEndpointsTest(APITestCase):
    def test_create_short_url_anonymous(self):
        url = reverse("shorturl-list")
        data = {"original_url": "https://python.org"}
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("short_code", response.data)
        self.assertEqual(response.data["original_url"], "https://python.org")
        
        # Check database
        self.assertTrue(ShortURL.objects.filter(short_code=response.data["short_code"]).exists())

    def test_redirect_view_302(self):
        # Create a short URL
        ShortURL.objects.create(
            original_url="https://google.com",
            short_code="googlyy"
        )
        
        # Hit redirect endpoint
        url = reverse("redirect_url_short", kwargs={"short_code": "googlyy"})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://google.com")

    def test_rate_limiting(self):
        from django.core.cache import cache
        cache.clear()
        # Hit the create endpoint multiple times to trigger rate limits
        url = reverse("shorturl-list")
        data = {"original_url": "https://python.org"}
        
        # Limit is 10 per minute. Hit it 10 times.
        for i in range(10):
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
        # The 11th request should be rate limited (429)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
