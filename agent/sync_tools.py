import asyncio
import xmlrpc.client
import os
import argparse
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client

# Carregar variáveis de ambiente
load_dotenv(os.path.expanduser("~/project-agent-system/.env"), override=True)

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

MCP_SERVERS = {
    "http://127.0.0.1:8002/sse": "Odoo MCP",
    "http://127.0.0.1:8003/sse": "Jira MCP"
}

async def fetch_tools_from_sse(url):
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            return tools.tools

async def main():
    parser = argparse.ArgumentParser(description="Sync MCP Tools to Odoo AI Governance")
    parser.add_argument('--company_id', type=int, required=True, help="Odoo Company ID to sync tools for")
    args = parser.parse_args()
    company_id = args.company_id

    print(f"🚀 A ligar ao Odoo (Company ID: {company_id})...")
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        print("❌ Falha na autenticação do Odoo. Verifica as credenciais no .env.")
        return
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    for url, server_name in MCP_SERVERS.items():
        print(f"\n🔍 A extrair ferramentas do {server_name} ({url})...")
        try:
            tools = await fetch_tools_from_sse(url)
            for t in tools:
                # Verificar se a tool já existe PARA ESTA EMPRESA
                existing = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'ai.tool', 'search', [[('name', '=', t.name), ('company_id', '=', company_id)]])
                
                vals = {
                    'description': t.description,
                    'tool_type': 'mcp_server',
                    'mcp_server_url': url,
                    'company_id': company_id,
                }

                if not existing:
                    vals['name'] = t.name
                    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'ai.tool', 'create', [vals])
                    print(f"  + Criada: {t.name}")
                else:
                    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'ai.tool', 'write', [existing, vals])
                    print(f"  - Atualizada: {t.name}")
        except Exception as e:
            print(f"❌ Erro ao ligar ao {server_name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
