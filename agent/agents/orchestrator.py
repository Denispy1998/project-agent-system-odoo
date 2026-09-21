# -*- coding: utf-8 -*-
"""Agent Orchestrator – routes requests to specialized agents (CrewAI 0.175.0)."""
import os
import time
import traceback
from typing import Optional
from crewai import Crew, Task, LLM
from dotenv import load_dotenv

from agents.project_manager_agent import get_project_manager_agent
from agents.team_member_agent import get_team_member_agent
from agents.reporting_agent import get_reporting_agent
from agents.diagram_agent import get_diagram_agent

load_dotenv('/home/denispy/project-agent-system/.env')


def get_llm(model_name: str = "groq"):
    """Return a CrewAI LLM instance based on the selected model."""
    if model_name == "openai":
        return LLM(
            model="openai/gpt-4o",
            temperature=0.0,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    if model_name == "anthropic":
        return LLM(
            model="anthropic/claude-3-5-sonnet-20241022",
            temperature=0.0,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    return LLM(
        model="groq/qwen/qwen3.8-27b",
        temperature=0.0,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def _detect_agent(user_message: str, is_manager: bool = False) -> str:
    msg = user_message.lower()
    if any(k in msg for k in ["diagram", "flowchart", "sequence", "er diagram", "mermaid"]):
        return "diagram"
    if any(k in msg for k in ["report", "summary", "status", "debug", "list", "show",
                              "analyze", "prioritize", "risks"]):
        return "reporting" if any(k in msg for k in ["report", "summary", "status"]) else (
            "team_member" if not is_manager else "project_manager"
        )
    if any(k in msg for k in ["create", "add", "delete", "remove", "move", "update"]) and is_manager:
        return "project_manager"
    return "project_manager" if is_manager else "team_member"


def run_orchestrator(
    user_message: str,
    user_id: Optional[int] = None,
    is_manager: bool = False,
    model_name: str = "groq",
    deep_thinking: bool = False,
) -> str:
    # === Permission guard: block write intents for team members ===
    write_keywords = ["create", "add", "delete", "remove", "move", "update", "edit",
                      "criar", "adicionar", "apagar", "eliminar", "mover", "atualizar"]
    msg_lower = user_message.lower()
    wants_write = any(k in msg_lower for k in write_keywords)

    if wants_write and not is_manager:
        return (
            "DENIED: You are signed in as a Team Member. "
            "Write operations (create/add/delete/move/update) require the "
            "'Project Manager' role. Please contact an administrator if you "
            "need this permission. You can still ask me to list projects, "
            "list tasks, analyze risks, prioritize work, or generate summaries."
        )

    max_attempts = 3
    wait_seconds = 65

    for attempt in range(1, max_attempts + 1):
        try:
            llm = get_llm(model_name)
            agent_type = _detect_agent(user_message, is_manager)

            if agent_type == "diagram":
                agent = get_diagram_agent(llm)
                task_desc = f"Generate a Mermaid diagram for: {user_message}"
            elif agent_type == "reporting":
                agent = get_reporting_agent(llm)
                task_desc = f"Generate a status report for: {user_message}"
            elif agent_type == "project_manager":
                agent = get_project_manager_agent(llm)
                task_desc = user_message
            else:
                agent = get_team_member_agent(llm)
                task_desc = user_message

            if deep_thinking:
                task_desc = (
                    "THINK STEP-BY-STEP before answering. Take your time to reason about "
                    "the problem, consider alternatives, and verify your plan. "
                    "Then provide a clear, final answer.\n\n"
                    f"User request: {task_desc}"
                )

            task = Task(
                description=task_desc,
                agent=agent,
                expected_output="A clear, concise response in English.",
            )
            crew = Crew(agents=[agent], tasks=[task], verbose=True)
            result = crew.kickoff()
            return str(result)

        except Exception as e:
            err = str(e).lower()
            is_rate_limit = "rate limit" in err or "429" in err or "rate_limit" in err
            if is_rate_limit and attempt < max_attempts:
                print(f"[Orchestrator] Rate limit hit. Waiting {wait_seconds}s "
                      f"before retry ({attempt}/{max_attempts})...")
                time.sleep(wait_seconds)
                continue
            return f"Orchestrator error: {e}\n{traceback.format_exc()}"

    return "Orchestrator error: max retry attempts reached."
