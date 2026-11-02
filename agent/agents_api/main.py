from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
import time
sys.path.append('/home/denispy/project-agent-system')

from agents.orchestrator import run_orchestrator
from tools.odoo_tools import verify_user_is_manager, _call as _odoo_call

app = FastAPI(title='Project Agent API')

API_VERSION = '2.9.3'

# --- SISTEMA DE CACHE ---
CACHE_DB = {}
CACHE_TTL = 300  # 5 minutos em segundos

def get_cache_key(message, user_id, is_manager, system_prompt):
    return f"{user_id}_{is_manager}_{system_prompt}_{message}"

def get_cached_response(key):
    if key in CACHE_DB:
        cached_time, response = CACHE_DB[key]
        if time.time() - cached_time < CACHE_TTL:
            return response
        else:
            del CACHE_DB[key]  # Expirou
    return None

def set_cache_response(key, response):
    # Limpeza periódica simples se o cache ficar muito grande
    if len(CACHE_DB) > 100:
        CACHE_DB.clear()
    CACHE_DB[key] = (time.time(), response)

# -------------------------

class ChatRequest(BaseModel):
    message: str
    user_id: int = 0
    is_manager: bool = False
    model_name: str = 'groq'
    system_prompt: str | None = None


class ChatResponse(BaseModel):
    response: str


@app.post('/agent/run', response_model=ChatResponse)
def run_agent(req: ChatRequest):
    # === Validação de input (v2.9.2) ===
    if not req.message or not req.message.strip():
        return ChatResponse(response="ERROR: Message cannot be empty.")

    if req.user_id:
        user_exists = _odoo_call('res.users', 'search_count', [[('id', '=', req.user_id)]])
        if not user_exists:
            return ChatResponse(response=f"ERROR: User with ID {req.user_id} not found.")

    # === Server-side permission verification ===
    client_claims_manager = bool(req.is_manager)
    if client_claims_manager and req.user_id:
        server_truth = verify_user_is_manager(req.user_id)
        if not server_truth:
            print('[PermissionGuard] user_id=' + str(req.user_id) +
                  ' claimed is_manager=True but Odoo says otherwise -> downgraded')
        effective_is_manager = server_truth
    else:
        effective_is_manager = False

    # === Verificação de Cache ===
    cache_key = get_cache_key(req.message, req.user_id, effective_is_manager, req.system_prompt)
    cached_result = get_cached_response(cache_key)
    
    if cached_result:
        print(f'[CACHE] Hit para: "{req.message}" -> Resposta devolvida do cache.')
        return ChatResponse(response=cached_result)

    # === Execução no Orquestrador ===
    print(f'[ORCHESTRATOR] A processar: "{req.message}"...')
    result = run_orchestrator(
        user_message=req.message,
        user_id=req.user_id,
        is_manager=effective_is_manager,
        model_name=req.model_name,
        system_prompt=req.system_prompt,
    )
    
    # Guardar no cache se não for um erro (para não guardar falhas temporárias)
    if not result.startswith("ERROR"):
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
