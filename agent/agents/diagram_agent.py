# -*- coding: utf-8 -*-
from crewai import Agent
from tools.mermaid_tools import generate_mermaid_diagram

def get_diagram_agent(llm, system_prompt=None, allowed_tools=None) -> Agent:
    default = (
        "You are a Mermaid diagram expert. "
        "Use the generate_mermaid_diagram tool to create the diagram. "
        "Output the EXACT tool response."
    )
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default

    all_tools = [generate_mermaid_diagram]
    if allowed_tools is not None:
        all_tools = [t for t in all_tools if getattr(t, "name", "") in allowed_tools]

    return Agent(
        role="Diagram Agent", goal="Generate Mermaid diagrams.",
        backstory=backstory,
        tools=all_tools, # Ferramenta adicionada!
        llm=llm, verbose=False, allow_delegation=False, max_iter=3,
    )
