# -*- coding: utf-8 -*-
"""Team Member Agent (read-only)."""
from crewai import Agent
from tools.odoo_tools import (
    list_projects, list_tasks, list_stages,
    analyze_risks, prioritize_tasks, project_summary,
)


def get_team_member_agent(llm) -> Agent:
    return Agent(
        role="Team Member",
        goal="Consult projects, tasks, stages, risks, and priorities.",
        backstory=(
            "You are a Team Member AI with read-only access.\n\n"
            "RULES:\n"
            "1. Call AT MOST ONE tool per request.\n"
            "2. Your final answer MUST be the tool's response copied VERBATIM.\n"
            "3. Do NOT paraphrase or rewrite. Do NOT add extra text.\n\n"
            "Respond in English."
        ),
        tools=[
            list_projects, list_tasks, list_stages,
            analyze_risks, prioritize_tasks, project_summary,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=1,
        max_rpm=10,
    )
