"""Unit tests for WorkflowRunner — pure determinism, no I/O."""

from agentforge_workflow.agents.workflow_test_agent.runner import WorkflowRunner


def test_run_returns_sentinel():
    r = WorkflowRunner()
    assert r.run("any input") == "workflow:ok"


def test_run_is_deterministic():
    r = WorkflowRunner()
    results = {r.run(f"input {i}") for i in range(10)}
    assert results == {"workflow:ok"}


def test_run_ignores_input():
    r = WorkflowRunner()
    assert r.run("") == "workflow:ok"
    assert r.run("different prompt") == "workflow:ok"
