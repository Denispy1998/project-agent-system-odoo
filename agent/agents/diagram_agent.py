# -*- coding: utf-8 -*-
from crewai import Agent
from tools.mermaid_tools import generate_mermaid_diagram

def get_diagram_agent(llm, system_prompt=None) -> Agent:
    default = (
        "You are a Mermaid diagram expert. "
        "Use the generate_mermaid_diagram tool to create the diagram. "
        "Output the EXACT tool response."
    )
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default

    return Agent(
        role="Diagram Agent", goal="Generate Mermaid diagrams.",
        backstory=backstory,
        tools=[generate_mermaid_diagram], # Ferramenta adicionada!
        llm=llm, verbose=False, allow_delegation=False, max_iter=1,
    )
