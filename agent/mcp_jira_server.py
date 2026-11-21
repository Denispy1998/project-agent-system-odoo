# -*- coding: utf-8 -*-
"""MCP Server for Jira (Phase 4 - Multi-Tenancy)."""
import logging
from mcp.server.mcpserver import MCPServer

from tools.jira_tools import (
    list_jira_projects, create_jira_issue, update_jira_issue,
    delete_jira_issue, move_jira_issue
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = MCPServer("Jira MCP Server")

@mcp.tool()
def mcp_jira_list_projects(company_id: int = 0, workspace_id: int = 0) -> str:
    return list_jira_projects.func()

@mcp.tool()
def mcp_jira_create_issue(project_key: str, summary: str, description: str = "", issue_type: str = "Task", company_id: int = 0, workspace_id: int = 0) -> str:
    return create_jira_issue.func(project_key=project_key, summary=summary, description=description, issue_type=issue_type)

@mcp.tool()
def mcp_jira_update_issue(issue_key: str, summary: str = "", description: str = "", company_id: int = 0, workspace_id: int = 0) -> str:
    return update_jira_issue.func(issue_key=issue_key, summary=summary, description=description)

@mcp.tool()
def mcp_jira_delete_issue(issue_key: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return delete_jira_issue.func(issue_key=issue_key)

@mcp.tool()
def mcp_jira_move_issue(issue_key: str, target_status: str, company_id: int = 0, workspace_id: int = 0) -> str:
    return move_jira_issue.func(issue_key=issue_key, target_status=target_status)

if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8003)
