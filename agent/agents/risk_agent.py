# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import analyze_risks, scan_project_risks

def get_risk_agent(llm, system_prompt=None) -> Agent:
    # Prompt ultra-curto para poupar tokens
    default = (
        "You are a Risk Auditor. "
        "Use analyze_risks or scan_project_risks. "
        "Output the EXACT tool response. No extra text."
    )
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default

    return Agent(
        role="Risk Auditor",
        goal="Evaluate project risks.",
        backstory=backstory,
        tools=[analyze_risks, scan_project_risks], # Apenas 2 ferramentas
        llm=llm, verbose=False, allow_delegation=False, max_iter=1,
    )
