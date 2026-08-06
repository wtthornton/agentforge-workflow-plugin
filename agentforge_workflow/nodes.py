"""Three deterministic transforms for the A→B→C workflow rig (TAP-759).

Each node is a tiny callable with:

- ``name``: stable identifier used in event topics.
- ``run(text: str) -> str``: pure transform, no I/O.

Node B optionally supports a ``fail_first_n_calls`` knob: the first N calls
raise :class:`TransientFailure`, the (N+1)th succeeds. This is the only
stateful behaviour across nodes — used by the retry-succeeds-on-attempt-2
smoke test. Keeping it on a dedicated subclass (``FlakyNodeB``) so the base
``NodeB`` stays a pure function.
"""

from __future__ import annotations


class TransientFailure(RuntimeError):
    """Raised by a node to signal a retryable failure."""


class PermanentFailure(RuntimeError):
    """Raised by a node to signal a non-retryable failure."""


class NodeA:
    name = "a"

    def run(self, text: str) -> str:
        # Pass-through — kept as a real transform so the pipeline has three
        # distinct stages instead of two useful + one no-op cosmetic.
        return text


class NodeB:
    name = "b"

    def run(self, text: str) -> str:
        return text[::-1]


class NodeC:
    name = "c"

    def run(self, text: str) -> str:
        return f"{text}-transformed"


class FlakyNodeB(NodeB):
    """Node B that raises ``TransientFailure`` on the first ``fail_count`` calls."""

    def __init__(self, fail_count: int) -> None:
        self._remaining = fail_count

    def run(self, text: str) -> str:
        if self._remaining > 0:
            self._remaining -= 1
            raise TransientFailure(
                f"node-b transient failure (remaining={self._remaining})"
            )
        return super().run(text)


class BrokenNodeB(NodeB):
    """Node B that always raises ``PermanentFailure`` — used for halt-chain test."""

    def run(self, text: str) -> str:
        raise PermanentFailure("node-b is permanently broken")
