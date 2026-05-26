# tests/test_db.py
import time
import pytest
import aiosqlite
from src.core.db import init_db, create_task, update_task_status, save_context, get_task, get_context


@pytest.fixture
async def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    await init_db(path)
    return path


async def test_create_and_get_task(db_path):
    task_id = await create_task(db_path, goal="scan for sqli", target="http://a.com")
    task = await get_task(db_path, task_id)
    assert task["goal"] == "scan for sqli"
    assert task["target"] == "http://a.com"
    assert task["status"] == "queued"


async def test_update_status(db_path):
    task_id = await create_task(db_path, goal="x", target="http://b.com")
    await update_task_status(db_path, task_id, "running")
    task = await get_task(db_path, task_id)
    assert task["status"] == "running"


async def test_save_and_get_context(db_path):
    task_id = await create_task(db_path, goal="x", target="http://c.com")
    await save_context(db_path, task_id=task_id, type_="thought",
                       message="I should run nmap", agent="reasoner")
    rows = await get_context(db_path, task_id)
    assert len(rows) == 1
    assert rows[0]["message"] == "I should run nmap"
    assert rows[0]["agent"] == "reasoner"
