import operator
from typing import TypedDict, Annotated


class AgentState(TypedDict):
    task_id: int
    goal: str
    target: str
    plan: list[str]
    messages: Annotated[list[dict], operator.add]
    findings: Annotated[list[dict], operator.add]
    verified: bool
    iterations: int
    max_iterations: int
