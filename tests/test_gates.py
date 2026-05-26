# tests/test_gates.py
import time
import pytest
from src.safety.gates import AllowedToolsGate, RateLimiter, ToolNotAllowed


def test_allowed_tool_passes():
    gate = AllowedToolsGate(allowed={"execute_command", "list_backends", "report_finding"})
    gate.check("execute_command")  # no exception


def test_forbidden_tool_raises():
    gate = AllowedToolsGate(allowed={"execute_command"})
    with pytest.raises(ToolNotAllowed, match="rm_rf"):
        gate.check("rm_rf")


def test_rate_limiter_allows_within_limit():
    limiter = RateLimiter(calls_per_minute=60)
    for _ in range(5):
        limiter.check()  # no exception


def test_rate_limiter_blocks_over_limit():
    limiter = RateLimiter(calls_per_minute=2)
    limiter.check()
    limiter.check()
    with pytest.raises(Exception, match="rate limit"):
        limiter.check()
