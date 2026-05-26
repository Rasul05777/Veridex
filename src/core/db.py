import time
import aiosqlite

_CREATE_TASKS = """
CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    goal       TEXT NOT NULL,
    target     TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'queued',
    created_at INTEGER NOT NULL
)
"""

_CREATE_CONTEXT = """
CREATE TABLE IF NOT EXISTS context (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id   INTEGER NOT NULL REFERENCES tasks(id),
    type      TEXT NOT NULL,
    message   TEXT NOT NULL,
    agent     TEXT NOT NULL,
    timestamp INTEGER NOT NULL
)
"""


async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(_CREATE_TASKS)
        await db.execute(_CREATE_CONTEXT)
        await db.commit()


async def create_task(db_path: str, goal: str, target: str) -> int:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO tasks (goal, target, status, created_at) VALUES (?, ?, 'queued', ?)",
            (goal, target, int(time.time())),
        )
        await db.commit()
        return cursor.lastrowid


async def update_task_status(db_path: str, task_id: int, status: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        await db.commit()


async def save_context(
    db_path: str, task_id: int, type_: str, message: str, agent: str
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO context (task_id, type, message, agent, timestamp) VALUES (?, ?, ?, ?, ?)",
            (task_id, type_, message, agent, int(time.time())),
        )
        await db.commit()


async def get_task(db_path: str, task_id: int) -> dict | None:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_context(db_path: str, task_id: int) -> list[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM context WHERE task_id = ? ORDER BY timestamp ASC",
            (task_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
