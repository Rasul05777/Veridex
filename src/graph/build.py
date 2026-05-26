import json
from langgraph.graph import StateGraph, END

from .state import AgentState
from .routes import after_reason, after_verify
from ..agent import planner, reasoner, verifier
from ..tools import gateway
from ..safety.gates import AllowedToolsGate

_gate = AllowedToolsGate(allowed={"execute_command", "list_backends", "report_finding"})


def _plan_node(state: AgentState) -> dict:
    subtasks = planner.plan(state["goal"], state["target"])
    initial_msg = {
        "role": "user",
        "content": f"Target: {state['target']}\nGoal: {state['goal']}\nBegin the security assessment.",
    }
    return {"plan": subtasks, "messages": [initial_msg]}


def _reason_node(state: AgentState) -> dict:
    return reasoner.reason(state)


def _tool_call_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1]
    tool_calls = last_msg.get("tool_calls", []) or []
    tool_results: list[dict] = []
    new_findings: list[dict] = []

    for tc in tool_calls:
        fn = tc["function"]
        name = fn["name"]
        try:
            args = json.loads(fn["arguments"])
        except json.JSONDecodeError:
            args = {}

        try:
            _gate.check(name)
        except Exception as e:
            output = str(e)
        else:
            if name == "execute_command":
                output = gateway.execute(
                    args.get("command", ""),
                    backend=args.get("backend", "kali"),
                    timeout=args.get("timeout", 300),
                )
            elif name == "list_backends":
                output = json.dumps(gateway.list_backends())
            elif name == "report_finding":
                new_findings.append(args)
                output = "Finding recorded."
            else:
                output = f"Unknown tool: {name}"

        tool_results.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": output,
        })

    return {"messages": tool_results, "findings": new_findings}


def _verify_node(state: AgentState) -> dict:
    result = verifier.verify(state["findings"], state["goal"])
    return {"verified": result.get("verified", True)}


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("plan", _plan_node)
    g.add_node("reason", _reason_node)
    g.add_node("tool_call", _tool_call_node)
    g.add_node("verify", _verify_node)

    g.set_entry_point("plan")
    g.add_edge("plan", "reason")
    g.add_conditional_edges("reason", after_reason, {"tool_call": "tool_call", "verify": "verify"})
    g.add_edge("tool_call", "reason")
    g.add_conditional_edges("verify", after_verify, {"reason": "reason", "__end__": END})

    return g.compile()
