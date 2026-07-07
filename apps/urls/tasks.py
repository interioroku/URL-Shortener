import logging
from celery import shared_task
from django.utils import timezone
from apps.urls.models import ShortURL, ClickEvent

logger = logging.getLogger(__name__)

def resolve_geoip_country(ip_address: str) -> str:
    """
    Mock GeoIP country resolver.
    In production, this would use django.contrib.gis.geoip2 or a MaxMind database.
    """
    if not ip_address:
        return "Unknown"
    
    # Return mock countries based on IP segments for testing/development
    if ip_address.startswith("127.") or ip_address == "::1":
        return "Localhost"
    elif ip_address.startswith("10.") or ip_address.startswith("192.168."):
        return "Private Network"
    
    # Deterministic mock lookup based on IP string to simulate geoip functionality
    countries = ["United States", "United Kingdom", "Canada", "Germany", "Japan", "India", "Australia", "France"]
    try:
        # Sum digits of IP to select a country deterministically
        val = sum(int(c) for c in ip_address if c.isdigit())
        return countries[val % len(countries)]
    except Exception:
        return "Unknown"

@shared_task
def log_click_event(short_code: str, ip_address: str, user_agent: str, referrer: str):
    """
    Asynchronously logs a ClickEvent to the database.
    This runs out-of-band to prevent slowing down the redirect response.
    """
    try:
        short_url = ShortURL.objects.get(short_code=short_code)
        
        # Resolve country from IP address
        country = resolve_geoip_country(ip_address)
        
        # Create the ClickEvent record
        ClickEvent.objects.create(
            short_url=short_url,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            timestamp=timezone.now()
        )
        logger.info(f"Asynchronously logged click event for short code: {short_code}")
    except ShortURL.DoesNotExist:
        logger.error(f"Failed to log click event: ShortURL with code '{short_code}' does not exist.")
    except Exception as e:
        logger.exception(f"Error logging click event: {e}")
