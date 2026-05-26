# tests/test_config.py
from src.core.config import Settings


def test_defaults():
    s = Settings(
        _env_file=None,
        anthropic_api_key="sk-test",
    )
    assert s.llm_model == "claude-sonnet-4-6"
    assert s.max_iterations == 10
    assert s.db_path == "data/verilab.db"


def test_allowed_targets_parsed():
    s = Settings(
        _env_file=None,
        anthropic_api_key="sk-test",
        allowed_targets="http://a.com,http://b.com",
    )
    assert "http://a.com" in s.allowed_targets_list
    assert "http://b.com" in s.allowed_targets_list
