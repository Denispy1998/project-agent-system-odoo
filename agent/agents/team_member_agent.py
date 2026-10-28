# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import (
    list_projects, list_tasks, list_stages, analyze_risks,
    prioritize_tasks, project_summary,
)

def get_team_member_agent(llm, system_prompt=None) -> Agent:
    default = (
        "You have read-only access. Call exactly ONE tool per request. "
        "Return the tool's output VERBATIM. Reply in English."
    )
    guardrail = "You must ONLY answer questions related to project management and Odoo. If the user asks off-topic questions, politely decline."
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default + "\n\n" + guardrail
    
    return Agent(
        role="Team Member", goal="Read project data from Odoo.",
        backstory=backstory,
        tools=[
            list_projects, list_tasks, list_stages, analyze_risks,
            prioritize_tasks, project_summary,
        ],
        llm=llm, verbose=True, allow_delegation=False, max_iter=1,
    )
