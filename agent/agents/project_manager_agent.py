# -*- coding: utf-8 -*-
from crewai import Agent
from tools.jira_tools import list_jira_projects, create_jira_issue, update_jira_issue, delete_jira_issue, move_jira_issue
from tools.odoo_tools import (
    list_projects, analyze_risks, prioritize_tasks, project_summary,
    create_project, add_task, bulk_move_tasks, setup_agile_project
)

def get_project_manager_agent(llm, system_prompt=None) -> Agent:
    # Prompt ultra-curto para poupar tokens
    default = (
        "You are a Project Manager AI. "
        "Use the provided tools to fulfill the request. "
        "Output the EXACT tool response. No extra text."
    )
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default

    return Agent(
        role="Project Manager", 
        goal="Manage projects and tasks in Odoo.",
        backstory=backstory,
        tools=[create_jira_issue, list_jira_projects, update_jira_issue, delete_jira_issue, move_jira_issue, 
            # Mantemos apenas as ferramentas que exigem raciocínio do LLM
            # O router local já trata de: list_tasks, list_stages, create_stage, 
            # move_single_task, move_tasks, delete_task, delete_stage, delete_project, simulate_delay
            list_projects, 
            create_project, 
            add_task, 
            analyze_risks, 
            prioritize_tasks, 
            project_summary, 
            bulk_move_tasks,
            setup_agile_project
        ],
        llm=llm, verbose=False, allow_delegation=False, max_iter=1, max_rpm=10,
    )
