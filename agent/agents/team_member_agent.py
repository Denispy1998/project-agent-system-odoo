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
            "You are a read-only assistant. Call at most ONE tool per request. "
            "Return the tool output VERBATIM. Reply in English."
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
