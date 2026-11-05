# -*- coding: utf-8 -*-
"""Agent Orchestrator – routes requests to specialized agents (CrewAI 0.175.0)."""
import os
import time
import logging
import re
from typing import Optional
from crewai import Crew, Task, LLM
from dotenv import load_dotenv

from agents.project_manager_agent import get_project_manager_agent
from agents.planning_agent import get_planning_agent
from agents.risk_agent import get_risk_agent
from agents.team_member_agent import get_team_member_agent
from agents.reporting_agent import get_reporting_agent
from agents.diagram_agent import get_diagram_agent
from agents.router import try_route

load_dotenv('/home/denispy/project-agent-system/.env')
_logger = logging.getLogger(__name__)

def _valid_key(key):
    if not key:
        return False
    k = key.strip()
    if k.lower().startswith(("your_", "sk-xxx", "xxx", "placeholder", "changeme")):
        return False
    if len(k) < 15:
        return False
    return True

def get_llm(model_name: str = "groq"):
    if model_name == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if _valid_key(key):
            return LLM(model="openai/gpt-4o", temperature=0.0, api_key=key)
        _logger.warning("OpenAI key invalid/missing -> fallback to Groq")
        return LLM(model="groq/qwen/qwen3.8-27b", max_tokens=512, temperature=0.0, api_key=os.getenv("GROQ_API_KEY"))

    if model_name == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
        if _valid_key(key):
            return LLM(model="anthropic/claude-3-5-sonnet-20241022", temperature=0.0, api_key=key)
        _logger.warning("Anthropic key invalid/missing -> fallback to Groq")
        return LLM(model="groq/qwen/qwen3.8-27b", max_tokens=512, temperature=0.0, api_key=os.getenv("GROQ_API_KEY"))

    return LLM(model="groq/qwen/qwen3.8-27b", max_tokens=512, temperature=0.0, api_key=os.getenv("GROQ_API_KEY"))

def _detect_agent(user_message: str, is_manager: bool = False) -> str:
    msg = user_message.lower()
    if any(k in msg for k in ["diagram", "flowchart", "sequence", "er diagram", "mermaid"]):
        return "diagram"
    if any(k in msg for k in ["report", "summary", "status", "debug", "list", "show", "analyze", "prioritize", "risks"]):
        return "reporting" if any(k in msg for k in ["report", "summary", "status"]) else ("team_member" if not is_manager else "project_manager")
    if any(k in msg for k in ["create", "add", "delete", "remove", "move", "update"]) and is_manager:
        return "project_manager"
    return "project_manager" if is_manager else "team_member"

def _recover_tool_output(crew):
    if crew is None:
        return None
    try:
        tasks = getattr(crew, "tasks", None) or []
        for t in reversed(tasks):
            out = getattr(t, "output", None)
            if out is None:
                continue
            raw = getattr(out, "raw", None)
            if raw and str(raw).strip():
                return str(raw)
            if isinstance(out, str) and out.strip():
                return out
    except Exception:
        pass
    return None

_DIAGRAM_KEYWORDS = ("diagram", "flowchart", "mermaid", "gantt", "pie chart", "sequence chart", "er chart", "class chart", "state chart")

def _detect_diagram_intent(msg: str) -> bool:
    m = msg.lower()
    return any(k in m for k in _DIAGRAM_KEYWORDS)

def _enforce_guardrails(message: str, guardrails: str) -> Optional[str]:
    """
    Hard Guardrail: Checks if the message violates any specific rules.
    Extracts words in ALL CAPS from the guardrail text and checks if they are in the message.
    """
    if not guardrails or not guardrails.strip():
        return None
    
    # Extrair palavras que estão em maiúsculas no guardrail (ex: "HACK")
    forbidden_terms = re.findall(r'\b[A-Z_]{3,}\b', guardrails)
    
    for term in forbidden_terms:
        if term.lower() in message.lower():
            _logger.warning(f"[Guardrail] Blocked '{term}' in message.")
            return f"DENIED by Guardrail: The term '{term}' is restricted by the active agent template rules."
    
    return None

def run_orchestrator(user_message: str, user_id: Optional[int] = None, is_manager: bool = False, model_name: str = "groq", system_prompt: Optional[str] = None, guardrails: Optional[str] = None) -> str:
    # 1. Permission Guard (RBAC)
    write_keywords = ["create", "add", "delete", "remove", "move", "update", "edit", "set ", "set\t", "mark ", "assign ", "setup", "simulate", "bulk", "criar", "adicionar", "apagar", "eliminar", "mover", "atualizar", "definir", "marcar", "atribuir"]
    msg_lower = user_message.lower()
    wants_write = any(k in msg_lower for k in write_keywords)

    if wants_write and not is_manager:
        return ("DENIED: You are signed in as a Team Member. Write operations require the 'Project Manager' role.")

    # 2. Hard Guardrails (Code-level enforcement)
    guardrail_violation = _enforce_guardrails(user_message, guardrails)
    if guardrail_violation:
        return guardrail_violation

    # 3. Inject Guardrails into System Prompt (Soft enforcement for LLM)
    if guardrails and guardrails.strip():
        if system_prompt:
            system_prompt = system_prompt + "\n\nRESTRIÇÕES E GUARDRAILS:\n" + guardrails
        else:
            system_prompt = "RESTRIÇÕES E GUARDRAILS:\n" + guardrails

    max_attempts = 3
    backoff_schedule = [30, 60, 120]
    crew = None

    # 4. Local Router
    local_result = try_route(user_message)
    if local_result is not None:
        _logger.info("Routed locally (no LLM call)")
        return local_result

    # 5. Off-topic Guardrail
    off_topic_keywords = ["poem", "poema", "cook", "cozinhar", "recipe", "receita", "weather", "clima", "joke", "piada", "story", "história", "filme", "movie"]
    if any(k in msg_lower for k in off_topic_keywords):
        _logger.info("Off-topic blocked locally (no LLM call)")
        return ("INFO: I am a Project Management AI Assistant. I can only help with projects, tasks, risks, and reports.")

    # 6. Diagram Shortcut
    if _detect_diagram_intent(user_message):
        try:
            from tools.mermaid_tools import generate_mermaid_diagram
            _logger.info("Diagram intent detected — direct tool call")
            return generate_mermaid_diagram.func(description=user_message)
        except Exception as e:
            _logger.error(f"Diagram shortcut failed: {e}")

    # 7. LLM Fallback
    for attempt in range(1, max_attempts + 1):
        try:
            llm = get_llm(model_name)
            agent_type = _detect_agent(user_message, is_manager)
            sp_lower = (system_prompt or "").lower()

            if agent_type == "diagram":
                agent = get_diagram_agent(llm, system_prompt)
                task_desc = f"Generate a Mermaid diagram for: {user_message}"
            elif "planner" in sp_lower or "planeamento" in sp_lower:
                agent = get_planning_agent(llm, system_prompt)
                task_desc = f"Create a project plan for: {user_message}"
            elif "auditor" in sp_lower or "risco" in sp_lower:
                agent = get_risk_agent(llm, system_prompt)
                task_desc = f"Evaluate risks for: {user_message}"
            elif agent_type == "reporting":
                agent = get_reporting_agent(llm, system_prompt)
                task_desc = f"Generate a status report for: {user_message}"
            elif agent_type == "project_manager":
                agent = get_project_manager_agent(llm, system_prompt)
                task_desc = user_message
            else:
                agent = get_team_member_agent(llm, system_prompt)
                task_desc = user_message

            task = Task(description=task_desc, agent=agent, expected_output="A clear, concise response in English.")
            crew = Crew(agents=[agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            return str(result)

        except Exception as e:
            err = str(e).lower()
            is_rate_limit = "rate limit" in err or "429" in err or "rate_limit" in err
            is_empty = "invalid response" in err or "none or empty" in err

            recovered = _recover_tool_output(crew)
            if recovered:
                return recovered

            if is_rate_limit and attempt < max_attempts:
                wait = backoff_schedule[attempt - 1]
                _logger.warning(f"Rate limit hit. Waiting {wait}s before retry ({attempt}/{max_attempts})...")
                time.sleep(wait)
                continue

            if is_rate_limit:
                total_wait = sum(backoff_schedule[:max_attempts - 1])
                return f"Rate limit reached on Groq free tier after {max_attempts} attempts (~{total_wait}s total). Please retry in 60 seconds."

            if is_empty:
                return "LLM returned an empty response. Please retry in 30 seconds."

            _logger.error(f"Orchestrator error: {type(e).__name__}")
            return f"Orchestrator error: {type(e).__name__}. Please retry in 30 seconds."
