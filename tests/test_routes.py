from src.graph.routes import after_reason, after_verify
from src.graph.state import AgentState


def _state(**overrides) -> AgentState:
    s: AgentState = {
        "task_id": 1, "goal": "x", "target": "http://a.com",
        "plan": [], "messages": [], "findings": [],
        "verified": False, "iterations": 1, "max_iterations": 10,
    }
    s.update(overrides)
    return s


def test_after_reason_routes_to_tool_call_when_tool_calls_present():
    state = _state(messages=[{
        "role": "assistant",
        "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "execute_command", "arguments": "{}"}}],
    }])
    assert after_reason(state) == "tool_call"


def test_after_reason_routes_to_verify_when_no_tool_calls():
    state = _state(messages=[{"role": "assistant", "content": "Done."}])
    assert after_reason(state) == "verify"


def test_after_reason_routes_to_verify_at_max_iterations():
    state = _state(
        iterations=10,
        max_iterations=10,
        messages=[{
            "role": "assistant",
            "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "execute_command", "arguments": "{}"}}],
        }],
    )
    assert after_reason(state) == "verify"


def test_after_verify_ends_when_verified():
    assert after_verify(_state(verified=True)) == "__end__"


def test_after_verify_ends_at_max_iterations():
    assert after_verify(_state(verified=False, iterations=10, max_iterations=10)) == "__end__"


def test_after_verify_retries_when_not_verified():
    assert after_verify(_state(verified=False, iterations=3)) == "reason"
