# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import project_summary, analyze_risks, list_tasks

def get_reporting_agent(llm, system_prompt=None, allowed_tools=None) -> Agent:
    default = (
        "You are a Reporting AI. Your goal is to generate status reports. "
        "Call exactly ONE tool per request. Output the EXACT tool response. "
        "Do NOT summarize or add extra text."
    )
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default

    all_tools = [project_summary, analyze_risks, list_tasks]
    if allowed_tools is not None:
        all_tools = [t for t in all_tools if getattr(t, "name", "") in allowed_tools]

    return Agent(
        role="Reporting Agent", goal="Generate status reports and risk analyses.",
        backstory=backstory,
        tools=all_tools,
        llm=llm, verbose=False, allow_delegation=False, max_iter=3,
    )
