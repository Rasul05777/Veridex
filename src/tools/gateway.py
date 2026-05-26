import subprocess

BACKENDS: dict[str, dict] = {
    "kali": {
        "container": "verilab-kali",
        "shell": "bash",
        "desc": "General pentest toolkit (nikto, sqlmap, gobuster, ffuf, hydra, whois, curl)",
        "tools": ["nikto", "sqlmap", "gobuster", "ffuf", "hydra", "whois", "curl", "wget"],
    },
    "nuclei": {
        "container": "verilab-nuclei",
        "shell": "sh",
        "desc": "CVE template scanner",
        "tools": ["nuclei"],
    },
    "nmap": {
        "container": "verilab-nmap",
        "shell": "sh",
        "desc": "Network and port scanner",
        "tools": ["nmap"],
    },
    "semgrep": {
        "container": "verilab-semgrep",
        "shell": "sh",
        "desc": "SAST static code analysis",
        "tools": ["semgrep"],
    },
    "trufflehog": {
        "container": "verilab-trufflehog",
        "shell": "sh",
        "desc": "Secrets and token leak detection",
        "tools": ["trufflehog"],
    },
}


def execute(command: str, backend: str = "kali", timeout: int = 300) -> str:
    cfg = BACKENDS.get(backend)
    if not cfg:
        return f"Unknown backend '{backend}'. Available: {list(BACKENDS)}"
    result = subprocess.run(
        ["docker", "exec", cfg["container"], cfg["shell"], "-c", command],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout + result.stderr


def list_backends() -> dict[str, dict]:
    return {k: {"desc": v["desc"], "tools": v["tools"]} for k, v in BACKENDS.items()}
