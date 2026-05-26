# tests/test_scope_guard.py
import pytest
from src.safety.scope_guard import check_target, ScopeViolation


def test_allowed_target_passes():
    check_target("http://testphp.vulnweb.com", ["http://testphp.vulnweb.com"])


def test_disallowed_target_raises():
    with pytest.raises(ScopeViolation, match="not in allowed scope"):
        check_target("http://evil.com", ["http://testphp.vulnweb.com"])


def test_empty_allowlist_blocks_all():
    with pytest.raises(ScopeViolation):
        check_target("http://anything.com", [])
