from fastapi import FastAPI
from pydantic import BaseModel
import sys
sys.path.append('/home/denispy/project-agent-system')

from agents.orchestrator import run_orchestrator

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
    result = run_orchestrator(
        user_message=req.message,
        user_id=req.user_id,
        is_manager=req.is_manager,
        model_name=req.model_name,
    )
    return ChatResponse(response=result)


@app.get("/health")
def health():
    return {"status": "ok"}
