# -*- coding: utf-8 -*-
"""
MCP Server for Odoo (Phase 2).
Exposes Odoo tools via Model Context Protocol.
"""
import os
import logging
from mcp.server.mcpserver import MCPServer

# Import existing tools from the ecosystem
from tools.odoo_tools import list_projects, create_project, analyze_risks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP Server
mcp = MCPServer("Odoo MCP Server")

@mcp.tool()
def mcp_list_projects() -> str:
    """List all projects in Odoo."""
    logger.info("MCP: list_projects called")
    # CrewAI decorator wraps the function, so we use .func() to call the raw logic
    return list_projects.func()

@mcp.tool()
def mcp_create_project(name: str, tasks: str = "") -> str:
    """Create a new project in Odoo. 'tasks' is a comma-separated list of task names."""
    logger.info(f"MCP: create_project called for '{name}'")
    return create_project.func(name=name, tasks=tasks)

@mcp.tool()
def mcp_analyze_risks(project_name: str) -> str:
    """Analyze the risk level of a project based on tasks without stages."""
    logger.info(f"MCP: analyze_risks called for '{project_name}'")
    return analyze_risks.func(project_name=project_name)

if __name__ == "__main__":
    # Run the server using SSE (Server-Sent Events) on port 8002
    logger.info("Starting Odoo MCP Server on 127.0.0.1:8002...")
    mcp.run(transport="sse", host="127.0.0.1", port=8002)
