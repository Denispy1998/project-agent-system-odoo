"""Unit tests for pure helpers in agents/orchestrator.py.

The orchestrator's run_orchestrator() hits CrewAI/LLM and is out of
scope here (covered by smoke test). We only test:
- _detect_diagram_intent()
- the permission-guard verb list (regression for T8)
"""
import sys

sys.path.insert(0, "/home/denispy/project-agent-system")

import pytest


def test_detect_diagram_intent_true():
    from agents.orchestrator import _detect_diagram_intent
    assert _detect_diagram_intent("draw a flowchart") is True
    assert _detect_diagram_intent("state diagram for lifecycle") is True
    assert _detect_diagram_intent("show me a mermaid diagram") is True
    assert _detect_diagram_intent("gantt chart for roadmap") is True
    assert _detect_diagram_intent("pie chart of tasks") is True


def test_detect_diagram_intent_false():
    from agents.orchestrator import _detect_diagram_intent
    assert _detect_diagram_intent("list all projects") is False
    assert _detect_diagram_intent("create a task") is False
    assert _detect_diagram_intent("analyze risks") is False
    assert _detect_diagram_intent("") is False


def test_write_keywords_include_router_verbs():
    """Regression for T8.

    The permission guard must recognise EVERY write verb used by the
    router's write patterns. If a new verb is added to router.py and
    not here, a Team Member could bypass the guard (see T8).
    """
    import inspect
    from agents import orchestrator as orch

    src = inspect.getsource(orch.run_orchestrator)

    # These verbs appear in router.py write patterns.
    # Accept both bare ("create") and suffix-qualified ("set ", "mark\\t")
    # forms, since the guard uses the latter for verbs that would
    # otherwise be prefixes of common words (settings, marker).
    required_verbs = ["create", "add", "delete", "move", "update",
                      "set", "mark"]

    for verb in required_verbs:
        candidates = [
            f'"{verb}"',   f"'{verb}'",     # exact bare
            f'"{verb} "',  f"'{verb} '",    # trailing space
            f'"{verb}\\t"', f"'{verb}\\t'",  # trailing tab
        ]
        found = any(c in src for c in candidates)
        assert found, f"write verb {verb!r} missing from orchestrator guard"


def test_permission_guard_denies_team_member(monkeypatch):
    """A Team Member asking for a write must be denied without hitting
    CrewAI. run_orchestrator should return a DENIED string immediately."""
    from agents import orchestrator as orch

    # Sabotage the router so we know if it's called
    def _boom(_msg):
        raise AssertionError("try_route should NOT be called for a denied write")
    monkeypatch.setattr(orch, "try_route", _boom)

    result = orch.run_orchestrator(
        user_message="create a new project called Hack",
        user_id=6,
        is_manager=False,
        model_name="groq",
    )
    assert result.startswith("DENIED")
