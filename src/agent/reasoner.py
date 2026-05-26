from ..core.llm import chat
from ..tools.registry import to_openai_tools
from ..graph.state import AgentState

_SYSTEM = (
    "You are a security researcher conducting a vulnerability assessment. "
    "Use the available tools to investigate the target systematically. "
    "Always explain your reasoning before calling a tool. "
    "When you have discovered all significant vulnerabilities, call report_finding for each, "
    "then stop calling tools."
)


def reason(state: AgentState) -> dict:
    plan_str = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(state["plan"]))
    system = f"{_SYSTEM}\n\nAssessment plan:\n{plan_str}"

    messages = [{"role": "system", "content": system}] + state["messages"]
    response = chat(messages, tools=to_openai_tools())

    return {
        "messages": [response],
        "iterations": state["iterations"] + 1,
    }
