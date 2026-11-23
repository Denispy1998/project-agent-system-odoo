import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from agents_api.main import app

client = TestClient(app)

@patch('agents_api.main._odoo_call')
def test_agent_paused(mock_odoo_call):
    # Simula: user existe, mas NENHUM agente em 'running'
    mock_odoo_call.side_effect = lambda model, method, args, kwargs=None: (
        True if model == 'res.users' else 
        [] if model == 'ai.agent' else 
        None
    )
    payload = {"message": "Hello", "user_id": 1, "company_id": 2}
    response = client.post("/agent/run", json=payload)
    assert response.status_code == 200
    assert "System Paused" in response.json()["response"]

@patch('agents_api.main._odoo_call')
@patch('agents_api.main.run_orchestrator')
def test_agent_running(mock_orchestrator, mock_odoo_call):
    # Simula: user existe, e HÁ um agente em 'running'
    mock_odoo_call.side_effect = lambda model, method, args, kwargs=None: (
        True if model == 'res.users' else 
        [1] if model == 'ai.agent' else 
        None
    )
    mock_orchestrator.return_value = ("Success", 0)
    payload = {"message": "Hello", "user_id": 1, "company_id": 2}
    response = client.post("/agent/run", json=payload)
    assert response.status_code == 200
    assert response.json()["response"] == "Success"
