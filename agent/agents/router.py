# -*- coding: utf-8 -*-
"""Lightweight local router for the AI Project Management Ecosystem.

Matches common user intents with regex and calls the corresponding tool
directly. This bypasses the LLM (and its rate limits) for the vast majority
of requests, cutting latency from ~3s to ~50ms.

Only intents NOT matched here fall through to the CrewAI orchestrator,
which calls the LLM for reasoning tasks (reports, diagrams, ambiguous
queries).
"""
import re
from typing import Optional

from tools.odoo_tools import (
    list_projects, list_tasks, list_stages,
    analyze_risks, prioritize_tasks, project_summary,
    create_project, add_task, create_stage,
    move_single_task,
    delete_task, delete_stage, delete_project,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_quotes(s: str) -> str:
    return s.strip().strip("'\"").strip()

def _clean_name(s: str) -> str:
    return _strip_quotes(s)

# ---------------------------------------------------------------------------
# Regex patterns (order matters — most specific first)
# ---------------------------------------------------------------------------

# READ patterns -------------------------------------------------------------
PATTERNS = [
    # list_projects
    (re.compile(r"^\s*(list|show|display)\s+(all\s+)?projects?\s*$", re.I),
     lambda m: list_projects.func()),

    # list_tasks — various phrasings
    (re.compile(r"^\s*(list|show|display)\s+(all\s+)?tasks?\s+(in|of|from)\s+"
                r"(?:project\s+)?[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: list_tasks.func(project_name=_clean_name(m.group(4)))),

    # list_stages
    (re.compile(r"^\s*(list|show|display)\s+(all\s+)?stages?\s+(in|of|from)\s+"
                r"(?:project\s+)?[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: list_stages.func(project_name=_clean_name(m.group(4)))),

    # analyze_risks
    (re.compile(r"^\s*(analyze|analyse|check|evaluate)\s+(the\s+)?risks?\s+"
                r"(of|for|in)\s+(?:project\s+)?[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: analyze_risks.func(project_name=_clean_name(m.group(4)))),

    # prioritize_tasks
    (re.compile(r"^\s*prioriti[sz]e\s+(the\s+)?tasks?\s+(in|of|for)\s+"
                r"(?:project\s+)?[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: prioritize_tasks.func(project_name=_clean_name(m.group(4)))),

    # project_summary
    (re.compile(r"^\s*(summary|status|overview)\s+(of|for|in)\s+"
                r"(?:project\s+)?[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: project_summary.func(project_name=_clean_name(m.group(3)))),

    # WRITE patterns --------------------------------------------------------
    # create_project
    (re.compile(r"^\s*create\s+(a\s+)?(new\s+)?project\s+(called|named)\s+"
                r"[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: create_project.func(name=_clean_name(m.group(4)))),

    # add_task
    (re.compile(r"^\s*add\s+(a\s+)?task\s+(called|named)\s+[\"']?(.+?)[\"']?\s+"
                r"(in|to)\s+(?:project\s+)?[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: add_task.func(
         project_name=_clean_name(m.group(5)),
         task_name=_clean_name(m.group(3)))),

    # create_stage
    (re.compile(r"^\s*create\s+(a\s+)?stage\s+(called|named)\s+[\"']?(.+?)[\"']?\s+"
                r"(in|of|to)\s+(?:project\s+)?[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: create_stage.func(
         project_name=_clean_name(m.group(5)),
         stage_name=_clean_name(m.group(3)))),

    # move_single_task
    (re.compile(r"^\s*move\s+(the\s+)?task\s+[\"']?(.+?)[\"']?\s+"
                r"to\s+stage\s+[\"']?(.+?)[\"']?\s+"
                r"(in|of)\s+(?:project\s+)?[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: move_single_task.func(
         project_name=_clean_name(m.group(5)),
         task_name=_clean_name(m.group(2)),
         target_stage_name=_clean_name(m.group(3)))),

    # delete_task
    (re.compile(r"^\s*delete\s+(the\s+)?task\s+[\"']?(.+?)[\"']?\s+"
                r"(from|in|of)\s+(?:project\s+)?[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: delete_task.func(
         project_name=_clean_name(m.group(4)),
         task_name=_clean_name(m.group(2)))),

    # delete_stage
    (re.compile(r"^\s*delete\s+(the\s+)?stage\s+[\"']?(.+?)[\"']?\s+"
                r"(from|in|of)\s+(?:project\s+)?[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: delete_stage.func(
         project_name=_clean_name(m.group(4)),
         stage_name=_clean_name(m.group(2)))),

    # delete_project
    (re.compile(r"^\s*delete\s+(the\s+)?project\s+[\"']?(.+?)[\"']?\s*$", re.I),
     lambda m: delete_project.func(project_name=_clean_name(m.group(2)))),
]


def try_route(message: str) -> Optional[str]:
    """Try to match the message with a local regex pattern.

    Returns the tool's response if a match is found; None otherwise
    (caller falls back to the LLM-based orchestrator).
    """
    if not message:
        return None
    for pattern, handler in PATTERNS:
        m = pattern.match(message)
        if m:
            try:
                return handler(m)
            except Exception as e:
                # If a matching regex triggers a tool error, fall through
                # to the LLM rather than crashing.
                return f"ERROR: {type(e).__name__}: {e}"
    return None
