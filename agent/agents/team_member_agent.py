# -*- coding: utf-8 -*-
from crewai import Agent
from tools.odoo_tools import (
    list_projects, list_tasks, list_stages, analyze_risks,
    prioritize_tasks, project_summary,
)

def get_team_member_agent(llm, system_prompt=None) -> Agent:
    default = (
        """You are an expert Project Manager AI. Your goal is to execute Odoo tasks.
CRITICAL RULES:
1. Call exactly ONE tool per request.
2. Output the EXACT text returned by the tool without changing a word. Do NOT summarize.
3. Do NOT add conversational filler. Do NOT retry if you receive a SUCCESS.
"""
    )
    guardrail = "You must ONLY answer questions related to project management and Odoo. If the user asks off-topic questions, politely decline."
    backstory = (system_prompt + "\n\n" if system_prompt else "") + default + "\n\n" + guardrail
    
    return Agent(
        role="Team Member", goal="Read project data from Odoo.",
        backstory=backstory,
        tools=[
            list_projects, list_tasks, list_stages, analyze_risks,
            prioritize_tasks, project_summary,
        ],
        llm=llm, verbose=True, allow_delegation=False, max_iter=1,
    )
