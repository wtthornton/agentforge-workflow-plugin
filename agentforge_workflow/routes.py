"""Workflow test plugin routes."""

from __future__ import annotations

from fastapi import APIRouter

from agentforge_workflow import __version__

router = APIRouter(prefix="/api/workflow-test", tags=["workflow-test"])


@router.get("/status")
async def status() -> dict:
    return {"status": "ok", "plugin": "workflow-test", "version": __version__}
