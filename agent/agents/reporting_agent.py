# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import project_summary, analyze_risks, list_tasks

def get_reporting_agent(llm, system_prompt=None) -> Agent:
    default = (
        "You are a Reporting AI. Your goal is to generate status reports. "
        "Call exactly ONE tool per request. Output the EXACT tool response. "
        "Do NOT summarize or add extra text."
    )
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default

    return Agent(
        role="Reporting Agent", goal="Generate status reports and risk analyses.",
        backstory=backstory,
        tools=[project_summary, analyze_risks, list_tasks],
        llm=llm, verbose=False, allow_delegation=False, max_iter=3,
    )
