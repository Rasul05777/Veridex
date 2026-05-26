import json
from ..core.llm import chat

_SYSTEM = (
    "You are a security assessment planner. "
    "Given a goal and a target, produce a numbered list of specific, actionable scanning subtasks. "
    "Return ONLY a valid JSON array of strings, nothing else."
)


def plan(goal: str, target: str) -> list[str]:
    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": f"Goal: {goal}\nTarget: {target}\n\nReturn a JSON array of subtasks.",
        },
    ]
    response = chat(messages)
    try:
        return json.loads(response.get("content", "[]"))
    except (json.JSONDecodeError, ValueError):
        return []
