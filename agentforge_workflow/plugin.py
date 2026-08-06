"""Plugin entry point — mounts the workflow-test router onto the FastAPI app."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI

logger = logging.getLogger(__name__)

_AGENTS_DIR = Path(__file__).parent / "agents"
_NAMESPACE = "project.workflow-test"


def register(app: FastAPI) -> None:
    from agentforge_workflow.routes import demo_router, router

    app.include_router(router)
    app.include_router(demo_router)

    agent_loader = getattr(app.state, "agent_loader", None)
    if agent_loader is None:
        logger.debug(
            "workflow-test plugin: no agent_loader on app.state — skipping agent load"
        )
        return

    try:
        newly_loaded = agent_loader.load_external(_AGENTS_DIR, _NAMESPACE)
        logger.info("workflow-test plugin: loaded %d agent(s)", len(newly_loaded))
    except Exception:
        logger.exception("workflow-test plugin: agent load failed")
