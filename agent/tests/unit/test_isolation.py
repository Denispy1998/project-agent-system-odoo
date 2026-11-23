import pytest
from agents_api.main import get_cache_key
from agents.router import try_route

def test_cache_key_multi_tenant():
    # Mesma mensagem, empresas diferentes
    k1 = get_cache_key("msg", 1, True, "groq", None, None, 1, 0, allowed_tools="['a']", agent_id=1)
    k2 = get_cache_key("msg", 1, True, "groq", None, None, 2, 0, allowed_tools="['a']", agent_id=1)
    assert k1 != k2, "Cache keys devem diferir entre empresas"

    # Mesma mensagem, ferramentas permitidas diferentes
    k3 = get_cache_key("msg", 1, True, "groq", None, None, 1, 0, allowed_tools="['b']", agent_id=1)
    assert k1 != k3, "Cache keys devem diferir consoante as allowed_tools"

    # Mesma mensagem, agentes diferentes
    k4 = get_cache_key("msg", 1, True, "groq", None, None, 1, 0, allowed_tools="['a']", agent_id=2)
    assert k1 != k4, "Cache keys devem diferir entre agentes"

def test_router_blocks_disallowed_tools():
    # Se a lista de tools for vazia, o router deve devolver None (passa para o LLM) e NÃO executar a tool
    result = try_route("list all projects", allowed_tools=[])
    assert result is None, "O router deve bloquear tools não autorizadas e devolver None"

    # Se a tool estiver autorizada, o router deve tentar executá-la (pode devolver um erro se o Odoo estiver off, mas não None)
    result_allowed = try_route("list all projects", allowed_tools=["mcp_list_projects", "list_projects"])
    assert result_allowed is not None, "O router deve permitir tools autorizadas"
