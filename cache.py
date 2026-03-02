"""Cache module for tracking recent listings and rate limiting."""

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Deque

from config import LISTING_CACHE_SIZE, RATE_LIMIT_INTERVAL

logger = logging.getLogger(__name__)


class ListingCache:
    """Cache for tracking recently seen listings to prevent duplicates."""
    
    def __init__(self, maxsize: int = LISTING_CACHE_SIZE):
        """Initialize the listing cache.
        
        Args:
            maxsize: Maximum number of listings to cache per city
        """
        self._caches: dict[str, Deque[str]] = {}
        self._maxsize = maxsize
    
    def has_seen(self, city: str, listing_url: str) -> bool:
        """Check if a listing has been seen recently.
        
        Args:
            city: City identifier (e.g., 'erlangen')
            listing_url: The listing URL to check
            
        Returns:
            True if listing was recently seen, False otherwise
        """
        if city not in self._caches:
            self._caches[city] = deque(maxlen=self._maxsize)
        
        return listing_url in self._caches[city]
    
    def add(self, city: str, listing_url: str) -> None:
        """Add a listing to the cache.
        
        Args:
            city: City identifier
            listing_url: The listing URL to cache
        """
        if city not in self._caches:
            self._caches[city] = deque(maxlen=self._maxsize)
        
        if listing_url not in self._caches[city]:
            self._caches[city].append(listing_url)
            logger.debug(f"Added to cache [{city}]: {listing_url}")
    
    def clear(self, city: str) -> None:
        """Clear the cache for a specific city.
        
        Args:
            city: City identifier to clear
        """
        if city in self._caches:
            self._caches[city].clear()
            logger.info(f"Cleared cache for {city}")
    
    def get_size(self, city: str) -> int:
        """Get the current cache size for a city.
        
        Args:
            city: City identifier
            
        Returns:
            Number of cached listings for the city
        """
        return len(self._caches.get(city, []))


class RateLimiter:
    """Rate limiter to prevent excessive requests."""
    
    def __init__(self, min_interval: float = RATE_LIMIT_INTERVAL):
        """Initialize the rate limiter.
        
        Args:
            min_interval: Minimum seconds between requests
        """
        self._last_request_time: dict[str, datetime] = {}
        self._min_interval = min_interval
    
    async def wait_if_needed(self, key: str = "default") -> None:
        """Wait if necessary to respect rate limits.
        
        Args:
            key: Identifier for separate rate limit tracking (e.g., URL or city)
        """
        if key in self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time[key]).total_seconds()
            if elapsed < self._min_interval:
                wait_time = self._min_interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {key}")
                await asyncio.sleep(wait_time)
        
        self._last_request_time[key] = datetime.now()


# Global instances
listing_cache = ListingCache()
rate_limiter = RateLimiter()
