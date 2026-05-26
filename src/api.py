import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .core.config import settings
from .core.db import init_db, create_task, update_task_status, save_context, get_task, get_context
from .core.logging import configure_logging, get_logger
from .graph.build import build_graph
from .safety.scope_guard import ScopeViolation, check_target

configure_logging()
log = get_logger()

_queue: asyncio.Queue = asyncio.Queue()
_graph = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    global _graph
    await init_db(settings.db_path)
    _graph = build_graph()
    task = asyncio.create_task(_worker_loop())
    log.info("verilab started", db=settings.db_path, model=settings.llm_model)
    yield
    task.cancel()


app = FastAPI(title="Verilab", lifespan=lifespan)


async def _worker_loop() -> None:
    while True:
        task_id, goal, target = await _queue.get()
        try:
            await _run_agent(task_id, goal, target)
        except Exception as exc:
            log.error("agent error", task_id=task_id, error=str(exc))
            await update_task_status(settings.db_path, task_id, "error")
        finally:
            _queue.task_done()


async def _run_agent(task_id: int, goal: str, target: str) -> None:
    await update_task_status(settings.db_path, task_id, "running")
    state = {
        "task_id": task_id,
        "goal": goal,
        "target": target,
        "plan": [],
        "messages": [],
        "findings": [],
        "verified": False,
        "iterations": 0,
        "max_iterations": settings.max_iterations,
    }

    async for event in _graph.astream(state):
        for node_name, output in event.items():
            msgs: list[dict] = output.get("messages", [])
            for msg in msgs:
                role = msg.get("role", "unknown")
                content = msg.get("content") or json.dumps(msg.get("tool_calls", []))
                type_ = _role_to_type(role, msg)
                await save_context(
                    settings.db_path,
                    task_id=task_id,
                    type_=type_,
                    message=str(content)[:4096],
                    agent=node_name,
                )

    await update_task_status(settings.db_path, task_id, "done")
    log.info("task done", task_id=task_id)


def _role_to_type(role: str, msg: dict) -> str:
    if role == "tool":
        return "observation"
    if msg.get("tool_calls"):
        return "action"
    return "thought"


class TaskRequest(BaseModel):
    goal: str
    target: str


@app.post("/task")
async def post_task(req: TaskRequest):
    try:
        check_target(req.target, settings.allowed_targets_list)
    except ScopeViolation as e:
        raise HTTPException(status_code=400, detail=str(e))

    task_id = await create_task(settings.db_path, goal=req.goal, target=req.target)
    _queue.put_nowait((task_id, req.goal, req.target))
    log.info("task queued", task_id=task_id, target=req.target)
    return {"task_id": task_id}


@app.get("/task/{task_id}")
async def get_task_status(task_id: int):
    task = await get_task(settings.db_path, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    ctx = await get_context(settings.db_path, task_id)
    findings = [c for c in ctx if c["type"] == "finding"]
    return {
        "task_id": task_id,
        "goal": task["goal"],
        "target": task["target"],
        "status": task["status"],
        "findings": findings,
    }


@app.get("/task/{task_id}/context")
async def get_task_context(task_id: int):
    task = await get_task(settings.db_path, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return await get_context(settings.db_path, task_id)
