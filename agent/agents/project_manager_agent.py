# -*- coding: utf-8 -*-
"""Project Manager Agent (CrewAI 0.175.0 compatible)."""
from crewai import Agent
from tools.odoo_tools import (
    list_projects, list_tasks, list_stages, analyze_risks,
    prioritize_tasks, project_summary,
    create_project, add_task, create_stage,
    move_single_task, move_tasks,
    delete_task, delete_stage, delete_project,
)


def get_project_manager_agent(llm) -> Agent:
    return Agent(
        role="Project Manager",
        goal="Manage projects, tasks, stages, and risks in Odoo.",
        backstory=(
            "You manage Odoo data via tools. Call exactly ONE tool per request. "
            "Return the tool's output VERBATIM — no paraphrase, no extra text, "
            "no second tool to verify. Tools are idempotent. Reply in English."
        ),
        tools=[
            list_projects, list_tasks, list_stages, analyze_risks,
            prioritize_tasks, project_summary,
            create_project, add_task, create_stage,
            move_single_task, move_tasks,
            delete_task, delete_stage, delete_project,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=1,
        max_rpm=10,
    )
