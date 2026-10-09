from fastapi import FastAPI
from pydantic import BaseModel
import sys
sys.path.append('/home/denispy/project-agent-system')

from agents.orchestrator import run_orchestrator
from tools.odoo_tools import verify_user_is_manager

app = FastAPI(title="Project Agent API")


class ChatRequest(BaseModel):
    message: str
    user_id: int = 0
    is_manager: bool = False
    model_name: str = "groq"


class ChatResponse(BaseModel):
    response: str


@app.post("/agent/run", response_model=ChatResponse)
def run_agent(req: ChatRequest):
    # === Server-side permission verification (v2.5) ===
    # Never trust is_manager sent by the client. Query Odoo for the real
    # group membership. If the client claimed True but Odoo says False,
    # the request is downgraded. If the client claimed False, we keep False
    # (never escalate privileges based on client input).
    client_claims_manager = bool(req.is_manager)
    if client_claims_manager and req.user_id:
        server_truth = verify_user_is_manager(req.user_id)
        if client_claims_manager and not server_truth:
            print(f"[PermissionGuard] user_id={req.user_id} claimed "
                  f"is_manager=True but Odoo says otherwise -> downgraded")
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


@app.get("/health")
def health():
    return {"status": "ok"}
