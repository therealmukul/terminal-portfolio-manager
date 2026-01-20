"""Rate limiting utility using token bucket algorithm."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Deque


class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Implements a sliding window rate limiter that tracks request timestamps
    and ensures requests stay within the configured limit per minute.
    """

    def __init__(self, requests_per_minute: int):
        """
        Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum number of requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.window_size = 60.0  # 1 minute window
        self.timestamps: Deque[float] = deque()

    async def acquire(self) -> None:
        """
        Acquire permission to make a request.

        Blocks if the rate limit would be exceeded, waiting until
        a request slot becomes available.
        """
        now = time.time()

        # Remove timestamps older than the window
        while self.timestamps and now - self.timestamps[0] > self.window_size:
            self.timestamps.popleft()

        # If at capacity, wait until oldest request exits the window
        if len(self.timestamps) >= self.requests_per_minute:
            oldest = self.timestamps[0]
            sleep_time = self.window_size - (now - oldest) + 0.1  # Small buffer
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                # Clean up again after sleeping
                now = time.time()
                while self.timestamps and now - self.timestamps[0] > self.window_size:
                    self.timestamps.popleft()

        # Record this request
        self.timestamps.append(time.time())

    def acquire_sync(self) -> None:
        """
        Synchronous version of acquire for non-async contexts.

        Blocks if the rate limit would be exceeded.
        """
        now = time.time()

        # Remove timestamps older than the window
        while self.timestamps and now - self.timestamps[0] > self.window_size:
            self.timestamps.popleft()

        # If at capacity, wait until oldest request exits the window
        if len(self.timestamps) >= self.requests_per_minute:
            oldest = self.timestamps[0]
            sleep_time = self.window_size - (now - oldest) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)
                now = time.time()
                while self.timestamps and now - self.timestamps[0] > self.window_size:
                    self.timestamps.popleft()

        self.timestamps.append(time.time())

    @property
    def remaining(self) -> int:
        """Get the number of remaining requests in the current window."""
        now = time.time()
        # Count only recent timestamps
        recent_count = sum(
            1 for ts in self.timestamps if now - ts <= self.window_size
        )
        return max(0, self.requests_per_minute - recent_count)
