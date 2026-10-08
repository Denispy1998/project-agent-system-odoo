# -*- coding: utf-8 -*-
"""Mermaid diagram generation tools — v2.2 (dynamic via LLM).

The tool delegates Mermaid code generation to the configured LLM (via
litellm, same path as the rest of the ecosystem). The diagram kind is
detected locally with a weighted-scoring rule so the LLM only focuses on
the content, keeping token usage low and output predictable. A
deterministic fallback is returned when the LLM is unavailable.
"""
import os
import re
import logging
from pathlib import Path

from crewai.tools import tool
from dotenv import load_dotenv
import litellm

_logger = logging.getLogger(__name__)

_ENV_PATH = Path("/home/denispy/project-agent-system/.env")
load_dotenv(_ENV_PATH)

_MERMAID_MODEL = os.getenv("MERMAID_MODEL", "groq/qwen/qwen3.8-27b")
_MAX_TOKENS = 512
_TIMEOUT = 30

_HEADERS = {
    "flowchart": "flowchart TD",
    "sequence": "sequenceDiagram",
    "er": "erDiagram",
    "class": "classDiagram",
    "state": "stateDiagram-v2",
    "gantt": "gantt",
    "pie": "pie",
}

# Weighted keywords: (kind, keyword, weight). Higher weight wins.
# Weights reflect specificity — "sequence diagram" beats "flow".
_KEYWORDS = [
    # ---- sequence (high specificity) ----
    ("sequence", "sequence diagram",     10),
    ("sequence", "sequencediagram",      10),
    ("sequence", "sequence",              8),
    ("sequence", "interaction diagram",   9),
    ("sequence", "lifeline",              7),
    ("sequence", "message flow",          8),
    ("sequence", "call flow",             8),
    # ---- ER ----
    ("er", "er diagram",                 10),
    ("er", "erdiagram",                  10),
    ("er", "entity relationship",         9),
    ("er", "entity",                      6),
    ("er", "database schema",             8),
    ("er", "schema",                      5),
    # ---- class ----
    ("class", "class diagram",           10),
    ("class", "classdiagram",            10),
    ("class", "uml class",                8),
    ("class", "object model",             7),
    # ---- state ----
    ("state", "state diagram",           10),
    ("state", "statediagram",            10),
    ("state", "state machine",            9),
    ("state", "lifecycle",                6),
    # ---- gantt ----
    ("gantt", "gantt",                   10),
    ("gantt", "timeline",                 7),
    ("gantt", "roadmap",                  6),
    # ---- pie ----
    ("pie", "pie chart",                 10),
    ("pie", "pie",                        8),
    ("pie", "distribution",               5),
    # ---- flowchart (lowest priority — most generic) ----
    ("flowchart", "flowchart",           10),
    ("flowchart", "flow chart",          10),
    ("flowchart", "workflow",             6),
    ("flowchart", "process",              5),
    ("flowchart", "pipeline",             5),
    ("flowchart", "steps",                4),
]


def _detect_kind(description: str) -> str:
    """Pick the best diagram kind via weighted keyword scoring."""
    desc = description.lower()
    scores = {}
    for kind, kw, weight in _KEYWORDS:
        if kw in desc:
            scores[kind] = scores.get(kind, 0) + weight
    if not scores:
        return "flowchart"
    # Highest score wins; ties broken by insertion order of _HEADERS.
    order = list(_HEADERS.keys())
    return max(scores.items(), key=lambda kv: (kv[1], -order.index(kv[0])))[0]


def _extract_mermaid_block(text: str):
    """Return the first ```mermaid ... ``` block, or wrap raw mermaid text."""
    if not text:
        return None
    m = re.search(r"```mermaid\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        body = m.group(1).strip()
        return "```mermaid\n" + body + "\n```"
    first = text.strip().splitlines()[0] if text.strip() else ""
    prefixes = ("flowchart", "graph ", "sequenceDiagram", "erDiagram",
                "classDiagram", "stateDiagram", "gantt", "pie")
    if any(first.startswith(p) for p in prefixes):
        return "```mermaid\n" + text.strip() + "\n```"
    return None


def _fallback(kind: str) -> str:
    """Deterministic minimal diagram used when the LLM is unavailable."""
    if kind == "sequence":
        return "```mermaid\nsequenceDiagram\n    A->>B: Request\n    B-->>A: Response\n```"
    if kind == "er":
        return ("```mermaid\nerDiagram\n"
                "    USER ||--o{ PROJECT : has\n"
                "    PROJECT ||--o{ TASK : contains\n```")
    if kind == "class":
        return ("```mermaid\nclassDiagram\n"
                "    class Project {\n        +String name\n    }\n"
                "    class Task {\n        +String title\n    }\n"
                "    Project \"1\" --> \"*\" Task\n```")
    if kind == "state":
        return ("```mermaid\nstateDiagram-v2\n"
                "    [*] --> InBacklog\n"
                "    InBacklog --> InProgress\n"
                "    InProgress --> Concluded\n"
                "    Concluded --> [*]\n```")
    if kind == "gantt":
        return ("```mermaid\ngantt\n"
                "    title Project Plan\n"
                "    dateFormat YYYY-MM-DD\n"
                "    section Phase 1\n"
                "    Analysis :a1, 2026-01-01, 10d\n"
                "    section Phase 2\n"
                "    Build    :a2, after a1, 15d\n```")
    if kind == "pie":
        return ("```mermaid\npie title Task Distribution\n"
                "    \"In Backlog\" : 40\n"
                "    \"In Progress\" : 35\n"
                "    \"Concluded\" : 25\n```")
    return "```mermaid\nflowchart TD\n    A[Start] --> B[Process]\n    B --> C[End]\n```"


def _call_llm(kind: str, description: str):
    """Ask the LLM for the Mermaid body. Returns None on any failure."""
    header = _HEADERS[kind]
    system_prompt = (
        "You are a Mermaid diagram generator. "
        "Return ONLY a single fenced code block starting with ```mermaid and "
        "ending with ```. Do NOT add any explanation, title, or prose outside "
        "the code block. Use valid Mermaid syntax. Keep the diagram focused "
        "and readable."
    )
    user_prompt = (
        "Generate a Mermaid '" + kind + "' diagram.\n"
        "Required first line after the opening fence: " + header + "\n"
        "Description:\n" + description
    )

    try:
        response = litellm.completion(
            model=_MERMAID_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=_MAX_TOKENS,
            temperature=0.2,
            timeout=_TIMEOUT,
        )
        content = response.choices[0].message.content or ""
        return _extract_mermaid_block(content)
    except Exception as e:
        _logger.warning("[mermaid_tools] LLM call failed (%s): %s", kind, e)
        return None


@tool("generate_mermaid_diagram")
def generate_mermaid_diagram(description: str) -> str:
    """Generate a Mermaid diagram code from a natural language description.

    Supports: flowchart, sequence diagram, ER diagram, class diagram,
    state diagram, Gantt chart, pie chart. Falls back to a deterministic
    minimal diagram if the LLM is unavailable.
    """
    if not description or not description.strip():
        return _fallback("flowchart")

    kind = _detect_kind(description)
    body = _call_llm(kind, description)
    return body if body else _fallback(kind)
