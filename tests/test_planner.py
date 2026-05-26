from src.agent.planner import plan


def test_plan_returns_list_of_strings(mocker):
    mocker.patch(
        "src.agent.planner.chat",
        return_value={"role": "assistant", "content": '["run nmap", "run nuclei", "report findings"]'},
    )
    result = plan(goal="find vulns", target="http://a.com")
    assert result == ["run nmap", "run nuclei", "report findings"]


def test_plan_handles_malformed_json(mocker):
    mocker.patch(
        "src.agent.planner.chat",
        return_value={"role": "assistant", "content": "not json"},
    )
    result = plan(goal="find vulns", target="http://a.com")
    assert result == []
