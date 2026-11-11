# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import setup_agile_project, list_projects

def get_planning_agent(llm, system_prompt=None) -> Agent:
    # Prompt curto para poupar tokens
    default = (
        "You are a Planner. "
        "Use setup_agile_project to create the WBS. "
        "Output the EXACT tool response. No extra text."
    )
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default

    return Agent(
        role="Project Planner",
        goal="Create structured project plans (WBS) in Odoo.",
        backstory=backstory,
        tools=[setup_agile_project, list_projects], # Apenas 2 ferramentas essenciais
        llm=llm, verbose=False, allow_delegation=False, max_iter=3,
    )
