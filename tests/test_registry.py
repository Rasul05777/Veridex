# tests/test_registry.py
from src.tools.registry import TOOL_REGISTRY, to_openai_tools, Tool


def test_registry_has_required_tools():
    assert "execute_command" in TOOL_REGISTRY
    assert "list_backends" in TOOL_REGISTRY
    assert "report_finding" in TOOL_REGISTRY


def test_tool_is_dataclass():
    t = TOOL_REGISTRY["execute_command"]
    assert isinstance(t, Tool)
    assert t.name == "execute_command"
    assert t.description
    assert isinstance(t.parameters, dict)


def test_to_openai_tools_format():
    tools = to_openai_tools()
    assert len(tools) == 3
    names = {t["function"]["name"] for t in tools}
    assert names == {"execute_command", "list_backends", "report_finding"}
    for t in tools:
        assert t["type"] == "function"
        assert "description" in t["function"]
        assert "parameters" in t["function"]


def test_execute_command_has_backend_enum():
    t = TOOL_REGISTRY["execute_command"]
    props = t.parameters["properties"]
    assert "enum" in props["backend"]
    assert "kali" in props["backend"]["enum"]
