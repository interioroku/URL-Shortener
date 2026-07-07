import logging
from django.core.cache import cache
from redis.exceptions import ConnectionError, RedisError

logger = logging.getLogger(__name__)

CACHE_PREFIX = "short_url:"
CACHE_TTL = 86400  # 24 hours in seconds

def get_short_url_cache(short_code: str) -> str:
    """
    Attempts to fetch original_url from the cache.
    Logs warning and returns None on Redis connection failure.
    """
    key = f"{CACHE_PREFIX}{short_code}"
    try:
        return cache.get(key)
    except (ConnectionError, RedisError) as e:
        logger.warning(f"Redis cache connection error on GET: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching from cache: {e}")
        return None

def set_short_url_cache(short_code: str, original_url: str) -> bool:
    """
    Attempts to set original_url mapping in cache with 24h TTL.
    Logs warning and returns False on Redis connection failure.
    """
    key = f"{CACHE_PREFIX}{short_code}"
    try:
        cache.set(key, original_url, timeout=CACHE_TTL)
        return True
    except (ConnectionError, RedisError) as e:
        logger.warning(f"Redis cache connection error on SET: {e}")
        return False
    except Exception as e:
        logger.error(f"Error setting in cache: {e}")
        return False

def delete_short_url_cache(short_code: str) -> bool:
    """
    Attempts to evict short code mapping from cache.
    """
    key = f"{CACHE_PREFIX}{short_code}"
    try:
        cache.delete(key)
        return True
    except (ConnectionError, RedisError) as e:
        logger.warning(f"Redis cache connection error on DELETE: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting from cache: {e}")
        return False
