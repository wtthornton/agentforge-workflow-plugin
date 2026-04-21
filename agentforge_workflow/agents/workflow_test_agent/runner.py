"""Deterministic runner for the workflow-test-agent.

No LLM, no subprocess — returns a fixed sentinel string every time.
Used to exercise the AgentForge orchestrator pipeline in smoke tests.
"""

from __future__ import annotations


class WorkflowRunner:
    """Deterministic agent runner — always returns 'workflow:ok'."""

    def run(self, input_text: str) -> str:
        return "workflow:ok"
