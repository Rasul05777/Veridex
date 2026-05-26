from src.agent.verifier import verify


def test_verify_returns_true_when_findings_sufficient(mocker):
    mocker.patch(
        "src.agent.verifier.chat",
        return_value={"role": "assistant", "content": '{"verified": true, "gaps": ""}'},
    )
    result = verify(
        findings=[{"severity": "high", "title": "SQLi", "description": "...", "tool": "sqlmap"}],
        goal="find vulnerabilities",
    )
    assert result["verified"] is True
    assert result["gaps"] == ""


def test_verify_returns_false_with_gaps(mocker):
    mocker.patch(
        "src.agent.verifier.chat",
        return_value={"role": "assistant", "content": '{"verified": false, "gaps": "No port scan done"}'},
    )
    result = verify(findings=[], goal="find vulnerabilities")
    assert result["verified"] is False
    assert "port scan" in result["gaps"]


def test_verify_handles_malformed_json(mocker):
    mocker.patch(
        "src.agent.verifier.chat",
        return_value={"role": "assistant", "content": "not json"},
    )
    result = verify(findings=[], goal="x")
    assert result["verified"] is True  # safe default: don't loop forever
