# -*- coding: utf-8 -*-
from crewai import Agent
from tools.jira_tools import list_jira_projects
from tools.odoo_tools import (
    list_projects, list_tasks, list_stages, analyze_risks,
    prioritize_tasks, project_summary,
)

def get_team_member_agent(llm, system_prompt=None) -> Agent:
    default = (
        "You are a Team Member AI. Your goal is to read data from Odoo. "
        "Call exactly ONE tool per request. Output the EXACT tool response. "
        "Do NOT summarize or add extra text."
    )
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default

    return Agent(
        role="Team Member", goal="Read project data from Odoo.",
        backstory=backstory,
        tools=[list_jira_projects, 
            list_projects, list_tasks, list_stages, analyze_risks,
            prioritize_tasks, project_summary,
        ],
        llm=llm, verbose=False, allow_delegation=False, max_iter=3,
    )
