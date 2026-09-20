# -*- coding: utf-8 -*-
"""Mermaid diagram generation tools (CrewAI 0.175.0 compatible)."""
from crewai.tools import tool


@tool("generate_mermaid_diagram")
def generate_mermaid_diagram(description: str) -> str:
    """Generate a Mermaid diagram code from a natural language description."""
    desc = description.lower()
    if "flowchart" in desc or "process" in desc:
        return "```mermaid\nflowchart TD\n    A[Start] --> B[Process]\n    B --> C[End]\n```"
    if "sequence" in desc or "interaction" in desc:
        return "```mermaid\nsequenceDiagram\n    A->>B: Request\n    B-->>A: Response\n```"
    if "er" in desc or "entity" in desc or "database" in desc:
        return "```mermaid\nerDiagram\n    USER ||--o{ PROJECT : has\n    PROJECT ||--o{ TASK : contains\n```"
    return "```mermaid\nflowchart LR\n    A --> B\n```"
