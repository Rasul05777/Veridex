from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict


TOOL_REGISTRY: dict[str, Tool] = {
    "execute_command": Tool(
        name="execute_command",
        description=(
            "Execute a shell command in a containerized security tool backend. "
            "Use this to run scans, enumerate targets, and discover vulnerabilities."
        ),
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "backend": {
                    "type": "string",
                    "enum": ["kali", "nuclei", "nmap", "semgrep", "trufflehog"],
                    "description": (
                        "Container to run in: kali=general pentest, nuclei=CVE scanner, "
                        "nmap=port scanner, semgrep=SAST, trufflehog=secrets"
                    ),
                },
                "timeout": {
                    "type": "integer",
                    "description": "Max seconds to wait for command (default 300)",
                    "default": 300,
                },
            },
            "required": ["command", "backend"],
        },
    ),
    "list_backends": Tool(
        name="list_backends",
        description="List all available security tool backends with their capabilities.",
        parameters={"type": "object", "properties": {}, "required": []},
    ),
    "report_finding": Tool(
        name="report_finding",
        description=(
            "Record a discovered vulnerability or security finding. "
            "Call this whenever you identify a concrete issue."
        ),
        parameters={
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low", "info"],
                },
                "title": {"type": "string", "description": "Short vulnerability title"},
                "description": {"type": "string", "description": "Detailed description and evidence"},
                "tool": {"type": "string", "description": "Tool that discovered this finding"},
            },
            "required": ["severity", "title", "description", "tool"],
        },
    ),
}


def to_openai_tools() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in TOOL_REGISTRY.values()
    ]
