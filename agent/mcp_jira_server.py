# -*- coding: utf-8 -*-
"""MCP Server for Jira (Phase 3.3)."""
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
def mcp_jira_list_projects() -> str:
    """List all Jira projects."""
    logger.info("MCP: jira_list_projects called")
    return list_jira_projects.func()

@mcp.tool()
def mcp_jira_create_issue(project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> str:
    """Create a new Jira issue."""
    logger.info(f"MCP: jira_create_issue called (project='{project_key}')")
    return create_jira_issue.func(project_key=project_key, summary=summary, description=description, issue_type=issue_type)

@mcp.tool()
def mcp_jira_update_issue(issue_key: str, summary: str = "", description: str = "") -> str:
    """Update an existing Jira issue."""
    logger.info(f"MCP: jira_update_issue called (issue='{issue_key}')")
    return update_jira_issue.func(issue_key=issue_key, summary=summary, description=description)

@mcp.tool()
def mcp_jira_delete_issue(issue_key: str) -> str:
    """Delete a Jira issue."""
    logger.info(f"MCP: jira_delete_issue called (issue='{issue_key}')")
    return delete_jira_issue.func(issue_key=issue_key)

@mcp.tool()
def mcp_jira_move_issue(issue_key: str, target_status: str) -> str:
    """Move a Jira issue to a new status (e.g. 'In Progress', 'Done')."""
    logger.info(f"MCP: jira_move_issue called (issue='{issue_key}' -> '{target_status}')")
    return move_jira_issue.func(issue_key=issue_key, target_status=target_status)

if __name__ == "__main__":
    logger.info("Starting Jira MCP Server (5 tools) on 127.0.0.1:8003...")
    mcp.run(transport="sse", host="127.0.0.1", port=8003)
