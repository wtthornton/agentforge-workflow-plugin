# agentforge-workflow-plugin

Test rig for the AgentForge orchestrator pipeline (TAP-759).

Provides a deterministic `WorkflowRunner` agent and a smoke-test suite that
exercises `step_match()` and `AgentLoader.load_external()` without any LLM
calls or subprocess execution.

## Structure

```
agentforge_workflow/
  __init__.py              # version
  plugin.json              # plugin manifest (id: workflow-test, namespace: project.workflow-test)
  plugin.py                # register(app) — mounts the status router
  routes.py                # GET /api/workflow-test/status
  agents/
    workflow_test_agent/
      AGENT.md             # agent definition (namespace: project.workflow-test.workflow-test-agent)
      runner.py            # WorkflowRunner.run() → "workflow:ok"
tests/
  test_runner.py           # pure unit tests for WorkflowRunner (no AgentForge deps)
backend/tests/
  test_workflow_smoke.py   # integration smoke tests (skipped if plugin not installed)
```

## Install

```bash
# From AgentForge repo root (editable install into the project venv):
uv pip install -e /path/to/agentforge-workflow-plugin
```

## Run smoke tests

```bash
uv run pytest backend/tests/test_workflow_smoke.py -v
```

Tests are skipped automatically if the plugin is not installed.

## What is tested

| Test | What it verifies |
|---|---|
| `test_workflow_runner_is_deterministic` | `WorkflowRunner.run()` returns `"workflow:ok"` every time |
| `test_workflow_agent_loads` | `AgentLoader.load_external()` registers the agent with correct runner + namespace |
| `test_step_match_finds_workflow_agent` | `step_match()` with `config_hint` bypasses the matcher and resolves directly |
| `test_task_context_config_hint` | `TaskContext` carries `config_hint` and auto-generates IDs |
| `test_step_match_no_hint_calls_matcher` | Without hint, `step_match()` delegates to `match_async` (mocked) |
