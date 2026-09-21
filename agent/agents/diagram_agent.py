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
            "IMPORTANT: You MUST call the tool 'generate_mermaid_diagram' exactly ONCE. "
            "Do NOT retry the tool. Do NOT call it multiple times. "
            "After the tool returns, respond with the diagram code only. "
            "Always respond in English."
        ),
        tools=[generate_mermaid_diagram],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=2,
    )
