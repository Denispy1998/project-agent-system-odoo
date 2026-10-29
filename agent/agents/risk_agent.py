# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import analyze_risks, list_tasks

def get_risk_agent(llm, system_prompt=None) -> Agent:
    default = (
        "You are a Risk Auditor. Evaluate project plans. "
        "Use analyze_risks to check the data. Suggest improvements if risk is high. "
        "Output the EXACT tool response."
    )
    guardrail = "Only analyze project risks."
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default + "\n\n" + guardrail
    
    return Agent(
        role="Risk Auditor", 
        goal="Evaluate project risks and suggest mitigations.",
        backstory=backstory,
        tools=[analyze_risks, list_tasks],
        llm=llm, verbose=True, allow_delegation=False, max_iter=1,
    )
