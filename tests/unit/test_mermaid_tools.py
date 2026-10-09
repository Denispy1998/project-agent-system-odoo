"""Unit tests for tools/mermaid_tools.py — pure helpers only.

The LLM call (_call_llm) is NOT exercised here; only the local
detection/fallback logic. The full pipeline is covered by the smoke
test (tests/smoke_test.py).
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


def test_detect_kind_sequence():
    from tools.mermaid_tools import _detect_kind
    assert _detect_kind("draw a sequence diagram of login") == "sequence"
    assert _detect_kind("sequence diagram between user and server") == "sequence"
    assert _detect_kind("message flow of order processing") == "sequence"


def test_detect_kind_flow_vs_sequence_priority():
    """Regression for the bug fixed in T2 (weighted scoring).

    The phrase 'login flow' contains 'flow' (flowchart keyword, weight 5)
    but the stronger 'sequence diagram' (weight 10) must win.
    """
    from tools.mermaid_tools import _detect_kind
    assert _detect_kind("draw a sequence diagram of the login flow") == "sequence"


def test_detect_kind_er():
    from tools.mermaid_tools import _detect_kind
    assert _detect_kind("er diagram for user project task") == "er"
    assert _detect_kind("entity relationship between users and orders") == "er"
    assert _detect_kind("database schema for inventory") == "er"


def test_detect_kind_class_state_gantt_pie():
    from tools.mermaid_tools import _detect_kind
    assert _detect_kind("class diagram for project management") == "class"
    assert _detect_kind("state diagram for task lifecycle") == "state"
    assert _detect_kind("gantt chart for the roadmap") == "gantt"
    assert _detect_kind("pie chart of task distribution") == "pie"


def test_detect_kind_default_flowchart():
    from tools.mermaid_tools import _detect_kind
    # No specific keyword -> default
    assert _detect_kind("draw something complex") == "flowchart"
    assert _detect_kind("workflow for deployment") == "flowchart"


def test_fallback_produces_valid_kind():
    from tools.mermaid_tools import _fallback
    for kind in ["flowchart", "sequence", "er", "class", "state", "gantt", "pie"]:
        out = _fallback(kind)
        assert out.startswith("```mermaid")
        assert out.rstrip().endswith("```")


def test_fallback_fenced_block_contains_kind_marker():
    from tools.mermaid_tools import _fallback
    assert "sequenceDiagram" in _fallback("sequence")
    assert "erDiagram" in _fallback("er")
    assert "classDiagram" in _fallback("class")
    assert "stateDiagram" in _fallback("state")
    assert "gantt" in _fallback("gantt")
    assert "pie" in _fallback("pie")
    assert "flowchart" in _fallback("flowchart")


def test_extract_mermaid_block_from_fenced():
    from tools.mermaid_tools import _extract_mermaid_block
    text = "Here you go:\n```mermaid\nflowchart TD\n    A --> B\n```\n"
    out = _extract_mermaid_block(text)
    assert out is not None
    assert out.startswith("```mermaid")
    assert "flowchart TD" in out


def test_extract_mermaid_block_from_raw():
    from tools.mermaid_tools import _extract_mermaid_block
    text = "flowchart TD\n    A --> B"
    out = _extract_mermaid_block(text)
    assert out is not None
    assert "flowchart TD" in out


def test_extract_mermaid_block_returns_none_on_garbage():
    from tools.mermaid_tools import _extract_mermaid_block
    assert _extract_mermaid_block("just some prose without any diagram") is None
    assert _extract_mermaid_block("") is None
    assert _extract_mermaid_block(None) is None


def test_headers_cover_all_kinds():
    from tools.mermaid_tools import _HEADERS
    for kind in ["flowchart", "sequence", "er", "class", "state", "gantt", "pie"]:
        assert kind in _HEADERS
