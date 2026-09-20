# -*- coding: utf-8 -*-
"""Diagram Agent (CrewAI 0.175.0 compatible)."""
from crewai import Agent
from tools.mermaid_tools import generate_mermaid_diagram


def get_diagram_agent(llm) -> Agent:
    return Agent(
        role="Diagram Generator",
        goal="Generate Mermaid diagrams from natural language descriptions.",
        backstory=(
            "You are a Diagram AI. You can create flowcharts, sequence diagrams, "
            "and ER diagrams using Mermaid syntax. "
            "IMPORTANT: You must use the provided tool to generate the diagram. "
            "When you need to generate a diagram, you MUST call the tool named 'generate_mermaid_diagram'. "
            "Do not just say you will do it; actually call the tool. "
            "Always respond in English."
        ),
        tools=[generate_mermaid_diagram],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
