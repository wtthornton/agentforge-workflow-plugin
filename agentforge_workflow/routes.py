"""Workflow test plugin routes (TAP-759)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from agentforge_workflow import __version__
from agentforge_workflow.nodes import BrokenNodeB, FlakyNodeB, NodeA, NodeB, NodeC
from agentforge_workflow.workflow import run_workflow

router = APIRouter(prefix="/api/workflow-test", tags=["workflow-test"])

# TAP-759 AC names this route explicitly: POST /api/workflow-demo/run.
demo_router = APIRouter(prefix="/api/workflow-demo", tags=["workflow-demo"])


@router.get("/status")
async def status() -> dict[str, Any]:
    return {"status": "ok", "plugin": "workflow-test", "version": __version__}


class WorkflowRunRequest(BaseModel):
    """Body for ``POST /api/workflow-demo/run``.

    ``b_mode`` selects node-B's behaviour — ``ok`` (default), ``flaky`` (uses
    ``b_fail_count`` transient failures then succeeds), or ``broken``
    (always permanent-fail).
    """

    input: str
    b_mode: str = "ok"
    b_fail_count: int = 1
    max_retries: int = Field(default=2, ge=0, le=5)


_NAMESPACE = "project.workflow"


def _build_nodes(req: WorkflowRunRequest) -> list[Any]:
    if req.b_mode == "flaky":
        b = FlakyNodeB(fail_count=req.b_fail_count)
    elif req.b_mode == "broken":
        b = BrokenNodeB()
    else:
        b = NodeB()
    return [NodeA(), b, NodeC()]


@demo_router.post("/run")
async def run_demo_workflow(
    body: WorkflowRunRequest, request: Request
) -> dict[str, Any]:
    """Execute the A→B→C workflow. Returns ``{"output": ...}`` or ``{"error": ...}``."""
    topic_bus = getattr(request.app.state, "topic_bus", None)

    async def _emit(event_type: str, payload: dict[str, Any]) -> None:
        if topic_bus is None:
            return
        await topic_bus.emit(_NAMESPACE, event_type, payload)

    nodes = _build_nodes(body)
    return await run_workflow(
        body.input,
        nodes,
        emit=_emit,
        max_retries=body.max_retries,
    )
