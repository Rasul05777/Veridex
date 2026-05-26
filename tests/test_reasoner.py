from src.agent.reasoner import reason
from src.graph.state import AgentState


def _base_state(**overrides) -> AgentState:
    state: AgentState = {
        "task_id": 1,
        "goal": "find vulns",
        "target": "http://a.com",
        "plan": ["run nmap", "run nuclei"],
        "messages": [{"role": "user", "content": "Begin assessment."}],
        "findings": [],
        "verified": False,
        "iterations": 0,
        "max_iterations": 10,
    }
    state.update(overrides)
    return state


def test_reason_returns_state_delta_with_message(mocker):
    mocker.patch(
        "src.agent.reasoner.chat",
        return_value={
            "role": "assistant",
            "content": "I will run nmap first.",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "execute_command", "arguments": '{"command":"nmap -sV http://a.com","backend":"nmap"}'},
                }
            ],
        },
    )
    delta = reason(_base_state())
    assert "messages" in delta
    assert delta["messages"][0]["role"] == "assistant"
    assert delta["iterations"] == 1


def test_reason_increments_iterations(mocker):
    mocker.patch(
        "src.agent.reasoner.chat",
        return_value={"role": "assistant", "content": "Done.", "tool_calls": None},
    )
    delta = reason(_base_state(iterations=3))
    assert delta["iterations"] == 4
