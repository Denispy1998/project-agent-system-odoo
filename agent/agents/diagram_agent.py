# -*- coding: utf-8 -*-
from crewai import Agent

def get_diagram_agent(llm, system_prompt=None) -> Agent:
    default = (
        """You are a Mermaid diagram expert. Generate ONLY the Mermaid code enclosed in ```mermaid ... ```. Do NOT add explanations."""
    )
    guardrail = "You must ONLY answer questions related to project management and Odoo. If the user asks off-topic questions, politely decline."
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default + "\n\n" + guardrail
    
    return Agent(
        role="Diagram Agent", goal="Generate Mermaid diagrams based on user requests.",
        backstory=backstory,
        llm=llm, verbose=True, allow_delegation=False, max_iter=1,
    )
