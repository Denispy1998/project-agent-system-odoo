# -*- coding: utf-8 -*-
"""MCP Server for Odoo (Phase 4 - Multi-Tenancy)."""
import logging
from mcp.server.mcpserver import MCPServer

from tools.odoo_tools import (
    list_projects, list_tasks, list_stages, analyze_risks, prioritize_tasks, project_summary,
    create_project, add_task, create_stage, move_single_task, move_tasks,
    delete_task, delete_stage, delete_project, move_all_tasks, set_task_status,
    list_agent_templates, setup_agile_project, bulk_move_tasks, simulate_delay, scan_project_risks
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = MCPServer("Odoo MCP Server")

@mcp.tool()
def mcp_list_projects(company_id: int = 0, workspace_id: int = 0) -> str:
    return list_projects.func()

@mcp.tool()
def mcp_list_tasks(project_name: str = "", company_id: int = 0, workspace_id: int = 0) -> str:
    return list_tasks.func(project_name=project_name)

@mcp.tool()
def mcp_list_stages(project_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return list_stages.func(project_name=project_name)

@mcp.tool()
def mcp_analyze_risks(project_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return analyze_risks.func(project_name=project_name)

@mcp.tool()
def mcp_prioritize_tasks(project_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return prioritize_tasks.func(project_name=project_name)

@mcp.tool()
def mcp_project_summary(project_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return project_summary.func(project_name=project_name)

@mcp.tool()
def mcp_create_project(name: str, tasks: str = "", company_id: int = 0, workspace_id: int = 0) -> str:
    return create_project.func(name=name, tasks=tasks)

@mcp.tool()
def mcp_add_task(project_name: str, task_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return add_task.func(project_name=project_name, task_name=task_name)

@mcp.tool()
def mcp_create_stage(project_name: str, stage_name: str, sequence: int = 10, company_id: int = 0, workspace_id: int = 0) -> str:
    return create_stage.func(project_name=project_name, stage_name=stage_name, sequence=sequence)

@mcp.tool()
def mcp_move_single_task(project_name: str, task_name: str, target_stage_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return move_single_task.func(project_name=project_name, task_name=task_name, target_stage_name=target_stage_name)

@mcp.tool()
def mcp_move_tasks(project_name: str, task_names_csv: str, target_stage_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return move_tasks.func(project_name=project_name, task_names_csv=task_names_csv, target_stage_name=target_stage_name)

@mcp.tool()
def mcp_delete_task(project_name: str, task_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return delete_task.func(project_name=project_name, task_name=task_name)

@mcp.tool()
def mcp_delete_stage(project_name: str, stage_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return delete_stage.func(project_name=project_name, stage_name=stage_name)

@mcp.tool()
def mcp_delete_project(project_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return delete_project.func(project_name=project_name)

@mcp.tool()
def mcp_move_all_tasks(project_name: str, target_stage_name: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return move_all_tasks.func(project_name=project_name, target_stage_name=target_stage_name)

@mcp.tool()
def mcp_set_task_status(project_name: str, task_name: str, new_status: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return set_task_status.func(project_name=project_name, task_name=task_name, new_status=new_status)

@mcp.tool()
def mcp_list_agent_templates(company_id: int = 0, workspace_id: int = 0) -> str:
    return list_agent_templates.func()

@mcp.tool()
def mcp_setup_agile_project(project_name: str, tasks_csv: str = "", company_id: int = 0, workspace_id: int = 0) -> str:
    return setup_agile_project.func(project_name=project_name, tasks_csv=tasks_csv)

@mcp.tool()
def mcp_bulk_move_tasks(project_name: str, from_stage: str, to_stage: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return bulk_move_tasks.func(project_name=project_name, from_stage=from_stage, to_stage=to_stage)

@mcp.tool()
def mcp_simulate_delay(project_name: str, task_name: str, delay_days: int, company_id: int = 0, workspace_id: int = 0) -> str:
    return simulate_delay.func(project_name=project_name, task_name=task_name, delay_days=delay_days)

@mcp.tool()
def mcp_scan_project_risks(project_name: str, days_threshold: int = 3, company_id: int = 0, workspace_id: int = 0) -> str:
    return scan_project_risks.func(project_name=project_name, days_threshold=days_threshold)

if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8002)
