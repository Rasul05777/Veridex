# tests/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("VERILAB_DB_PATH", db_path)
    monkeypatch.setenv("VERILAB_ALLOWED_TARGETS", "http://testphp.vulnweb.com")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    import importlib
    import src.core.config as cfg_mod
    importlib.reload(cfg_mod)
    import src.api as api_mod
    importlib.reload(api_mod)

    # Manually initialize DB and graph since ASGITransport does not trigger lifespan
    from src.core.db import init_db
    from src.core.config import settings as reloaded_settings
    from src.graph.build import build_graph
    await init_db(db_path)
    api_mod._graph = build_graph()

    from src.api import app as reloaded_app
    async with AsyncClient(transport=ASGITransport(app=reloaded_app), base_url="http://test") as ac:
        yield ac


async def test_post_task_returns_task_id(client, mocker):
    mocker.patch("src.api._queue.put_nowait")
    resp = await client.post("/task", json={"goal": "find vulns", "target": "http://testphp.vulnweb.com"})
    assert resp.status_code == 200
    assert "task_id" in resp.json()


async def test_post_task_rejects_out_of_scope(client):
    resp = await client.post("/task", json={"goal": "find vulns", "target": "http://evil.com"})
    assert resp.status_code == 400
    assert "scope" in resp.json()["detail"].lower()


async def test_get_task_not_found(client):
    resp = await client.get("/task/9999")
    assert resp.status_code == 404


async def test_get_task_returns_status(client, mocker):
    mocker.patch("src.api._queue.put_nowait")
    post = await client.post("/task", json={"goal": "x", "target": "http://testphp.vulnweb.com"})
    task_id = post.json()["task_id"]
    get = await client.get(f"/task/{task_id}")
    assert get.status_code == 200
    assert get.json()["status"] in ("queued", "running", "done", "error")


def test_context_entries_from_message_records_tool_calls():
    from src.api import _context_entries_from_message

    entries = _context_entries_from_message({
        "role": "assistant",
        "content": "I will inspect headers.",
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "execute_command",
                    "arguments": '{"command":"curl -I https://example.com","backend":"kali"}',
                },
            }
        ],
    })

    assert entries[0] == {"type": "thought", "message": "I will inspect headers."}
    assert entries[1]["type"] == "action"
    assert '"tool": "execute_command"' in entries[1]["message"]
    assert '"backend": "kali"' in entries[1]["message"]
