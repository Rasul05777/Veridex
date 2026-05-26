import time
from collections import deque


class ToolNotAllowed(Exception):
    pass


class AllowedToolsGate:
    def __init__(self, allowed: set[str]) -> None:
        self._allowed = allowed

    def check(self, tool_name: str) -> None:
        if tool_name not in self._allowed:
            raise ToolNotAllowed(f"Tool '{tool_name}' is not in allowlist")


class RateLimiter:
    def __init__(self, calls_per_minute: int = 30) -> None:
        self._limit = calls_per_minute
        self._window = 60.0
        self._calls: deque[float] = deque()

    def check(self) -> None:
        now = time.monotonic()
        cutoff = now - self._window
        while self._calls and self._calls[0] < cutoff:
            self._calls.popleft()
        if len(self._calls) >= self._limit:
            raise RuntimeError(f"Tool gateway rate limit exceeded ({self._limit}/min)")
        self._calls.append(now)
