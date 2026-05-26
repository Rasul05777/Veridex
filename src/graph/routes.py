from .state import AgentState


def after_reason(state: AgentState) -> str:
    if state["iterations"] >= state["max_iterations"]:
        return "verify"
    last = state["messages"][-1] if state["messages"] else {}
    if last.get("tool_calls"):
        return "tool_call"
    return "verify"


def after_verify(state: AgentState) -> str:
    if state["verified"] or state["iterations"] >= state["max_iterations"]:
        return "__end__"
    return "reason"
