# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import (
    list_projects, list_tasks, list_stages, analyze_risks,
    prioritize_tasks, project_summary, create_project, add_task,
    create_stage, move_single_task, move_tasks, delete_task, setup_agile_project, bulk_move_tasks,
    delete_stage, delete_project,
)

def get_project_manager_agent(llm, system_prompt=None) -> Agent:
    default = (
        "You manage Odoo data via tools. Call exactly ONE tool per request. "
        "Return the tool's output VERBATIM. Do NOT retry if you receive a SUCCESS. Reply in English."
    )
    guardrail = "You must ONLY answer questions related to project management and Odoo. If the user asks off-topic questions, politely decline."
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default + "\n\n" + guardrail
    
    return Agent(
        role="Project Manager", goal="Manage projects, tasks, stages, and risks in Odoo.",
        backstory=backstory,
        tools=[
            list_projects, list_tasks, list_stages, analyze_risks,
            prioritize_tasks, project_summary, create_project, add_task,
            create_stage, move_single_task, move_tasks, delete_task, setup_agile_project, bulk_move_tasks,
            delete_stage, delete_project,
        ],
        llm=llm, verbose=True, allow_delegation=False, max_iter=1, max_rpm=10,
    )
