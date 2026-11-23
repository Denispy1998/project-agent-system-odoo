import logging
_logger = logging.getLogger(__name__)

from fastapi import FastAPI
from pydantic import BaseModel, Field
import os
import sys
import time
sys.path.append('/home/denispy/project-agent-system')

from agents.orchestrator import run_orchestrator
from tools.odoo_tools import verify_user_is_manager, _call as _odoo_call

app = FastAPI(title='Project Agent API')
API_VERSION = '3.2.0'

CACHE_DB = {}
CACHE_TTL = 300

# Lista de verbos que indicam uma operação de escrita
WRITE_KEYWORDS = [
    "create", "add", "delete", "remove", "move", "update", "edit",
    "set ", "set\t", "mark ", "assign ", "setup", "simulate", "bulk",
    "criar", "adicionar", "apagar", "eliminar", "mover", "atualizar",
    "definir", "marcar", "atribuir"
]

def get_cache_key(message, user_id, is_manager, model_name, system_prompt, guardrails, company_id, workspace_id, allowed_tools=None):
    return f"{company_id}_{workspace_id}_{user_id}_{is_manager}_{model_name}_{system_prompt}_{guardrails}_{message}"

def get_cached_response(key):
    if key in CACHE_DB:
        cached_time, response = CACHE_DB[key]
        if time.time() - cached_time < CACHE_TTL:
            return response
        else:
            del CACHE_DB[key]
    return None

def set_cache_response(key, response):
    if len(CACHE_DB) > 100:
        CACHE_DB.clear()
    CACHE_DB[key] = (time.time(), response)

class ChatRequest(BaseModel):
    company_id: int = 0
    workspace_id: int = 0
    message: str = Field(..., max_length=2000)
    user_id: int = 0
    is_manager: bool = False
    model_name: str = 'groq'
    system_prompt: str | None = None
    guardrails: str | None = None
    allowed_tools: list[str] = []

class ChatResponse(BaseModel):
    response: str

@app.post('/agent/run', response_model=ChatResponse)
def run_agent(req: ChatRequest):
    if not req.message or not req.message.strip():
        return ChatResponse(response="ERROR: Message cannot be empty.")

    if req.user_id:
        user_exists = _odoo_call('res.users', 'search_count', [[('id', '=', req.user_id)]])
        if not user_exists:
            return ChatResponse(response=f"ERROR: User with ID {req.user_id} not found.")

    # Phase 6: Agent Lifecycle Check
    if req.company_id > 0:
        try:
            _logger.info(f"[LIFECYCLE] A verificar agente para company_id={req.company_id}")
            active_agents = _odoo_call('ai.agent', 'search', [[('company_id', '=', req.company_id), ('state', '=', 'running')]])
            
            if not active_agents:
                return ChatResponse(response="ERROR: System Paused. There is no AI Agent in 'Running' state for this Organization. Please go to AI Governance > Agents and click 'Start'.")
            else:
                _logger.info(f"[LIFECYCLE] Agente(s) encontrado(s): {active_agents}")
        except Exception as e:
            _logger.error(f"Failed to check agent state: {e}")

    client_claims_manager = bool(req.is_manager)
    if client_claims_manager and req.user_id:
        server_truth = verify_user_is_manager(req.user_id)
        if not server_truth:
            _logger.warning(f'[PermissionGuard] user_id={req.user_id} claimed manager -> downgraded')
        effective_is_manager = server_truth
    else:
        effective_is_manager = False

    cache_key = get_cache_key(req.message, req.user_id, effective_is_manager, req.model_name, req.system_prompt, req.guardrails, req.company_id, req.workspace_id, allowed_tools=str(sorted(req.allowed_tools)))
    cached_result = get_cached_response(cache_key)

    if cached_result:
        _logger.info(f'[CACHE] Hit para: "{req.message[:50]}..."')
        return ChatResponse(response=cached_result)

    _logger.info(f'[ORCHESTRATOR] A processar: "{req.message[:50]}..."')
    start_time = time.time()
    status = 'success'
    error_msg = ''
    
    try:
        result, tokens_used = run_orchestrator(
            user_message=req.message,
            user_id=req.user_id,
            is_manager=effective_is_manager,
            model_name=req.model_name,
            system_prompt=req.system_prompt,
            guardrails=req.guardrails,
            company_id=req.company_id,
            workspace_id=req.workspace_id,
            allowed_tools=req.allowed_tools
        )
        if result.startswith("ERROR"):
            status = 'error'
            error_msg = result
    except Exception as e:
        result = f"ERROR: {str(e)}"
        status = 'error'
        error_msg = str(e)
        tokens_used = 0
        _logger.error(f"Orchestrator exception: {e}")

    execution_time = time.time() - start_time
    
    # Log to Odoo Monitorization
    try:
        _logger.info(f"[TELEMETRY] A gravar log: company_id={req.company_id}")
        agent_ids = _odoo_call('ai.agent', 'search', [[('company_id', '=', req.company_id)]], {'limit': 1})
        if agent_ids:
            _odoo_call('ai.monitorization', 'create', [{
                'agent_id': agent_ids[0],
                'company_id': req.company_id,
                'execution_time': round(execution_time, 3),
                'tokens_used': tokens_used,
                'status': status,
                'log_message': error_msg if status == 'error' else result[:500]
            }])
    except Exception as log_e:
        _logger.error(f"Failed to save monitorization log: {log_e}")

    if not result.startswith("ERROR"):
        # Se for uma operação de escrita, limpa todo o cache (cache invalidation)
        msg_lower = req.message.lower()
        is_write = any(k in msg_lower for k in WRITE_KEYWORDS)
        
        if is_write:
            _logger.info("[CACHE] Operação de escrita detetada. Cache limpo.")
            CACHE_DB.clear()
        else:
            set_cache_response(cache_key, result)

    return ChatResponse(response=result)

def _check_odoo():
    try:
        t0 = time.time()
        _odoo_call('res.users', 'search_count', [[]])
        return {'status': 'ok', 'latency_ms': int((time.time() - t0) * 1000)}
    except Exception as e:
        return {'status': 'error', 'detail': type(e).__name__ + ': ' + str(e)[:120]}

def _check_groq_key():
    key = os.getenv('GROQ_API_KEY', '')
    if not key:
        return {'status': 'missing'}
    prefix = key[:8] + '...' if key.startswith('gsk_') else 'unknown'
    return {'status': 'ok', 'configured': True, 'prefix': prefix}

@app.get('/health')
def health():
    odoo = _check_odoo()
    groq = _check_groq_key()
    components = {
        'fastapi': {'status': 'ok'},
        'odoo': odoo,
        'groq_key': groq,
    }
    all_ok = all(c.get('status') == 'ok' for c in components.values())
    return {
        'status': 'ok' if all_ok else 'degraded',
        'version': API_VERSION,
        'components': components,
    }
