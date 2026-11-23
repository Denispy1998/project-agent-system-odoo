# -*- coding: utf-8 -*-
"""Adaptador MCP -> CrewAI (Fase 3.3 - Odoo + Jira)."""
import asyncio
import contextvars
from crewai.tools import tool
from mcp import ClientSession
from mcp.client.sse import sse_client

_company_id = contextvars.ContextVar('company_id', default=0)
_workspace_id = contextvars.ContextVar('workspace_id', default=0)

def set_mcp_context(company_id: int, workspace_id: int):
    _company_id.set(company_id)
    _workspace_id.set(workspace_id)

MCP_ODOO_URL = "http://127.0.0.1:8002/sse"
MCP_JIRA_URL = "http://127.0.0.1:8003/sse"

def _run_async_tool(tool_name: str, arguments: dict, server_url: str = MCP_ODOO_URL) -> str:
    arguments['company_id'] = _company_id.get()
    arguments['workspace_id'] = _workspace_id.get()

    async def _call():
        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                if result.content:
                    return result.content[0].text
                return "Sem resultado."

    try:
        try:
            loop = asyncio.get_running_loop()
            future = asyncio.run_coroutine_threadsafe(_call(), loop)
            return future.result(timeout=30)
        except RuntimeError:
            return asyncio.run(_call())
    except Exception as e:
        return f"ERROR (MCP): {str(e)}"

# ==========================================
# === ODOO TOOLS (21) ===
# ==========================================
# === READ TOOLS ===
@tool("mcp_list_projects")
def mcp_list_projects() -> str:
    """List all projects in Odoo."""
    return _run_async_tool("mcp_list_projects", {})

@tool("mcp_list_tasks")
def mcp_list_tasks(project_name: str = "") -> str:
    """List tasks of a project (or all tasks if empty)."""
    return _run_async_tool("mcp_list_tasks", {"project_name": project_name})

@tool("mcp_list_stages")
def mcp_list_stages(project_name: str) -> str:
    """List all stages of a project."""
    return _run_async_tool("mcp_list_stages", {"project_name": project_name})

@tool("mcp_analyze_risks")
def mcp_analyze_risks(project_name: str) -> str:
    """Analyze risk based on tasks without stages."""
    return _run_async_tool("mcp_analyze_risks", {"project_name": project_name})

@tool("mcp_prioritize_tasks")
def mcp_prioritize_tasks(project_name: str) -> str:
    """Prioritize tasks (no-stage first)."""
    return _run_async_tool("mcp_prioritize_tasks", {"project_name": project_name})

@tool("mcp_project_summary")
def mcp_project_summary(project_name: str) -> str:
    """Full summary of a project."""
    return _run_async_tool("mcp_project_summary", {"project_name": project_name})

# === WRITE TOOLS ===
@tool("mcp_create_project")
def mcp_create_project(name: str, tasks: str = "") -> str:
    """Create a new project. 'tasks' is comma-separated."""
    return _run_async_tool("mcp_create_project", {"name": name, "tasks": tasks})

@tool("mcp_add_task")
def mcp_add_task(project_name: str, task_name: str) -> str:
    """Add a task to a project."""
    return _run_async_tool("mcp_add_task", {"project_name": project_name, "task_name": task_name})

@tool("mcp_create_stage")
def mcp_create_stage(project_name: str, stage_name: str, sequence: int = 10) -> str:
    """Create a stage in a project."""
    return _run_async_tool("mcp_create_stage", {"project_name": project_name, "stage_name": stage_name, "sequence": sequence})

@tool("mcp_move_single_task")
def mcp_move_single_task(project_name: str, task_name: str, target_stage_name: str) -> str:
    """Move ONE task to a target stage."""
    return _run_async_tool("mcp_move_single_task", {"project_name": project_name, "task_name": task_name, "target_stage_name": target_stage_name})

@tool("mcp_move_tasks")
def mcp_move_tasks(project_name: str, task_names_csv: str, target_stage_name: str) -> str:
    """Move MULTIPLE tasks to a target stage."""
    return _run_async_tool("mcp_move_tasks", {"project_name": project_name, "task_names_csv": task_names_csv, "target_stage_name": target_stage_name})

@tool("mcp_delete_task")
def mcp_delete_task(project_name: str, task_name: str) -> str:
    """Delete a task."""
    return _run_async_tool("mcp_delete_task", {"project_name": project_name, "task_name": task_name})

@tool("mcp_delete_stage")
def mcp_delete_stage(project_name: str, stage_name: str) -> str:
    """Delete a stage (only if empty)."""
    return _run_async_tool("mcp_delete_stage", {"project_name": project_name, "stage_name": stage_name})

@tool("mcp_delete_project")
def mcp_delete_project(project_name: str) -> str:
    """Delete a project and all its tasks."""
    return _run_async_tool("mcp_delete_project", {"project_name": project_name})

@tool("mcp_move_all_tasks")
def mcp_move_all_tasks(project_name: str, target_stage_name: str) -> str:
    """Move ALL tasks to a target stage."""
    return _run_async_tool("mcp_move_all_tasks", {"project_name": project_name, "target_stage_name": target_stage_name})

@tool("mcp_set_task_status")
def mcp_set_task_status(project_name: str, task_name: str, new_status: str) -> str:
    """Change task status (in_backlog, in_progress, concluded)."""
    return _run_async_tool("mcp_set_task_status", {"project_name": project_name, "task_name": task_name, "new_status": new_status})

# === ADVANCED TOOLS ===
@tool("mcp_list_agent_templates")
def mcp_list_agent_templates() -> str:
    """List all active AI Agent templates."""
    return _run_async_tool("mcp_list_agent_templates", {})

@tool("mcp_setup_agile_project")
def mcp_setup_agile_project(project_name: str, tasks_csv: str = "") -> str:
    """Create a complete Agile project (3 stages + tasks)."""
    return _run_async_tool("mcp_setup_agile_project", {"project_name": project_name, "tasks_csv": tasks_csv})

@tool("mcp_bulk_move_tasks")
def mcp_bulk_move_tasks(project_name: str, from_stage: str, to_stage: str) -> str:
    """Move ALL tasks from one stage to another."""
    return _run_async_tool("mcp_bulk_move_tasks", {"project_name": project_name, "from_stage": from_stage, "to_stage": to_stage})

@tool("mcp_simulate_delay")
def mcp_simulate_delay(project_name: str, task_name: str, delay_days: int) -> str:
    """Simulate a task delay."""
    return _run_async_tool("mcp_simulate_delay", {"project_name": project_name, "task_name": task_name, "delay_days": delay_days})

@tool("mcp_scan_project_risks")
def mcp_scan_project_risks(project_name: str, days_threshold: int = 3) -> str:
    """Scan for imminent risks."""
    return _run_async_tool("mcp_scan_project_risks", {"project_name": project_name, "days_threshold": days_threshold})

# ==========================================
# === JIRA TOOLS (5) ===
# ==========================================
@tool("mcp_jira_list_projects")
def mcp_jira_list_projects() -> str:
    """List all Jira projects."""
    return _run_async_tool("mcp_jira_list_projects", {}, server_url=MCP_JIRA_URL)

@tool("mcp_jira_create_issue")
def mcp_jira_create_issue(project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> str:
    """Create a new Jira issue."""
    return _run_async_tool("mcp_jira_create_issue", {"project_key": project_key, "summary": summary, "description": description, "issue_type": issue_type}, server_url=MCP_JIRA_URL)

@tool("mcp_jira_update_issue")
def mcp_jira_update_issue(issue_key: str, summary: str = "", description: str = "") -> str:
    """Update an existing Jira issue."""
    return _run_async_tool("mcp_jira_update_issue", {"issue_key": issue_key, "summary": summary, "description": description}, server_url=MCP_JIRA_URL)

@tool("mcp_jira_delete_issue")
def mcp_jira_delete_issue(issue_key: str) -> str:
    """Delete a Jira issue."""
    return _run_async_tool("mcp_jira_delete_issue", {"issue_key": issue_key}, server_url=MCP_JIRA_URL)

@tool("mcp_jira_move_issue")
def mcp_jira_move_issue(issue_key: str, target_status: str) -> str:
    """Move a Jira issue to a new status (e.g., 'In Progress', 'Done')."""
    return _run_async_tool("mcp_jira_move_issue", {"issue_key": issue_key, "target_status": target_status}, server_url=MCP_JIRA_URL)

def get_all_mcp_tools(allowed_names: list = None) -> list:
    all_tools = [
        mcp_list_projects, mcp_list_tasks, mcp_list_stages, mcp_analyze_risks, mcp_prioritize_tasks, mcp_project_summary,
        mcp_create_project, mcp_add_task, mcp_create_stage, mcp_move_single_task, mcp_move_tasks,
        mcp_delete_task, mcp_delete_stage, mcp_delete_project, mcp_move_all_tasks, mcp_set_task_status,
        mcp_list_agent_templates, mcp_setup_agile_project, mcp_bulk_move_tasks, mcp_simulate_delay, mcp_scan_project_risks,
        mcp_jira_list_projects, mcp_jira_create_issue, mcp_jira_update_issue, mcp_jira_delete_issue, mcp_jira_move_issue
    ]
    if allowed_names is not None:
        return [t for t in all_tools if getattr(t, "name", "") in allowed_names]
    return all_tools
