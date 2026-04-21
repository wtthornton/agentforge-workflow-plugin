"""Plugin entry point — mounts the workflow-test router onto the FastAPI app."""

from __future__ import annotations

from fastapi import FastAPI

from agentforge_workflow.routes import router


def register(app: FastAPI) -> None:
    """Called by PluginRegistry when the plugin is registered."""
    app.include_router(router)
