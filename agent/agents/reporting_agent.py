# -*- coding: utf-8 -*-
"""Reporting Agent (CrewAI 0.175.0 compatible)."""
from crewai import Agent
from tools.odoo_tools import list_projects, list_tasks, analyze_risks


def get_reporting_agent(llm) -> Agent:
    return Agent(
        role="Reporting Specialist",
        goal="Generate project status reports and summaries.",
        backstory=(
            "You generate concise project reports. Use the provided tools "
            "(list_projects, list_tasks, analyze_risks). Reply in English."
        ),
        tools=[list_projects, list_tasks, analyze_risks],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=1,
        max_rpm=10,
    )
