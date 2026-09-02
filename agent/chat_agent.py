#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente IA – Versão Final (Corrigida)
- Criação automática de stages ao mover tarefa única
- Domínios corrigidos para Odoo 19
- Logs detalhados
"""

import os
import re
import json
import time
import logging
import xmlrpc.client
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("🚀 AGENTE CARREGADO: versão final com correções")

# ========================== GROQ API ==========================
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("⚠️ Biblioteca 'groq' não instalada. Instale com: pip install groq")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY não definida no ficheiro .env")

# ========================== CONFIGURAÇÕES ==========================
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")
MODEL_NAME = "openai/gpt-oss-20b"
TEMPERATURE = 0.0
TIMEOUT = 30
MAX_RETRIES = 3

# ========================== CONEXÃO ODOO ==========================
_odoo_connection = None

def _get_odoo_connection():
    global _odoo_connection
    if _odoo_connection is not None:
        return _odoo_connection
    for attempt in range(MAX_RETRIES):
        try:
            common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", allow_none=True)
            uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
            if not uid:
                raise ConnectionError("Falha na autenticação Odoo")
            models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", allow_none=True)
            _odoo_connection = (common, uid, models)
            logger.info("✅ Conexão Odoo estabelecida.")
            return _odoo_connection
        except Exception as e:
            logger.warning(f"Tentativa {attempt+1} falhou: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            raise ConnectionError(f"Erro ao conectar ao Odoo após {MAX_RETRIES} tentativas: {e}")

# ========================== FUNÇÕES AUXILIARES ==========================
def _get_project_id_by_name(name: str) -> Optional[int]:
    if not name:
        return None
    name = name.strip('"\'')
    common, uid, models = _get_odoo_connection()
    ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.project', 'search', [[('name', '=', name)]])
    return ids[0] if ids else None

def _get_task_id_by_name(project_id: int, task_name: str) -> Optional[int]:
    common, uid, models = _get_odoo_connection()
    ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'search', [
        [('project_id', '=', project_id), ('name', '=', task_name)]
    ])
    return ids[0] if ids else None

# ========================== FUNÇÃO CORRIGIDA: _get_stage_id ==========================
def _get_stage_id(project_id: int, stage_name: str, create_if_missing: bool = False) -> Optional[int]:
    """
    Obtém o ID de um stage pelo nome no projeto.
    Se `create_if_missing` for True e o stage não existir, cria-o com sequência 10.
    """
    common, uid, models = _get_odoo_connection()
    # Domínio CORRETO: lista de triplas, com o valor do project_id como lista
    domain = [('name', '=', stage_name), ('project_ids', 'in', [project_id])]
    stage_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task.type', 'search', [domain])
    if stage_ids:
        return stage_ids[0]
    if create_if_missing:
        logger.info(f"🔨 Stage '{stage_name}' não encontrado. A criar automaticamente...")
        try:
            new_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task.type', 'create', [{
                'name': stage_name,
                'sequence': 10,
                'project_ids': [(4, project_id, 0)]   # Ligação ao projeto
            }])
            logger.info(f"✅ Stage '{stage_name}' criado com ID {new_id}")
            return new_id
        except Exception as e:
            logger.error(f"Erro ao criar stage '{stage_name}': {e}")
            return None
    return None

# ========================== FERRAMENTAS DO AGENTE ==========================

def listar_projetos(user_id=None, is_manager=False) -> str:
    try:
        common, uid, models = _get_odoo_connection()
        ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.project', 'search', [[]])
        if not ids:
            return "Nenhum projeto encontrado."
        projetos = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.project', 'read',
                                      [ids], {'fields': ['name', 'task_ids']})
        resposta = ["Projetos existentes:"]
        for p in projetos:
            resposta.append(f"  • {p['name']} (ID: {p['id']}) – {len(p['task_ids'])} tarefas")
        return "\n".join(resposta)
    except Exception as e:
        logger.error(f"Erro ao listar projetos: {e}")
        return f"Erro ao listar projetos: {str(e)}"

def criar_projeto(name: str, tasks: str = "", user_id=None, is_manager=False) -> str:
    if not is_manager:
        return "Permissão negada. Apenas gestores de projeto podem criar projetos."
    try:
        name = name.strip('"\'')
        if not name:
            return "ERRO: Nome do projeto não pode estar vazio."
        common, uid, models = _get_odoo_connection()
        if _get_project_id_by_name(name):
            return f"ERRO: Já existe um projeto com o nome '{name}'."
        proj_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.project', 'create', [{
            'name': name,
            'description': ''
        }])
        logger.info(f"Projeto '{name}' criado com ID {proj_id}")
        task_list = [t.strip() for t in tasks.split(',') if t.strip()]
        created = 0
        for tname in task_list:
            try:
                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'create', [{
                    'name': tname,
                    'project_id': proj_id,
                    'stage_id': False,
                    'description': f"Tarefa: {tname}"
                }])
                created += 1
            except Exception as e:
                logger.error(f"Erro ao criar tarefa '{tname}': {e}")
        return f"SUCESSO: Projeto '{name}' (ID {proj_id}) criado com {created} tarefas."
    except Exception as e:
        logger.error(f"ERRO crítico em criar_projeto: {e}")
        return f"ERRO crítico: {str(e)}"

def adicionar_tarefa(project_name: str, task_name: str, user_id=None, is_manager=False) -> str:
    if not is_manager:
        return "Permissão negada. Apenas gestores podem adicionar tarefas."
    try:
        if not project_name or not task_name:
            return "ERRO: É necessário indicar o projeto e a tarefa."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'create', [{
            'name': task_name,
            'project_id': proj_id,
            'stage_id': False,
            'description': task_name
        }])
        return f"SUCESSO: Tarefa '{task_name}' adicionada ao projeto '{project_name}'."
    except Exception as e:
        logger.error(f"Erro em adicionar_tarefa: {e}")
        return f"ERRO: {str(e)}"

def listar_tarefas(project_name: str, user_id=None, is_manager=False) -> str:
    try:
        if not project_name:
            return "ERRO: É necessário indicar o nome do projeto."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        task_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'search',
                                      [[('project_id', '=', proj_id)]])
        if not task_ids:
            return f"Projeto '{project_name}' não tem tarefas."
        tasks = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'read',
                                   [task_ids], {'fields': ['name', 'stage_id']})
        resposta = [f"Tarefas de '{project_name}':"]
        for t in tasks:
            stage = "Sem Stage" if t['stage_id'] is False else (t['stage_id'][1] if t['stage_id'] else "Sem Stage")
            resposta.append(f"  • {t['name']} (Stage: {stage})")
        return "\n".join(resposta)
    except Exception as e:
        return f"ERRO: {str(e)}"

def listar_stages(project_name: str, user_id=None, is_manager=False) -> str:
    try:
        if not project_name:
            return "ERRO: É necessário indicar o nome do projeto."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        stage_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task.type', 'search',
                                      [[('project_ids', 'in', [proj_id])]])
        if not stage_ids:
            return f"Projeto '{project_name}' não tem stages configurados."
        stages = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task.type', 'read',
                                    [stage_ids], {'fields': ['name', 'sequence']})
        resposta = [f"Stages do projeto '{project_name}':"]
        for s in sorted(stages, key=lambda x: x.get('sequence', 0)):
            resposta.append(f"  • {s['name']} (Seq: {s.get('sequence', 0)})")
        return "\n".join(resposta)
    except Exception as e:
        return f"ERRO: {str(e)}"

def criar_stage(project_name: str, stage_name: str, sequence: int = 10, user_id=None, is_manager=False) -> str:
    if not is_manager:
        return "Permissão negada. Apenas gestores podem criar stages."
    try:
        if not project_name or not stage_name:
            return "ERRO: É necessário indicar o projeto e o nome do stage."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        if _get_stage_id(proj_id, stage_name, create_if_missing=False):
            return f"ERRO: Stage '{stage_name}' já existe neste projeto."
        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task.type', 'create', [{
            'name': stage_name,
            'sequence': sequence,
            'project_ids': [(4, proj_id, 0)]
        }])
        return f"SUCESSO: Stage '{stage_name}' criado para '{project_name}'."
    except Exception as e:
        return f"ERRO: {str(e)}"

def mover_tarefas(project_name: str, stage_name: str, user_id=None, is_manager=False) -> str:
    if not is_manager:
        return "Permissão negada. Apenas gestores podem mover tarefas."
    try:
        if not project_name or not stage_name:
            return "ERRO: É necessário indicar o projeto e o stage."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        stage_id = _get_stage_id(proj_id, stage_name, create_if_missing=False)
        if not stage_id:
            return f"ERRO: Stage '{stage_name}' não encontrado no projeto '{project_name}'."
        task_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'search',
                                      [[('project_id', '=', proj_id)]])
        if not task_ids:
            return f"Projeto '{project_name}' não tem tarefas."
        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'write', [task_ids, {'stage_id': stage_id}])
        return f"SUCESSO: {len(task_ids)} tarefas movidas para '{stage_name}'."
    except Exception as e:
        return f"ERRO: {str(e)}"

# ========================== FUNÇÃO CORRIGIDA: mover_tarefa_unica ==========================
def mover_tarefa_unica(project_name: str, task_name: str, stage_name: str, user_id=None, is_manager=False) -> str:
    if not is_manager:
        return "Permissão negada. Apenas gestores podem mover tarefas."
    try:
        if not project_name or not task_name or not stage_name:
            return "ERRO: É necessário indicar o projeto, a tarefa e o stage."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        task_id = _get_task_id_by_name(proj_id, task_name)
        if not task_id:
            return f"ERRO: Tarefa '{task_name}' não encontrada no projeto '{project_name}'."

        # Obtém o stage (cria se não existir)
        stage_id = _get_stage_id(proj_id, stage_name, create_if_missing=True)
        if not stage_id:
            return f"ERRO: Não foi possível criar/obter o stage '{stage_name}'."

        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'write', [[task_id], {'stage_id': stage_id}])
        return f"SUCESSO: Tarefa '{task_name}' movida para '{stage_name}'."

    except xmlrpc.client.Fault as fault:
        logger.error(f"Erro XML-RPC em mover_tarefa_unica: {fault}")
        return f"ERRO (XML-RPC): {fault.faultString}"
    except Exception as e:
        logger.error(f"Erro em mover_tarefa_unica: {e}", exc_info=True)
        return f"ERRO: {str(e)}"

def eliminar_tarefa(project_name: str, task_name: str, user_id=None, is_manager=False) -> str:
    if not is_manager:
        return "Permissão negada. Apenas gestores podem eliminar tarefas."
    try:
        if not project_name or not task_name:
            return "ERRO: É necessário indicar o projeto e a tarefa."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        task_id = _get_task_id_by_name(proj_id, task_name)
        if not task_id:
            return f"ERRO: Tarefa '{task_name}' não encontrada no projeto '{project_name}'."
        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'unlink', [[task_id]])
        return f"SUCESSO: Tarefa '{task_name}' eliminada."
    except Exception as e:
        return f"ERRO: {str(e)}"

def eliminar_stage(project_name: str, stage_name: str, user_id=None, is_manager=False) -> str:
    if not is_manager:
        return "Permissão negada. Apenas gestores podem eliminar stages."
    try:
        if not project_name or not stage_name:
            return "ERRO: É necessário indicar o projeto e o stage."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        stage_id = _get_stage_id(proj_id, stage_name, create_if_missing=False)
        if not stage_id:
            return f"ERRO: Stage '{stage_name}' não encontrado no projeto '{project_name}'."
        task_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'search',
                                      [[('stage_id', '=', stage_id)]])
        if task_ids:
            return f"ERRO: Stage tem {len(task_ids)} tarefas. Movas ou elimine-as primeiro."
        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task.type', 'unlink', [stage_id])
        return f"SUCESSO: Stage '{stage_name}' eliminado."
    except Exception as e:
        return f"ERRO: {str(e)}"

def eliminar_projeto(project_name: str, user_id=None, is_manager=False) -> str:
    if not is_manager:
        return "Permissão negada. Apenas gestores podem eliminar projetos."
    try:
        if not project_name:
            return "ERRO: É necessário indicar o nome do projeto."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        task_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'search',
                                      [[('project_id', '=', proj_id)]])
        if task_ids:
            models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'unlink', [task_ids])
        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.project', 'unlink', [proj_id])
        return f"SUCESSO: Projeto '{project_name}' eliminado."
    except Exception as e:
        return f"ERRO: {str(e)}"

def analisar_riscos(project_name: str, user_id=None, is_manager=False) -> str:
    try:
        if not project_name:
            return "ERRO: É necessário indicar o nome do projeto."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        task_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'search',
                                      [[('project_id', '=', proj_id)]])
        if not task_ids:
            return f"Projeto '{project_name}' não tem tarefas para análise."
        tasks = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'read',
                                   [task_ids], {'fields': ['name', 'stage_id']})
        total = len(tasks)
        no_stage = sum(1 for t in tasks if t['stage_id'] is False)
        risco = (no_stage / total * 100) if total > 0 else 0
        resposta = f"Análise de riscos para o projeto '{project_name}':\n"
        resposta += f"  • Total de tarefas: {total}\n"
        resposta += f"  • Tarefas sem stage definido: {no_stage}\n"
        resposta += f"  • Probabilidade estimada de atraso: {min(risco, 100):.1f}%\n"
        resposta += "  • Recomendação: "
        if risco > 70:
            resposta += "Priorize a definição de stages para todas as tarefas."
        elif risco > 40:
            resposta += "Considere rever o planeamento e atribuir stages às tarefas pendentes."
        else:
            resposta += "O projeto parece estar bem organizado. Continue monitorizando."
        return resposta
    except Exception as e:
        return f"ERRO na análise de riscos: {str(e)}"

def priorizar_tarefas(project_name: str, user_id=None, is_manager=False) -> str:
    try:
        if not project_name:
            return "ERRO: É necessário indicar o nome do projeto."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        task_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'search',
                                      [[('project_id', '=', proj_id)]])
        if not task_ids:
            return f"Projeto '{project_name}' não tem tarefas."
        tasks = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'read',
                                   [task_ids], {'fields': ['name', 'stage_id']})
        sorted_tasks = sorted(tasks, key=lambda t: (0 if t['stage_id'] is False else 1, t['name']))
        resposta = f"Tarefas do projeto '{project_name}' por ordem de prioridade (mais prioritárias primeiro):\n"
        for idx, t in enumerate(sorted_tasks, 1):
            stage = "Sem Stage" if t['stage_id'] is False else (t['stage_id'][1] if t['stage_id'] else "Sem Stage")
            resposta += f"  {idx}. {t['name']} (Stage: {stage})"
            if stage == "Sem Stage":
                resposta += " ⚠️ (prioritária)"
            resposta += "\n"
        return resposta
    except Exception as e:
        return f"ERRO na priorização: {str(e)}"

def resumo_projeto(project_name: str, user_id=None, is_manager=False) -> str:
    try:
        if not project_name:
            return "ERRO: É necessário indicar o nome do projeto."
        common, uid, models = _get_odoo_connection()
        proj_id = _get_project_id_by_name(project_name)
        if not proj_id:
            return f"ERRO: Projeto '{project_name}' não encontrado."
        task_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'search',
                                      [[('project_id', '=', proj_id)]])
        if not task_ids:
            return f"O projeto '{project_name}' não tem tarefas."
        tasks = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'project.task', 'read',
                                   [task_ids], {'fields': ['name', 'stage_id']})
        total = len(tasks)
        no_stage = 0
        stages = {}
        for t in tasks:
            if t['stage_id'] is False:
                no_stage += 1
            else:
                sname = t['stage_id'][1] if t['stage_id'] else "Sem Stage"
                stages[sname] = stages.get(sname, 0) + 1
        resposta = f"📊 RESUMO DO PROJETO: {project_name}\n"
        resposta += f"• Total de tarefas: {total}\n"
        resposta += "• Distribuição por stages:\n"
        for stage, count in stages.items():
            resposta += f"   - {stage}: {count} tarefas\n"
        if no_stage > 0:
            resposta += f"   - ⚠️ Sem Stage: {no_stage} tarefas (prioritárias)\n"
        risco = (no_stage / total * 100) if total > 0 else 0
        resposta += "• Recomendação: "
        if risco > 70:
            resposta += "Priorize a definição de stages para todas as tarefas."
        elif risco > 40:
            resposta += "Considere atribuir stages às tarefas pendentes."
        else:
            resposta += "Projeto bem organizado. Continue monitorizando."
        return resposta
    except Exception as e:
        return f"ERRO ao gerar resumo: {str(e)}"

# ========================== EXTRACTORS ==========================
def _extract_project_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r'(?:projeto|projecto|project)\s+(?:["\']?)([^"\',;]+)(?:["\']?)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'["\']([^"\']+)["\']', text)
    if match:
        return match.group(1).strip()
    return None

def _extract_stage_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r'(?:stage|etapa)\s+(?:["\']?)([^"\',;]+)(?:["\']?)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'["\']([^"\']+)["\']', text)
    if match:
        return match.group(1).strip()
    return None

def _extract_task_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r'(?:tarefa|task)\s+(?:["\']?)([^"\',;]+)(?:["\']?)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'["\']([^"\']+)["\']', text)
    if match:
        return match.group(1).strip()
    return None

def _extract_tasks_from_text(text: str) -> str:
    if not text:
        return ""
    match = re.search(r'(?:tarefas|tasks)\s*:\s*["\']?(.+?)["\']?$', text, re.IGNORECASE)
    if not match:
        match = re.search(r'(?:tarefas|tasks)\s+["\']?(.+?)["\']?$', text, re.IGNORECASE)
    if not match:
        match = re.search(r'(?:tarefas|tasks)\s+(.+)', text, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def _extract_sequence_from_text(text: str) -> int:
    match = re.search(r'sequ[eê]ncia\s+(\d+)', text, re.IGNORECASE)
    return int(match.group(1)) if match else 10

# ========================== FALLBACK DIRETO ==========================
def _fallback_direct(user_message: str, user_id=None, is_manager=False) -> Optional[str]:
    if not user_message:
        return None
    msg = user_message.strip()
    msg_lower = msg.lower()

    if re.search(r'(lista|listar|mostra|exibe|ver)\s+(os\s+)?(projetos|projectos)', msg_lower):
        return listar_projetos(user_id, is_manager)

    if re.search(r'(cria|criar)\s+(um\s+)?(o\s+)?(projeto|projecto)', msg_lower):
        nome = _extract_project_from_text(msg)
        if not nome:
            return "Não consegui identificar o nome do projeto. Exemplo: 'Cria o projeto \"Vendas\" com tarefas A, B'"
        tarefas = _extract_tasks_from_text(msg)
        return criar_projeto(nome, tarefas, user_id, is_manager)

    if re.search(r'(adiciona|adicionar|acrescenta|acrescentar)\s+(a\s+)?(tarefa|task)', msg_lower):
        proj = _extract_project_from_text(msg)
        task = _extract_task_from_text(msg)
        if not proj or not task:
            return "Exemplo: 'Adiciona a tarefa \"T4\" ao projeto \"Vendas\"'"
        return adicionar_tarefa(proj, task, user_id, is_manager)

    if re.search(r'(lista|listar|mostra|exibe|ver)\s+(as\s+)?(tarefas|tasks)', msg_lower):
        proj = _extract_project_from_text(msg)
        if not proj:
            return "Exemplo: 'Lista as tarefas do projeto \"Vendas\"'"
        return listar_tarefas(proj, user_id, is_manager)

    if re.search(r'(lista|listar|mostra|exibe|ver)\s+(os\s+)?(stages|etapas)', msg_lower):
        proj = _extract_project_from_text(msg)
        if not proj:
            return "Exemplo: 'Lista os stages do projeto \"Vendas\"'"
        return listar_stages(proj, user_id, is_manager)

    if re.search(r'(cria|criar)\s+(um\s+)?(o\s+)?(stage|etapa)', msg_lower):
        logger.info(f"🔍 FALLBACK: detectado comando 'cria o stage'")
        proj = _extract_project_from_text(msg)
        stage = _extract_stage_from_text(msg)
        if not proj or not stage:
            parts = re.split(r'\s+', msg)
            for i, w in enumerate(parts):
                if w.lower() in ['stage', 'etapa'] and i+1 < len(parts):
                    stage = parts[i+1].strip('"\'')
                if w.lower() in ['projeto', 'projecto', 'project'] and i+1 < len(parts):
                    proj = parts[i+1].strip('"\'')
        if not proj or not stage:
            return "Exemplo: 'Cria o stage \"REVIEW\" com sequência 15 para o projeto \"Vendas\"'"
        seq = _extract_sequence_from_text(msg)
        return criar_stage(proj, stage, seq, user_id, is_manager)

    if re.search(r'(move|mover|transfere|transferir)\s+(todas\s+)?(as\s+)?(tarefas|tasks)', msg_lower) and ("todas" in msg_lower or "tarefas" in msg_lower):
        proj = _extract_project_from_text(msg)
        stage = _extract_stage_from_text(msg)
        if not stage:
            match = re.search(r'para\s+["\']?([^"\',;]+)["\']?', msg, re.IGNORECASE)
            if match:
                stage = match.group(1).strip()
        if not proj or not stage:
            return "Exemplo: 'Move todas as tarefas do projeto \"Vendas\" para o stage \"REVIEW\"'"
        return mover_tarefas(proj, stage, user_id, is_manager)

    # ========== MOVER UMA TAREFA (COM CRIAÇÃO AUTOMÁTICA) ==========
    if re.search(r'(move|mover|transfere|transferir)\s+(a\s+)?(tarefa|task)', msg_lower) and "todas" not in msg_lower:
        proj = _extract_project_from_text(msg)
        task = _extract_task_from_text(msg)
        stage = _extract_stage_from_text(msg)
        if not stage:
            match = re.search(r'para\s+["\']?([^"\',;]+)["\']?', msg, re.IGNORECASE)
            if match:
                stage = match.group(1).strip()
        if not proj or not task or not stage:
            return "Exemplo: 'Move a tarefa \"A\" do projeto \"Vendas\" para o stage \"REVIEW\"'"
        return mover_tarefa_unica(proj, task, stage, user_id, is_manager)

    if re.search(r'(elimina|eliminar|apaga|apagar)\s+(a\s+)?(tarefa|task)', msg_lower):
        proj = _extract_project_from_text(msg)
        task = _extract_task_from_text(msg)
        if not proj or not task:
            return "Exemplo: 'Elimina a tarefa \"T1\" do projeto \"Vendas\"'"
        return eliminar_tarefa(proj, task, user_id, is_manager)

    if re.search(r'(elimina|eliminar|apaga|apagar)\s+(o\s+)?(stage|etapa)', msg_lower):
        proj = _extract_project_from_text(msg)
        stage = _extract_stage_from_text(msg)
        if not proj or not stage:
            return "Exemplo: 'Elimina o stage \"REVIEW\" do projeto \"Vendas\"'"
        return eliminar_stage(proj, stage, user_id, is_manager)

    if re.search(r'(elimina|eliminar|apaga|apagar)\s+(o\s+)?(projeto|projecto)', msg_lower):
        proj = _extract_project_from_text(msg)
        if not proj:
            return "Exemplo: 'Elimina o projeto \"Vendas\"'"
        return eliminar_projeto(proj, user_id, is_manager)

    if re.search(r'(analisa|analisar|analiza|analizar)\s+(os\s+)?(riscos|risks)', msg_lower):
        proj = _extract_project_from_text(msg)
        if not proj:
            return "Exemplo: 'Analisa os riscos do projeto \"Vendas\"'"
        return analisar_riscos(proj, user_id, is_manager)

    if re.search(r'(prioriza|priorizar)\s+(as\s+)?(tarefas|tasks)', msg_lower):
        proj = _extract_project_from_text(msg)
        if not proj:
            return "Exemplo: 'Prioriza as tarefas do projeto \"Vendas\"'"
        return priorizar_tarefas(proj, user_id, is_manager)

    if re.search(r'(resumo|sumário|dá-me um resumo|mostra o resumo)', msg_lower):
        proj = _extract_project_from_text(msg)
        if not proj:
            return "Exemplo: 'Dá-me um resumo do projeto \"Vendas\"'"
        return resumo_projeto(proj, user_id, is_manager)

    return None

# ========================== LLM FALLBACK ==========================
def _classify_with_groq(user_message: str) -> Optional[Dict[str, Any]]:
    if not GROQ_AVAILABLE:
        return None
    try:
        client = Groq(api_key=GROQ_API_KEY)
        prompt = f"""
You are an assistant for Odoo projects. Classify the user request and respond in JSON format with:
- "action": one of ["listar_projetos", "criar_projeto", "adicionar_tarefa", "listar_tarefas", "listar_stages", "criar_stage", "mover_tarefas", "mover_tarefa_unica", "eliminar_tarefa", "eliminar_stage", "eliminar_projeto", "analisar_riscos", "priorizar_tarefas", "resumo_projeto"]
- "params": a dictionary with the required parameters.

Examples:
- "Cria o projeto Teste com tarefas A,B" -> {{"action": "criar_projeto", "params": {{"name": "Teste", "tasks": "A, B"}}}}
- "Adiciona a tarefa X ao projeto Y" -> {{"action": "adicionar_tarefa", "params": {{"project_name": "Y", "task_name": "X"}}}}
- "Dá-me um resumo do projeto Vendas" -> {{"action": "resumo_projeto", "params": {{"project_name": "Vendas"}}}}

User request: {user_message}
"""
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        action = result.get("action")
        params = result.get("params", {})
        if action:
            return {"action": action, "params": params}
        return None
    except Exception as e:
        logger.error(f"Erro ao chamar Groq: {e}")
        return None

def _execute_action(action: str, params: Dict[str, Any], user_id: Optional[int], is_manager: bool) -> str:
    action_map = {
        "listar_projetos": lambda: listar_projetos(user_id, is_manager),
        "criar_projeto": lambda: criar_projeto(params.get("name", ""), params.get("tasks", ""), user_id, is_manager),
        "adicionar_tarefa": lambda: adicionar_tarefa(params.get("project_name", ""), params.get("task_name", ""), user_id, is_manager),
        "listar_tarefas": lambda: listar_tarefas(params.get("project_name", ""), user_id, is_manager),
        "listar_stages": lambda: listar_stages(params.get("project_name", ""), user_id, is_manager),
        "criar_stage": lambda: criar_stage(params.get("project_name", ""), params.get("stage_name", ""), params.get("sequence", 10), user_id, is_manager),
        "mover_tarefas": lambda: mover_tarefas(params.get("project_name", ""), params.get("stage_name", ""), user_id, is_manager),
        "mover_tarefa_unica": lambda: mover_tarefa_unica(params.get("project_name", ""), params.get("task_name", ""), params.get("stage_name", ""), user_id, is_manager),
        "eliminar_tarefa": lambda: eliminar_tarefa(params.get("project_name", ""), params.get("task_name", ""), user_id, is_manager),
        "eliminar_stage": lambda: eliminar_stage(params.get("project_name", ""), params.get("stage_name", ""), user_id, is_manager),
        "eliminar_projeto": lambda: eliminar_projeto(params.get("project_name", ""), user_id, is_manager),
        "analisar_riscos": lambda: analisar_riscos(params.get("project_name", ""), user_id, is_manager),
        "priorizar_tarefas": lambda: priorizar_tarefas(params.get("project_name", ""), user_id, is_manager),
        "resumo_projeto": lambda: resumo_projeto(params.get("project_name", ""), user_id, is_manager),
    }
    func = action_map.get(action)
    if func:
        try:
            return func()
        except Exception as e:
            logger.error(f"Erro ao executar ação '{action}': {e}")
            return f"Erro ao executar ação: {str(e)}"
    return f"Ação '{action}' não reconhecida."

def run_agent(user_message: str, user_id: Optional[int] = None, is_manager: bool = False) -> str:
    logger.info(f"🔄 run_agent chamado com: {user_message[:80]}...")
    if not user_message or len(user_message.strip()) < 2:
        return "Por favor, escreve uma mensagem mais detalhada."

    direct = _fallback_direct(user_message, user_id, is_manager)
    if direct is not None:
        logger.info(f"✅ Fallback direto usado: {direct[:50]}...")
        return direct

    logger.info("⚠️ Fallback direto falhou, usando LLM...")
    if GROQ_AVAILABLE:
        classification = _classify_with_groq(user_message)
        if classification:
            return _execute_action(classification["action"], classification["params"], user_id, is_manager)
        else:
            return "Não entendi o pedido. Tenta reformular com uma das opções sugeridas."
    return "Não entendi o comando. Use: Listar projetos, Criar projeto \"Nome\" com tarefas..., etc."

if __name__ == "__main__":
    print("Agente IA. Escreva 'sair' para terminar.")
    while True:
        msg = input("> ")
        if msg.lower() == "sair":
            break
        print(run_agent(msg))
