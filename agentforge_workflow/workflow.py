"""A→B→C workflow execution with retry + event emission (TAP-759).

Sequential, deterministic, no LLM. Emits ``project.workflow.<node>.start`` /
``.success`` / ``.failure`` via an injected emit-callable so the module
stays agnostic of the specific event bus (the plugin hands it a bound
``TopicBus.emit`` or a test double).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from agentforge_workflow.nodes import PermanentFailure, TransientFailure

logger = logging.getLogger(__name__)

# Signature: emit(event_type, payload) — source_namespace is bound by the caller.
EmitCallable = Callable[[str, dict[str, Any]], Awaitable[None]]


class _Node(Protocol):
    name: str

    def run(self, text: str) -> str: ...


async def run_workflow(
    input_text: str,
    nodes: list[_Node],
    *,
    emit: EmitCallable,
    max_retries: int = 2,
) -> dict[str, Any]:
    """Execute ``nodes`` in order, emitting events at each boundary.

    Retry policy: a ``TransientFailure`` triggers up to ``max_retries`` additional
    attempts (default 2 → 3 total). A ``PermanentFailure`` short-circuits with
    no retries. Any other exception is treated as permanent.

    Returns ``{"output": str, "nodes_run": [...]}`` on full success, or
    ``{"error": {"node": str, "message": str, "attempts": int}, "nodes_run": [...]}``
    if any node fails terminally.
    """
    text = input_text
    nodes_run: list[str] = []

    for node in nodes:
        attempts = 0
        while True:
            attempts += 1
            await emit(f"{node.name}.start", {"attempt": attempts, "input": text})
            try:
                text = node.run(text)
            except TransientFailure as exc:
                if attempts <= max_retries:
                    logger.info(
                        "node %s transient failure (attempt %d/%d): %s",
                        node.name,
                        attempts,
                        max_retries + 1,
                        exc,
                    )
                    await emit(
                        f"{node.name}.retry",
                        {"attempt": attempts, "error": str(exc)},
                    )
                    continue
                await emit(
                    f"{node.name}.failure",
                    {
                        "attempt": attempts,
                        "error": str(exc),
                        "kind": "transient-exhausted",
                    },
                )
                return {
                    "error": {
                        "node": node.name,
                        "message": str(exc),
                        "attempts": attempts,
                    },
                    "nodes_run": nodes_run,
                }
            except Exception as exc:  # noqa: BLE001 — PermanentFailure + anything else
                kind = (
                    "permanent" if isinstance(exc, PermanentFailure) else "unexpected"
                )
                await emit(
                    f"{node.name}.failure",
                    {"attempt": attempts, "error": str(exc), "kind": kind},
                )
                return {
                    "error": {
                        "node": node.name,
                        "message": str(exc),
                        "attempts": attempts,
                    },
                    "nodes_run": nodes_run,
                }
            # Success
            await emit(f"{node.name}.success", {"attempt": attempts, "output": text})
            nodes_run.append(node.name)
            break

    return {"output": text, "nodes_run": nodes_run}
