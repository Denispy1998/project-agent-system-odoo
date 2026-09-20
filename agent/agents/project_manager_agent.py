# -*- coding: utf-8 -*-
"""Project Manager Agent (CrewAI 0.175.0 compatible)."""
from crewai import Agent
from tools.odoo_tools import (
    list_projects, list_tasks, list_stages, analyze_risks,
    prioritize_tasks, project_summary,
    create_project, add_task, create_stage,
    move_single_task, move_tasks,
    delete_task, delete_stage, delete_project,
    debug_list_all_tasks,
)


def get_project_manager_agent(llm) -> Agent:
    return Agent(
        role="Project Manager",
        goal="Manage projects, tasks, stages, and risks in Odoo.",
        backstory=(
            "You are a Project Manager AI that manages Odoo data via tools.\n\n"
            "════════ CRITICAL RULES ════════\n"
            "1. Call EXACTLY ONE tool per user request. Never retry, never verify.\n"
            "2. Your final answer MUST be the tool's response copied VERBATIM, "
            "character-for-character.\n"
            "3. Do NOT paraphrase, summarize, or rewrite the tool output.\n"
            "4. Do NOT add any text before or after the tool response.\n"
            "5. Do NOT call a second tool to double-check the first one.\n"
            "6. Trust the tool's response as final. It is idempotent: the same "
            "message is returned whether the object was created or already existed.\n"
            "7. Never invent information not present in the tool response.\n\n"
            "Always respond in English."
        ),
        tools=[
            list_projects, list_tasks, list_stages, analyze_risks,
            prioritize_tasks, project_summary,
            create_project, add_task, create_stage,
            move_single_task, move_tasks,
            delete_task, delete_stage, delete_project,
            debug_list_all_tasks,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=1,
        max_rpm=10,
    )
