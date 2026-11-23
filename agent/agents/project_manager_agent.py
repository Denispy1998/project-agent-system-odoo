# -*- coding: utf-8 -*-
from crewai import Agent
from tools.jira_tools import list_jira_projects, create_jira_issue, update_jira_issue, delete_jira_issue, move_jira_issue
from tools.mcp_adapter import get_all_mcp_tools
from tools.odoo_tools import (
    list_projects, analyze_risks, prioritize_tasks, project_summary,
    create_project, add_task, bulk_move_tasks, setup_agile_project
)

def get_project_manager_agent(llm, system_prompt=None, allowed_tools=None) -> Agent:
    default = "You are a Project Manager AI. Use the provided tools to fulfill the request. Output the EXACT tool response. No extra text."
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default
    all_tools = get_all_mcp_tools() + [create_jira_issue, list_jira_projects, update_jira_issue, delete_jira_issue, move_jira_issue, list_projects, create_project, add_task, analyze_risks, prioritize_tasks, project_summary, bulk_move_tasks, setup_agile_project]
    if allowed_tools is not None:
        all_tools = [t for t in all_tools if getattr(t, "name", "") in allowed_tools]
    return Agent(role="Project Manager", goal="Manage projects and tasks in Odoo.", backstory=backstory, tools=all_tools, llm=llm, verbose=False, allow_delegation=False, max_iter=3, max_rpm=10)
