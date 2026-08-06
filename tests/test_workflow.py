"""Unit tests for ``run_workflow`` — retry + halt + event emission (TAP-759).

No AgentForge deps — ``emit`` is a recording async callable.
"""

from __future__ import annotations

from typing import Any

import pytest

from agentforge_workflow.nodes import BrokenNodeB, FlakyNodeB, NodeA, NodeB, NodeC
from agentforge_workflow.workflow import run_workflow


class _Recorder:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    async def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append((event_type, payload))

    def types(self) -> list[str]:
        return [t for t, _ in self.events]


@pytest.mark.asyncio
async def test_run_workflow_happy_path() -> None:
    rec = _Recorder()
    result = await run_workflow("abc", [NodeA(), NodeB(), NodeC()], emit=rec.emit)
    assert result == {"output": "cba-transformed", "nodes_run": ["a", "b", "c"]}
    # 3 nodes × (start + success) = 6 events, in order.
    assert rec.types() == [
        "a.start",
        "a.success",
        "b.start",
        "b.success",
        "c.start",
        "c.success",
    ]


@pytest.mark.asyncio
async def test_run_workflow_halts_on_permanent_failure() -> None:
    rec = _Recorder()
    result = await run_workflow("abc", [NodeA(), BrokenNodeB(), NodeC()], emit=rec.emit)
    assert "error" in result
    assert result["error"]["node"] == "b"
    assert result["nodes_run"] == ["a"]
    # C must never have started
    assert "c.start" not in rec.types()
    assert "c.success" not in rec.types()
    # B emitted start + failure (no retry for permanent)
    assert "b.start" in rec.types()
    assert "b.failure" in rec.types()
    assert "b.retry" not in rec.types()


@pytest.mark.asyncio
async def test_run_workflow_retries_and_succeeds() -> None:
    rec = _Recorder()
    # Fails once, then succeeds on retry.
    result = await run_workflow(
        "abc",
        [NodeA(), FlakyNodeB(fail_count=1), NodeC()],
        emit=rec.emit,
        max_retries=2,
    )
    assert result["output"] == "cba-transformed"
    assert result["nodes_run"] == ["a", "b", "c"]
    assert rec.types().count("b.start") == 2  # original + retry
    assert "b.retry" in rec.types()
    assert "b.success" in rec.types()


@pytest.mark.asyncio
async def test_run_workflow_exhausts_retries() -> None:
    rec = _Recorder()
    # Always transient — 3 attempts (1 + 2 retries) then fails.
    result = await run_workflow(
        "abc",
        [NodeA(), FlakyNodeB(fail_count=10), NodeC()],
        emit=rec.emit,
        max_retries=2,
    )
    assert "error" in result
    assert result["error"]["node"] == "b"
    assert result["error"]["attempts"] == 3
    assert rec.types().count("b.start") == 3
    assert rec.types().count("b.retry") == 2
    failures = [e for e in rec.events if e[0] == "b.failure"]
    assert len(failures) == 1
    assert failures[0][1]["kind"] == "transient-exhausted"
