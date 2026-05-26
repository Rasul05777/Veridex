# tests/test_gateway.py
import pytest
from unittest.mock import MagicMock
from src.tools.gateway import execute, list_backends, BACKENDS


def test_list_backends_returns_all():
    result = list_backends()
    assert set(result.keys()) == {"kali", "nuclei", "nmap", "semgrep", "trufflehog"}
    assert "desc" in result["kali"]
    assert "tools" in result["kali"]


def test_execute_unknown_backend():
    result = execute("echo hi", backend="nonexistent")
    assert "Unknown backend" in result
    assert "nonexistent" in result


def test_execute_calls_docker(mocker):
    mock_run = mocker.patch("src.tools.gateway.subprocess.run")
    mock_run.return_value = MagicMock(stdout="scan complete\n", stderr="")
    result = execute("nmap -sV 127.0.0.1", backend="nmap", timeout=30)
    assert result == "scan complete\n"
    mock_run.assert_called_once_with(
        ["docker", "exec", "verilab-nmap", "sh", "-c", "nmap -sV 127.0.0.1"],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_execute_combines_stdout_stderr(mocker):
    mock_run = mocker.patch("src.tools.gateway.subprocess.run")
    mock_run.return_value = MagicMock(stdout="out", stderr="err")
    result = execute("ls", backend="kali")
    assert result == "outerr"
