# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import project_summary, analyze_risks, list_tasks

def get_reporting_agent(llm, system_prompt=None) -> Agent:
    default = "You generate concise project status reports. Reply in English."
    guardrail = "You must ONLY answer questions related to project management and Odoo. If the user asks off-topic questions, politely decline."
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default + "\n\n" + guardrail
    
    return Agent(
        role="Reporting Agent", goal="Generate status reports and risk analyses.",
        backstory=backstory,
        tools=[project_summary, analyze_risks, list_tasks],
        llm=llm, verbose=True, allow_delegation=False, max_iter=1,
    )
