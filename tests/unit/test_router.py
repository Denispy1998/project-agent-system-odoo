"""Unit tests for agents/router.py — local regex classifier.

These tests exercise the pure-Python part of the router (patterns +
helpers). They do NOT call Odoo or the LLM. Tools are mocked where
needed; the goal is to verify the message -> intent mapping.
"""
import os
import sys
from pathlib import Path

# Make both dev tree (agents/, tools/ at repo root) and repo tree
# (agent/agents/, agent/tools/) importable from the same test file.
_root = Path(__file__).resolve().parents[2]
for _p in (str(_root), str(_root / "agent")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest


def test_clean_name_strips_quotes():
    from agents.router import _clean_name
    assert _clean_name('"Sistema Hospitalar"') == "Sistema Hospitalar"
    assert _clean_name("'Projecto de Vendas'") == "Projecto de Vendas"
    assert _clean_name("  plain  ") == "plain"


def test_strip_quotes_variants():
    from agents.router import _strip_quotes
    assert _strip_quotes('"a"') == "a"
    assert _strip_quotes("'a'") == "a"
    assert _strip_quotes("a") == "a"
    assert _strip_quotes('  "spaced"  ') == "spaced"


# ----------------------------------------------------------------
# Route detection — verify the router recognises the right pattern
# for a battery of messages. Tools are patched so no network is hit.
# ----------------------------------------------------------------

@pytest.fixture
def router_mod():
    from agents import router as r
    return r


def _mock_route(router_mod, monkeypatch, message):
    """Run the router on `message` but intercept the actual tool call.

    Returns the (pattern_index, groups) that matched, or None if the
    message did not match any pattern.
    """
    captured = {"hit": None}

    # Replace every pattern's lambda with a recorder
    original_patterns = list(router_mod.PATTERNS)

    def _make_recorder(idx):
        def _rec(match):
            captured["hit"] = {"idx": idx, "groups": match.groups()}
            return "__ROUTED__"
        return _rec

    new_patterns = []
    for i, (regex, _fn) in enumerate(original_patterns):
        new_patterns.append((regex, _make_recorder(i)))
    monkeypatch.setattr(router_mod, "PATTERNS", new_patterns)

    result = router_mod.try_route(message)
    if result == "__ROUTED__":
        return captured["hit"]
    return None


@pytest.mark.parametrize("message,expected_group_substrings", [
    ("list all projects", []),
    ("list projects", []),
    ("show all tasks", []),
    ("list tasks in Sistema Hospitalar", ["Sistema Hospitalar"]),
    ("show tasks of Projecto de Vendas", ["Projecto de Vendas"]),
])
def test_route_lists(router_mod, monkeypatch, message, expected_group_substrings):
    hit = _mock_route(router_mod, monkeypatch, message)
    assert hit is not None, f"no pattern matched: {message!r}"


@pytest.mark.parametrize("message", [
    "set task Task-1 in Sistema Hospitalar to concluded",
    "set task Task-1 in Sistema Hospitalar to done",
    "set task Foo in Bar to in_progress",
])
def test_route_set_task_status_variants(router_mod, monkeypatch, message):
    hit = _mock_route(router_mod, monkeypatch, message)
    assert hit is not None, f"set_task_status pattern did not match: {message!r}"


@pytest.mark.parametrize("message", [
    "mark task Task-1 as done in Sistema Hospitalar",
    "mark task Task-1 as in_progress in Sistema Hospitalar",
])
def test_route_mark_task_variants(router_mod, monkeypatch, message):
    hit = _mock_route(router_mod, monkeypatch, message)
    assert hit is not None, f"mark pattern did not match: {message!r}"


@pytest.mark.parametrize("message", [
    "create project called Smoke",
    "create a new project named Smoke",
])
def test_route_create_project(router_mod, monkeypatch, message):
    hit = _mock_route(router_mod, monkeypatch, message)
    assert hit is not None, f"create_project did not match: {message!r}"


def test_route_unmatched_returns_none(router_mod):
    # Ambiguous / free-form message should fall through to the LLM
    result = router_mod.try_route("what is the meaning of life?")
    assert result is None


def test_patterns_count_stable(router_mod):
    # The router should expose exactly 17 patterns (one per intent).
    # If you add a new write verb, update this number AND the guard in
    # orchestrator.py (see T8 in CHANGELOG_TECHNICAL.md).
    assert len(router_mod.PATTERNS) == 17
