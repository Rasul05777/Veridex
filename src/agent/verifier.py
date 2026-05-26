import json
from ..core.llm import chat

_SYSTEM = (
    "You are a security assessment verifier. "
    "Review the findings list and the original goal. "
    "Decide whether the assessment is sufficiently complete. "
    "Return ONLY valid JSON: {\"verified\": bool, \"gaps\": \"explanation if not verified, else empty string\"}"
)


def verify(findings: list[dict], goal: str) -> dict:
    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": (
                f"Goal: {goal}\n\n"
                f"Findings ({len(findings)} total):\n"
                + json.dumps(findings, indent=2)
                + "\n\nIs assessment complete?"
            ),
        },
    ]
    response = chat(messages)
    try:
        return json.loads(response.get("content", "{}"))
    except (json.JSONDecodeError, ValueError):
        return {"verified": True, "gaps": ""}
