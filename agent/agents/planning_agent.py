# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import list_projects, list_tasks, setup_agile_project, simulate_delay

def get_planning_agent(llm, system_prompt=None) -> Agent:
    default = (
        "You are a Project Planner. Decompose the goal into stages and tasks. "
        "Use the setup_agile_project tool to create it. Output the EXACT tool response."
    )
    guardrail = "Only manage project planning."
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default + "\n\n" + guardrail
    
    return Agent(
        role="Project Planner", 
        goal="Create structured project plans (WBS) in Odoo.",
        backstory=backstory,
        tools=[setup_agile_project, list_projects, list_tasks, simulate_delay],
        llm=llm, verbose=True, allow_delegation=False, max_iter=1,
    )
