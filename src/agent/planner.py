import json
import re
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
    content = response.get("content", "[]")
    # Strip markdown fences if present
    content = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.MULTILINE)
    content = re.sub(r"```\s*$", "", content.strip(), flags=re.MULTILINE)
    try:
        result = json.loads(content.strip())
        if isinstance(result, list):
            return result
        return []
    except (json.JSONDecodeError, ValueError):
        return []
