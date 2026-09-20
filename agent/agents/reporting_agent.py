# -*- coding: utf-8 -*-
"""Reporting Agent (CrewAI 0.175.0 compatible)."""
from crewai import Agent
from tools.odoo_tools import list_projects, list_tasks, analyze_risks


def get_reporting_agent(llm) -> Agent:
    return Agent(
        role="Reporting Specialist",
        goal="Generate project status reports and summaries.",
        backstory=(
            "You are a Reporting AI. You can list projects, list tasks, and analyze risks "
            "to produce concise status reports. "
            "IMPORTANT: You must use the provided tools to answer. "
            "When you need to list projects, you MUST call the tool named 'list_projects'. "
            "Do not just say you will do it; actually call the tool. "
            "Always respond in English."
        ),
        tools=[list_projects, list_tasks, analyze_risks],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
