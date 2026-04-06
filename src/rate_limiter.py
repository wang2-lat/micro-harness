"""
Global rate limiter — prevents 429 errors across all harness backends.

Problem: each harness instance has its own sleep(1), but when running
multiple agents or benchmark trials back-to-back, the global request
rate exceeds the API limit.

Solution: a singleton rate limiter that ALL API calls go through.
"""
import time
import threading


class RateLimiter:
    """Token bucket rate limiter. Thread-safe."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, max_rpm: int = 30, min_interval: float = 2.0):
        if self._initialized:
            return
        self._initialized = True
        self.max_rpm = max_rpm
        self.min_interval = min_interval
        self.last_call = 0.0
        self._call_lock = threading.Lock()
        self.total_calls = 0
        self.total_waits = 0

    def wait(self):
        """Call before every API request. Blocks if too fast."""
        with self._call_lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                self.total_waits += 1
                time.sleep(wait_time)
            self.last_call = time.time()
            self.total_calls += 1

    def stats(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "total_waits": self.total_waits,
            "wait_ratio": f"{self.total_waits}/{self.total_calls}" if self.total_calls else "0/0",
        }


# Global singleton
_limiter = RateLimiter()


def rate_limit():
    """Call this before every API request."""
    _limiter.wait()


def rate_stats() -> dict:
    return _limiter.stats()
