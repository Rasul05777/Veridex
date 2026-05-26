import os
import litellm
from .config import settings

litellm.drop_params = True


def chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """Call LLM and return the assistant message as a plain dict."""
    os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)

    kwargs: dict = {
        "model": settings.llm_model,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = litellm.completion(**kwargs)
    msg = response.choices[0].message

    result: dict = {"role": msg.role, "content": msg.content or ""}
    if msg.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return result
