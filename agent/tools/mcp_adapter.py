# -*- coding: utf-8 -*-
"""
Adaptador que converte as ferramentas do MCP Server em ferramentas CrewAI.
"""
import asyncio
import json
from crewai.tools import tool
from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_ODOO_URL = "http://127.0.0.1:8002/sse"

# Cache global para guardar as ferramentas descobertas
_MCP_TOOLS_CACHE = {}

def _run_async_tool(tool_name: str, arguments: dict) -> str:
    """Executa uma ferramenta MCP num loop asyncio (necessário porque o CrewAI é sync)."""
    async def _call():
        async with sse_client(MCP_ODOO_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                if result.content:
                    return result.content[0].text
                return "A ferramenta não devolveu resultado."
    
    try:
        # Verificar se já há um loop a correr
        try:
            loop = asyncio.get_running_loop()
            # Se estivermos dentro de um loop, usar run_coroutine_threadsafe ou similar
            future = asyncio.run_coroutine_threadsafe(_call(), loop)
            return future.result(timeout=30)
        except RuntimeError:
            # Se não houver loop, criar um novo
            return asyncio.run(_call())
    except Exception as e:
        return f"ERROR (MCP): {str(e)}"

def get_odoo_mcp_tools() -> list:
    """Retorna uma lista de ferramentas CrewAI mapeadas para o MCP Server do Odoo."""
    
    # 1. Definir as ferramentas manualmente (para manter controlo do schema)
    @tool("mcp_list_projects")
    def mcp_list_projects() -> str:
        """List all projects in Odoo via MCP."""
        return _run_async_tool("mcp_list_projects", {})

    @tool("mcp_create_project")
    def mcp_create_project(name: str, tasks: str = "") -> str:
        """Create a new project in Odoo via MCP. 'tasks' is a comma-separated list."""
        return _run_async_tool("mcp_create_project", {"name": name, "tasks": tasks})

    @tool("mcp_analyze_risks")
    def mcp_analyze_risks(project_name: str) -> str:
        """Analyze the risk level of a project via MCP."""
        return _run_async_tool("mcp_analyze_risks", {"project_name": project_name})

    return [mcp_list_projects, mcp_create_project, mcp_analyze_risks]

def get_all_mcp_tools() -> list:
    """Função pública para obter todas as ferramentas MCP (Odoo + Jira no futuro)."""
    tools = []
    tools.extend(get_odoo_mcp_tools())
    return tools
