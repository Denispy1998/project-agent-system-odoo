# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import setup_agile_project, list_projects

def get_planning_agent(llm, system_prompt=None, allowed_tools=None) -> Agent:
    # Prompt curto para poupar tokens
    default = (
        "You are a Planner. "
        "Use setup_agile_project to create the WBS. "
        "Output the EXACT tool response. No extra text."
    )
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default

    all_tools = [setup_agile_project, list_projects]
    if allowed_tools is not None:
        all_tools = [t for t in all_tools if getattr(t, "name", "") in allowed_tools]

    return Agent(
        role="Project Planner",
        goal="Create structured project plans (WBS) in Odoo.",
        backstory=backstory,
        tools=all_tools, # Apenas 2 ferramentas essenciais
        llm=llm, verbose=False, allow_delegation=False, max_iter=3,
    )
