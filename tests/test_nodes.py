"""Unit tests for the A→B→C transforms (TAP-759).

Pure / deterministic — no AgentForge deps. Keep these tests fast so the
plugin package is installable + testable in isolation.
"""

from __future__ import annotations

import pytest

from agentforge_workflow.nodes import (
    BrokenNodeB,
    FlakyNodeB,
    NodeA,
    NodeB,
    NodeC,
    PermanentFailure,
    TransientFailure,
)


def test_node_a_is_passthrough() -> None:
    assert NodeA().run("abc") == "abc"
    assert NodeA().run("") == ""


def test_node_b_reverses() -> None:
    assert NodeB().run("abc") == "cba"
    assert NodeB().run("abcd") == "dcba"
    assert NodeB().run("") == ""


def test_node_c_appends_suffix() -> None:
    assert NodeC().run("cba") == "cba-transformed"
    assert NodeC().run("") == "-transformed"


def test_pipeline_happy_composition() -> None:
    text = "abc"
    text = NodeA().run(text)
    text = NodeB().run(text)
    text = NodeC().run(text)
    assert text == "cba-transformed"


def test_flaky_node_b_fails_then_succeeds() -> None:
    b = FlakyNodeB(fail_count=2)
    with pytest.raises(TransientFailure):
        b.run("abc")
    with pytest.raises(TransientFailure):
        b.run("abc")
    # 3rd call succeeds
    assert b.run("abc") == "cba"


def test_flaky_node_b_zero_failures() -> None:
    b = FlakyNodeB(fail_count=0)
    assert b.run("abc") == "cba"


def test_broken_node_b_always_raises() -> None:
    b = BrokenNodeB()
    with pytest.raises(PermanentFailure):
        b.run("abc")
    # still broken on subsequent calls
    with pytest.raises(PermanentFailure):
        b.run("xyz")
