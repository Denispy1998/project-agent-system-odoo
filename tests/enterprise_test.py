import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.odoo_tools import setup_agile_project, bulk_move_tasks, list_projects
from tools.odoo_tools import _call, _find_project

def run_tests():
    print("=== TESTES ENTERPRISE (Direto ao Odoo, Zero LLM) ===")
    
    # 1. Teste de Criação e Idempotência
    print("\n1. A testar setup_agile_project...")
    res1 = setup_agile_project.func("Projeto Teste Automatizado")
    print(f"   [Novo] {res1}")
    assert "SUCCESS" in res1 and "CREATED FROM SCRATCH" in res1
    
    res2 = setup_agile_project.func("Projeto Teste Automatizado")
    print(f"   [Duplicado] {res2}")
    assert "SUCCESS" in res2 and "already set up" in res2

    # 2. Teste de Movimentação em Massa
    print("\n2. A testar bulk_move_tasks...")
    proj_id = _find_project("Projeto Teste Automatizado")
    assert proj_id is not None, "Projeto não encontrado na DB"
    
    res3 = bulk_move_tasks.func("Projeto Teste Automatizado", "To Do", "In Progress")
    print(f"   [Movimentação] {res3}")
    assert "SUCCESS" in res3 and "Moved 3 tasks" in res3

    # 3. Teste de Falha (Stage Inválido)
    print("\n3. A testar falha de stage inválido...")
    res4 = bulk_move_tasks.func("Projeto Teste Automatizado", "To Do", "Stage_Fantasma")
    print(f"   [Esperado Falhar] {res4}")
    assert "ERROR" in res4 and "not found in project" in res4

    print("\n>>> TODOS OS TESTES ENTERPRISE PASSARAM! <<<")
    
    # Limpar o projeto criado no teste
    print("A limpar o projeto de teste...")
    _call('project.project', 'unlink', [[proj_id]])
    print("  ✅ Limpo.")

if __name__ == "__main__":
    run_tests()
