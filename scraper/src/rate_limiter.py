"""Rate limiter for polite scraping."""
import asyncio
import time
from typing import Dict

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 30, delay_ms: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.delay_ms = delay_ms
        self.last_request_time: Dict[str, float] = {}
    
    async def wait(self, domain: str):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        last_time = self.last_request_time.get(domain, 0)
        time_since_last = current_time - last_time
        min_interval = self.delay_ms / 1000.0
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()
