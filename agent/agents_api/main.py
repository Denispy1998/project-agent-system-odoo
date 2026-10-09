from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
import time
sys.path.append('/home/denispy/project-agent-system')

from agents.orchestrator import run_orchestrator
from tools.odoo_tools import verify_user_is_manager, _call as _odoo_call

app = FastAPI(title='Project Agent API')

API_VERSION = '2.5.2'


class ChatRequest(BaseModel):
    message: str
    user_id: int = 0
    is_manager: bool = False
    model_name: str = 'groq'


class ChatResponse(BaseModel):
    response: str


@app.post('/agent/run', response_model=ChatResponse)
def run_agent(req: ChatRequest):
    # === Server-side permission verification (v2.5) ===
    client_claims_manager = bool(req.is_manager)
    if client_claims_manager and req.user_id:
        server_truth = verify_user_is_manager(req.user_id)
        if not server_truth:
            print('[PermissionGuard] user_id=' + str(req.user_id) +
                  ' claimed is_manager=True but Odoo says otherwise -> downgraded')
        effective_is_manager = server_truth
    else:
        effective_is_manager = False

    result = run_orchestrator(
        user_message=req.message,
        user_id=req.user_id,
        is_manager=effective_is_manager,
        model_name=req.model_name,
    )
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
