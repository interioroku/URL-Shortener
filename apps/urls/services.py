import hashlib
from django.conf import settings
from django.utils import timezone
from apps.urls.models import ShortURL
from apps.urls.tasks import log_click_event
from core.cache import get_short_url_cache, set_short_url_cache

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

class URLShortenerService:
    @staticmethod
    def encode_base62(num: int) -> str:
        """Encodes an integer into a Base62 string."""
        if num == 0:
            return BASE62_ALPHABET[0]
        arr = []
        base = len(BASE62_ALPHABET)
        while num:
            num, rem = divmod(num, base)
            arr.append(BASE62_ALPHABET[rem])
        arr.reverse()
        return "".join(arr)

    @classmethod
    def generate_short_code(cls, original_url: str, salt: str = "", counter: int = 0) -> str:
        """
        Generates a 7-character Base62 short code from MD5(original_url + salt + str(counter)).
        """
        # Append salt and optional collision counter
        payload = f"{original_url}{salt}{counter}"
        # Compute MD5
        md5_hash = hashlib.md5(payload.encode("utf-8")).hexdigest()
        # Convert first 8 bytes (16 hex chars) of MD5 to an integer (64-bit integer)
        val = int(md5_hash[:16], 16)
        # Convert integer to Base62
        base62_str = cls.encode_base62(val)
        # Take the first 7 characters, padded with zeros if shorter
        return base62_str[:7].zfill(7)

    @classmethod
    def shorten_url(cls, original_url: str, user=None, expires_at=None) -> ShortURL:
        """
        Deduplicates original URLs and creates a unique short code.
        If a collision occurs (different URL maps to same short code),
        increments the counter and tries again.
        """
        salt = getattr(settings, "URL_SHORTENER_SALT", "")
        counter = 0

        while True:
            short_code = cls.generate_short_code(original_url, salt, counter)
            
            # Check database for existing short code
            existing = ShortURL.objects.filter(short_code=short_code).first()
            if not existing:
                # No collision: create and return new ShortURL
                return ShortURL.objects.create(
                    original_url=original_url,
                    short_code=short_code,
                    user=user,
                    expires_at=expires_at
                )
            elif existing.original_url == original_url:
                # Same URL: return existing (deduplication)
                # If existing is expired or inactive, we could reactivate it.
                if not existing.is_active:
                    existing.is_active = True
                    existing.expires_at = expires_at
                    existing.save()
                return existing
            else:
                # Collision: different URL has this short code. Try again with incremented counter.
                counter += 1


class RedirectService:
    @staticmethod
    def resolve_short_code(short_code: str, request_meta: dict) -> str:
        """
        Resolves short code. Checks cache first, falls back to DB, and
        dispatches an async task to log the click event.
        """
        # Try cache lookup
        original_url = get_short_url_cache(short_code)

        if not original_url:
            # Cache miss, check DB
            try:
                short_url_obj = ShortURL.objects.get(short_code=short_code, is_active=True)
                if short_url_obj.is_expired:
                    return None
                original_url = short_url_obj.original_url
                # Set in cache
                set_short_url_cache(short_code, original_url)
            except ShortURL.DoesNotExist:
                return None

        # Dispatch async click log task
        log_click_event.delay(
            short_code=short_code,
            ip_address=request_meta.get("ip_address"),
            user_agent=request_meta.get("user_agent"),
            referrer=request_meta.get("referrer")
        )

        return original_url
