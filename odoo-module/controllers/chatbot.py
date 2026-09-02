# -*- coding: utf-8 -*-
import sys
import json
import logging
import traceback
import time
import csv
from io import StringIO
from datetime import datetime
from odoo import http
from odoo.http import request, Response
from functools import lru_cache

# ========== AGENTE ==========
AGENT_PATH = '/home/denispy/project-agent-system'
if AGENT_PATH not in sys.path:
    sys.path.append(AGENT_PATH)

_logger = logging.getLogger(__name__)

try:
    from chat_agent import run_agent
    AGENTE_ATIVO = True
    _logger.info("✅ Agente IA importado com sucesso!")
except Exception as e:
    AGENTE_ATIVO = False
    _logger.error(f"❌ Erro ao importar agente: {e}")

from .dashboard_utils import get_project_stats

# ========== GERAR PDF ==========
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    _logger.warning("⚠️ ReportLab não instalado. Usando relatório em texto.")

def generate_pdf_report(project_id):
    Project = http.request.env['project.project']
    Task = http.request.env['project.task']
    project = Project.browse(project_id)
    if not project.exists():
        return None

    if not REPORTLAB_AVAILABLE:
        tasks = Task.search([('project_id', '=', project.id), ('name', '!=', False), ('name', '!=', '')])
        lines = [f"Relatório do Projeto: {project.name}", "="*40, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}"]
        lines.append(f"Descrição: {project.description or 'Sem descrição'}")
        lines.append(f"\nTarefas ({len(tasks)}):")
        for t in tasks:
            assignee_obj = getattr(t, 'user_id', None) or getattr(t, 'create_uid', None)
            assignee = assignee_obj.name if assignee_obj else "Não atribuído"
            lines.append(f"  - {t.name} (Atribuída a: {assignee})")
        no_stage = Task.search_count([('project_id', '=', project.id), ('stage_id', '=', False), ('name', '!=', False), ('name', '!=', '')])
        total = len(tasks)
        risk = (no_stage / total * 100) if total else 0
        lines.append(f"\nAnálise de Riscos:")
        lines.append(f"  Tarefas sem stage: {no_stage} ({risk:.1f}%)")
        lines.append("  Recomendação: " + ("Priorize a definição de stages." if risk > 50 else "Projeto bem organizado."))
        return "\n".join(lines).encode('utf-8')

    from io import BytesIO
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 2*cm, f"Relatório do Projeto: {project.name}")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 3*cm, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawString(2*cm, height - 3.8*cm, f"Descrição: {project.description or 'Sem descrição'}")

    tasks = Task.search([('project_id', '=', project.id), ('name', '!=', False), ('name', '!=', '')])
    y = height - 5*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, f"Tarefas ({len(tasks)})")
    y -= 0.8*cm
    c.setFont("Helvetica", 10)
    for t in tasks[:20]:
        assignee_obj = getattr(t, 'user_id', None) or getattr(t, 'create_uid', None)
        assignee = assignee_obj.name if assignee_obj else "Não atribuído"
        c.drawString(2*cm, y, f"- {t.name} (Atribuída a: {assignee})")
        y -= 0.6*cm
        if y < 2*cm:
            c.showPage()
            y = height - 2*cm

    y -= 1*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Análise de Riscos")
    y -= 0.8*cm
    c.setFont("Helvetica", 10)
    no_stage = Task.search_count([('project_id', '=', project.id), ('stage_id', '=', False), ('name', '!=', False), ('name', '!=', '')])
    total = len(tasks)
    risk = (no_stage / total * 100) if total else 0
    c.drawString(2*cm, y, f"Tarefas sem stage: {no_stage} ({risk:.1f}%)")
    y -= 0.6*cm
    if risk > 50:
        c.setFillColor(colors.red)
        c.drawString(2*cm, y, "Recomendação: Priorize a definição de stages para todas as tarefas.")
    else:
        c.setFillColor(colors.green)
        c.drawString(2*cm, y, "Recomendação: Projeto bem organizado. Continue a monitorizar.")
    c.setFillColor(colors.black)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ========== CACHE DE PERMISSÕES ==========
@lru_cache(maxsize=128)
def _is_user_manager(user_id: int) -> bool:
    try:
        user = request.env['res.users'].browse(user_id)
        if not user.exists():
            return False
        if user.login == 'admin' or user.has_group('base.group_system'):
            return True
        Group = request.env['res.groups']
        manager_group = Group.search([('name', '=', 'Gestor de Projeto')], limit=1)
        if manager_group:
            return manager_group.id in user.groups_id.ids
        return False
    except Exception:
        return False

# ========== CONTROLADOR ==========
class ChatbotController(http.Controller):

    @http.route('/assistente', type='http', auth='user', website=True)
    def pagina_inicial(self):
        stats = get_project_stats()
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Ecossistema IA</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #714B67, #875A7A); border-radius: 16px; color: white; }}
            .header h1 {{ font-size: 2.8rem; margin: 0; letter-spacing: 1px; }}
            .header p {{ font-size: 1.1rem; margin: 5px 0 0; opacity: 0.9; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .stat {{ background: white; border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 4px solid #714B67; }}
            .stat h3 {{ font-size: 2rem; color: #714B67; margin: 0; }}
            .stat p {{ color: #6c757d; margin: 5px 0 0; }}
            .card-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; }}
            .card {{ background: white; border-radius: 24px; padding: 25px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); text-align: center; transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-5px); }}
            .card a {{ text-decoration: none; color: inherit; display: block; }}
            .card i {{ font-size: 2.5rem; color: #714B67; margin-bottom: 10px; }}
            .card h3 {{ color: #1a1a1a; }}
            .card p {{ color: #6c757d; }}
            .footer {{ text-align: center; margin-top: 40px; color: #aaa; font-size: 0.85rem; }}
        </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><i class="fas fa-robot" style="margin-right:10px;"></i>Ecossistema IA</h1>
                    <p>Gestão de Projetos · Planeamento · Execução · Tomada de Decisão</p>
                </div>
                <div class="grid">
                    <div class="stat"><h3>{stats.get('total_projetos', 0)}</h3><p>📁 Projetos</p></div>
                    <div class="stat"><h3>{stats.get('total_tarefas', 0)}</h3><p>✅ Tarefas</p></div>
                    <div class="stat"><h3>{len(stats.get('stats_stages', []))}</h3><p>📊 Stages</p></div>
                    <div class="stat"><h3>{stats.get('avg_lead_time', 0):.1f}</h3><p>⏱️ Lead time</p></div>
                    <div class="stat"><h3>{stats.get('throughput', 0):.1f}</h3><p>📈 Tarefas/dia</p></div>
                </div>
                <div class="card-grid">
                    <div class="card"><a href="/assistente/page"><i class="fas fa-comment-dots"></i><h3>Chat</h3><p>Converse com o agente IA.</p></a></div>
                    <div class="card"><a href="/assistente/dashboard"><i class="fas fa-chart-pie"></i><h3>Dashboard</h3><p>Visão global.</p></a></div>
                    <div class="card"><a href="/assistente/projetos"><i class="fas fa-folder-open"></i><h3>Projetos</h3><p>Sub‑Dashboards.</p></a></div>
                    <div class="card"><a href="/assistente/meus-projetos"><i class="fas fa-user"></i><h3>Meus Projetos</h3><p>Projetos e tarefas.</p></a></div>
                </div>
                <div class="footer">© 2026 · Denilson Santos · Instituto Superior Técnico</div>
            </div>
        </body>
        </html>
        """

    @http.route('/assistente/page', type='http', auth='user', website=True)
    def pagina_chat(self):
        if not AGENTE_ATIVO:
            return "<h1>⚠️ Agente indisponível</h1><a href='/assistente'>Voltar</a>"
        return """
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Assistente IA</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
            body { background: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .chat-container { max-width: 800px; width: 100%; height: 90vh; background: white; border-radius: 24px; box-shadow: 0 12px 40px rgba(0,0,0,0.15); display: flex; flex-direction: column; overflow: hidden; }
            .chat-header { background: linear-gradient(135deg, #714B67, #875A7A); color: white; padding: 18px 24px; display: flex; align-items: center; gap: 12px; }
            .chat-header .back { color: white; text-decoration: none; margin-right: 10px; }
            .chat-header .badge { background: rgba(255,255,255,0.2); padding: 2px 12px; border-radius: 20px; font-size: 0.7rem; margin-left: auto; }
            .chat-messages { flex: 1; padding: 20px 24px; overflow-y: auto; background: #f8f9fc; }
            .message { display: flex; margin-bottom: 16px; }
            .message.user { justify-content: flex-end; }
            .message.bot { justify-content: flex-start; }
            .message .bubble { max-width: 75%; padding: 12px 18px; border-radius: 18px; line-height: 1.5; word-wrap: break-word; }
            .message.user .bubble { background: #714B67; color: white; border-bottom-right-radius: 4px; }
            .message.bot .bubble { background: white; color: #1a1a1a; border: 1px solid #e9ecef; border-bottom-left-radius: 4px; }
            .message .avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 10px; background: #e9ecef; color: #495057; }
            .message.bot .avatar { background: #714B67; color: white; }
            .message.user .avatar { background: #28a745; color: white; order: 1; margin-left: 10px; margin-right: 0; }
            .typing-indicator { display: none; padding: 12px 24px; font-style: italic; color: #6c757d; }
            .chat-input-area { padding: 16px 24px; background: white; border-top: 1px solid #e9ecef; display: flex; gap: 12px; }
            .chat-input-area input { flex: 1; padding: 12px 18px; border: 2px solid #e9ecef; border-radius: 30px; outline: none; }
            .chat-input-area input:focus { border-color: #714B67; }
            .chat-input-area button { background: #714B67; color: white; border: none; padding: 0 24px; border-radius: 30px; cursor: pointer; }
            .help-box {
                margin: 10px 24px 12px 24px;
                background: #f8f9fc;
                border-radius: 12px;
                border: 1px solid #e9ecef;
                overflow: hidden;
                transition: all 0.3s;
            }
            .help-box summary {
                padding: 10px 16px;
                cursor: pointer;
                font-weight: 600;
                color: #714B67;
                display: flex;
                align-items: center;
                gap: 8px;
                user-select: none;
                list-style: none;
            }
            .help-box summary::-webkit-details-marker { display: none; }
            .help-box summary::marker { display: none; }
            .help-box summary .arrow {
                display: inline-block;
                transition: transform 0.2s;
                font-size: 0.9rem;
                margin-left: auto;
            }
            .help-box[open] summary .arrow {
                transform: rotate(90deg);
            }
            .help-box summary:hover { background: #f0f0f0; }
            .help-box summary i { font-size: 1.2rem; }
            .help-content {
                padding: 0 16px 16px 16px;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px 16px;
            }
            .help-content .cmd {
                background: white;
                padding: 6px 12px;
                border-radius: 20px;
                border: 1px solid #dee2e6;
                font-size: 0.85rem;
                color: #1a1a1a;
                display: inline-block;
            }
            .help-content .cmd i { margin-right: 6px; color: #714B67; }
            .help-content .cmd .highlight { color: #714B67; font-weight: 600; }
            .help-content .desc {
                font-size: 0.8rem;
                color: #6c757d;
                grid-column: 1 / -1;
                margin-top: 4px;
            }
            .feedback-link {
                text-align: center;
                font-size: 0.8rem;
                color: #888;
                cursor: pointer;
                padding: 8px 0 12px 0;
                margin-top: 4px;
                border-top: 1px solid #f0f0f0;
            }
            .feedback-link:hover { color: #714B67; }
            @media (max-width: 600px) { .help-content { grid-template-columns: 1fr; } }
        </style>
        </head>
        <body>
            <div class="chat-container">
                <div class="chat-header">
                    <a href="/assistente" class="back"><i class="fas fa-arrow-left"></i></a>
                    <i class="fas fa-robot"></i>
                    <h2>Assistente IA</h2>
                    <span class="badge"><i class="fas fa-circle" style="color:#28a745;"></i> Online</span>
                </div>

                <details class="help-box" id="helpBox">
                    <summary>
                        <i class="fas fa-lightbulb"></i> Como usar? Clique para ver exemplos
                        <span class="arrow">▸</span>
                    </summary>
                    <div class="help-content">
                        <span class="cmd"><i class="fas fa-list"></i> <span class="highlight">1. Lista os projetos existentes</span></span>
                        <span class="cmd"><i class="fas fa-plus-circle"></i> <span class="highlight">2. Cria o projeto "Nome"</span> com tarefas A, B</span>
                        <span class="cmd"><i class="fas fa-tasks"></i> <span class="highlight">3. Adiciona a tarefa "D"</span> ao projeto "Nome"</span>
                        <span class="cmd"><i class="fas fa-tasks"></i> <span class="highlight">4. Lista as tarefas</span> do projeto "Nome"</span>
                        <span class="cmd"><i class="fas fa-layer-group"></i> <span class="highlight">5. Lista os stages</span> do projeto "Nome"</span>
                        <span class="cmd"><i class="fas fa-edit"></i> <span class="highlight">6. Cria o stage "REVIEW"</span> com sequência 15 para o projeto "Nome"</span>
                        <span class="cmd"><i class="fas fa-arrow-right"></i> <span class="highlight">7. Move todas as tarefas</span> do projeto "Nome" para o stage "REVIEW"</span>
                        <span class="cmd"><i class="fas fa-arrow-right"></i> <span class="highlight">8. Move a tarefa "A"</span> do projeto "Nome" para o stage "FASE_2"</span>
                        <span class="cmd"><i class="fas fa-trash-alt"></i> <span class="highlight">9. Elimina a tarefa "B"</span> do projeto "Nome"</span>
                        <span class="cmd"><i class="fas fa-trash-alt"></i> <span class="highlight">10. Elimina o stage "REVIEW"</span> do projeto "Nome"</span>
                        <span class="cmd"><i class="fas fa-trash-alt"></i> <span class="highlight">11. Elimina o projeto "Nome"</span></span>
                        <span class="cmd"><i class="fas fa-chart-line"></i> <span class="highlight">12. Analisa os riscos</span> do projeto "Nome"</span>
                        <span class="cmd"><i class="fas fa-sort-amount-up"></i> <span class="highlight">13. Prioriza as tarefas</span> do projeto "Nome"</span>
                        <span class="cmd"><i class="fas fa-info-circle"></i> <span class="highlight">14. Dá-me um resumo</span> do projeto "Nome"</span>
                   <div class="desc"><i class="fas fa-info-circle" style="color:#714B67;"></i> Podes escrever em linguagem natural. O agente entende variações como "mostra", "exibe", "ver", "cria", "move", "analisa", "transfere", "apaga", etc.</div>
                 </div> 
                </details>

                <div id="chatMessages" class="chat-messages">
                    <div class="message bot">
                        <div class="avatar"><i class="fas fa-robot"></i></div>
                        <div class="bubble">Olá! Sou o assistente IA. Pergunta-me sobre projetos, tarefas, riscos ou prioridades.</div>
                    </div>
                </div>
                <div id="typingIndicator" class="typing-indicator">🤔 A processar...</div>

                <div class="chat-input-area">
                    <input type="text" id="userInput" placeholder="Escreve..." onkeypress="if(event.key==='Enter') sendMessage()">
                    <button id="sendBtn" onclick="sendMessage()"><i class="fas fa-paper-plane"></i></button>
                </div>

                <div class="feedback-link" onclick="feedback()">💬 Avaliar (0-10)</div>
            </div>
            <script>
                const chatMessages = document.getElementById('chatMessages');
                const userInput = document.getElementById('userInput');
                const sendBtn = document.getElementById('sendBtn');
                const typing = document.getElementById('typingIndicator');

                function addMessage(text, isUser) {
                    const div = document.createElement('div');
                    div.className = `message ${isUser ? 'user' : 'bot'}`;
                    const avatar = document.createElement('div');
                    avatar.className = 'avatar';
                    avatar.innerHTML = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
                    const bubble = document.createElement('div');
                    bubble.className = 'bubble';
                    bubble.innerHTML = text.replace(/\\n/g, '<br>');
                    div.appendChild(avatar);
                    div.appendChild(bubble);
                    chatMessages.appendChild(div);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }

                function sendMessage(msg) {
                    const text = msg || userInput.value.trim();
                    if (!text) return;
                    userInput.value = '';
                    addMessage(text, true);
                    sendBtn.disabled = true;
                    typing.style.display = 'block';
                    fetch('/assistente/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mensagem: text })
                    })
                    .then(res => res.json())
                    .then(data => {
                        typing.style.display = 'none';
                        sendBtn.disabled = false;
                        if (data.erro) addMessage('❌ ' + data.erro, false);
                        else addMessage(data.resposta || '⚠️ Resposta vazia', false);
                    })
                    .catch(err => {
                        typing.style.display = 'none';
                        sendBtn.disabled = false;
                        addMessage('❌ Erro: ' + err.message, false);
                    });
                }

                function feedback() {
                    const nota = prompt("De 0 a 10, como avalia?");
                    if (nota !== null) {
                        fetch('/assistente/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nota: nota }) })
                        .then(() => alert('Obrigado!'))
                        .catch(() => alert('Erro.'));
                    }
                }
                userInput.focus();
            </script>
        </body>
        </html>
        """

    @http.route('/assistente/chat', type='http', auth='user', methods=['POST'], csrf=False)
    def chat_endpoint(self):
        if not AGENTE_ATIVO:
            return Response(json.dumps({'erro': 'Agente indisponível'}), content_type='application/json', status=503)
        try:
            data = json.loads(request.httprequest.data)
            pergunta = data.get('mensagem', '').strip()
            if not pergunta:
                return Response(json.dumps({'erro': 'Mensagem vazia'}), status=400)

            _logger.info(f"📩 Mensagem recebida: {pergunta}")

            user = request.env.user
            user_id = user.id
            is_manager = _is_user_manager(user_id)

            _logger.info(f"👤 Utilizador {user.login} – is_manager: {is_manager}")

            inicio = time.time()
            resposta = run_agent(pergunta, user_id, is_manager)
            fim = time.time()
            _logger.info(f"⏱️ Resposta em {fim - inicio:.3f}s")
            return Response(json.dumps({'resposta': resposta or 'Sem resposta'}), content_type='application/json')
        except Exception as e:
            _logger.error(traceback.format_exc())
            return Response(json.dumps({'erro': str(e)}), status=500)

    @http.route('/assistente/feedback', type='http', auth='user', methods=['POST'], csrf=False)
    def feedback_endpoint(self):
        try:
            data = json.loads(request.httprequest.data)
            nota = data.get('nota')
            if nota is None:
                return Response(json.dumps({'erro': 'Nota não fornecida'}), status=400)
            _logger.info(f"📝 Feedback: {nota}/10")
            return Response(json.dumps({'status': 'ok'}), content_type='application/json')
        except Exception as e:
            return Response(json.dumps({'erro': str(e)}), status=500)

    @http.route('/assistente/dashboard', type='http', auth='user', website=True)
    def dashboard_geral(self):
        stats = get_project_stats()
        import json
        stage_labels = json.dumps([s['nome'] for s in stats.get('stats_stages', [])])
        stage_data = json.dumps([s['count'] for s in stats.get('stats_stages', [])])
        user_labels = json.dumps([u['nome'] for u in stats.get('user_stats', [])])
        user_data = json.dumps([u['count'] for u in stats.get('user_stats', [])])
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Dashboard Geral</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .card {{ background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; overflow: auto; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin-bottom: 20px; }}
            .stat {{ text-align: center; padding: 20px; background: #f8f9fc; border-radius: 12px; border-left: 4px solid #714B67; }}
            .stat h3 {{ font-size: 2rem; margin: 0; color: #714B67; }}
            .stat p {{ margin: 5px 0 0; color: #6c757d; }}
            .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
            .chart-wrapper {{ display: flex; flex-direction: column; align-items: center; background: #f8f9fc; border-radius: 12px; padding: 15px; }}
            .chart-wrapper h3 {{ margin: 5px 0 10px; font-size: 1rem; color: #1a1a1a; }}
            .chart-box {{ background: white; border-radius: 8px; padding: 10px; height: 200px; width: 100%; overflow: hidden; position: relative; }}
            .chart-box canvas {{ display: block; width: 100% !important; height: 100% !important; max-width: 100%; max-height: 100%; }}
            .list-item {{ padding: 8px 0; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }}
            .badge {{ background: #714B67; color: white; padding: 2px 12px; border-radius: 20px; font-size: 0.8rem; }}
            .back-link {{ display: inline-block; margin: 20px 0; color: #714B67; text-decoration: none; font-weight: bold; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: #714B67; color: white; border-radius: 30px; text-decoration: none; margin-top: 10px; }}
        </style>
        </head>
        <body>
        <div class="container">
            <a href="/assistente" class="back-link"><i class="fas fa-arrow-left"></i> Voltar</a>
            <h1><i class="fas fa-chart-pie" style="color:#714B67;"></i> Dashboard Geral</h1>
            <div class="grid">
                <div class="stat"><h3>{stats.get('total_projetos', 0)}</h3><p>📁 Projetos</p></div>
                <div class="stat"><h3>{stats.get('total_tarefas', 0)}</h3><p>✅ Tarefas</p></div>
                <div class="stat"><h3>{len(stats.get('stats_stages', []))}</h3><p>📊 Stages</p></div>
                <div class="stat"><h3>{stats.get('avg_lead_time', 0):.1f}</h3><p>⏱️ Lead time</p></div>
                <div class="stat"><h3>{stats.get('throughput', 0):.1f}</h3><p>📈 Tarefas/dia</p></div>
            </div>
            <div class="card charts-grid">
                <div class="chart-wrapper">
                    <h3>Tarefas por Stage</h3>
                    <div class="chart-box">
                        <canvas id="stageChart"></canvas>
                    </div>
                </div>
                <div class="chart-wrapper">
                    <h3>Tarefas por Criador</h3>
                    <div class="chart-box">
                        <canvas id="userChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="card">
                <h2>Detalhe por Stage</h2>
                {''.join([f'<div class="list-item"><span>{s["nome"]}</span><span class="badge">{s["count"]}</span></div>' for s in stats.get('stats_stages', [])])}
                {('<p>Nenhuma tarefa</p>' if not stats.get('stats_stages') else '')}
            </div>
            <div class="card">
                <h2>Detalhe por Criador</h2>
                {''.join([f'<div class="list-item"><span>{u["nome"]}</span><span class="badge">{u["count"]}</span></div>' for u in stats.get('user_stats', [])])}
                {('<p>Nenhuma tarefa</p>' if not stats.get('user_stats') else '')}
            </div>
            <a href="/assistente" class="btn"><i class="fas fa-home"></i> Página Inicial</a>
        </div>
        <script>
            new Chart(document.getElementById('stageChart'), {{
                type: 'pie',
                data: {{ labels: {stage_labels}, datasets: [{{ data: {stage_data}, backgroundColor: ['#714B67','#875A7A','#A88B9E','#C4A8B8','#E5D0D0','#F0E0E0'] }}] }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
            }});
            new Chart(document.getElementById('userChart'), {{
                type: 'bar',
                data: {{ labels: {user_labels}, datasets: [{{ label: 'Tarefas', data: {user_data}, backgroundColor: '#714B67' }}] }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
            }});
        </script>
        </body>
        </html>
        """

    @http.route('/assistente/projetos', type='http', auth='user', website=True)
    def lista_projetos(self):
        projetos = http.request.env['project.project'].search([])
        html = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Projetos</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; }
            .project-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            .project-item { background: #f8f9fc; border-radius: 12px; padding: 15px; text-align: center; }
            .project-item a { text-decoration: none; color: #714B67; font-weight: bold; display: block; }
            .back-link { display: inline-block; margin: 20px 0; color: #714B67; text-decoration: none; font-weight: bold; }
            .btn { display: inline-block; padding: 12px 24px; background: #714B67; color: white; border-radius: 30px; text-decoration: none; margin-top: 10px; }
        </style>
        </head>
        <body>
            <div class="container">
                <a href="/assistente" class="back-link"><i class="fas fa-arrow-left"></i> Voltar</a>
                <h1><i class="fas fa-folder-open" style="color:#714B67;"></i> Projetos</h1>
                <div class="card">
                    <div class="project-grid">
        """
        if not projetos:
            html += '<p>Nenhum projeto encontrado.</p>'
        else:
            for p in projetos:
                html += f'<div class="project-item"><a href="/assistente/projeto/{p.id}">📁 {p.name}</a></div>'
        html += """
                    </div>
                </div>
                <a href="/assistente" class="btn"><i class="fas fa-home"></i> Página Inicial</a>
            </div>
        </body>
        </html>
        """
        return html

    @http.route('/assistente/projeto/<int:projeto_id>', type='http', auth='user', website=True)
    def dashboard_projeto(self, projeto_id):
        stats = get_project_stats(projeto_id)
        if stats is None:
            return "<h1>Projeto não encontrado</h1><a href='/assistente/dashboard'>Voltar</a>"
        import json
        project_name = stats.get('project_name', 'Projeto')
        tasks = stats.get('task_list', [])
        task_rows = ''.join([f'<tr><td>{t["name"]}</td><td>{t["stage"]}</td><td>{t["assignee"]}</td><td>{t["create_date"]}</td></tr>' for t in tasks])
        stage_labels = json.dumps([s['nome'] for s in stats.get('stats_stages', [])])
        stage_data = json.dumps([s['count'] for s in stats.get('stats_stages', [])])
        user_labels = json.dumps([u['nome'] for u in stats.get('user_stats', [])])
        user_data = json.dumps([u['count'] for u in stats.get('user_stats', [])])
        dates = json.dumps(stats.get('burndown_dates', []))
        counts = json.dumps(stats.get('burndown_counts', []))
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>📊 Sub‑Dashboard - {project_name}</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .card {{ background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; overflow: auto; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin-bottom: 20px; }}
                .stat {{ text-align: center; padding: 20px; background: #f8f9fc; border-radius: 12px; border-left: 4px solid #714B67; }}
                .stat h3 {{ font-size: 2rem; margin: 0; color: #714B67; }}
                .stat p {{ margin: 5px 0 0; color: #6c757d; }}
                .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
                .chart-wrapper {{ display: flex; flex-direction: column; align-items: center; background: #f8f9fc; border-radius: 12px; padding: 15px; }}
                .chart-wrapper h3 {{ margin: 5px 0 10px; font-size: 1rem; color: #1a1a1a; }}
                .chart-box {{ background: white; border-radius: 8px; padding: 10px; height: 200px; width: 100%; overflow: hidden; position: relative; }}
                .chart-box canvas {{ display: block; width: 100% !important; height: 100% !important; max-width: 100%; max-height: 100%; }}
                .list-item {{ padding: 8px 0; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }}
                .badge {{ background: #714B67; color: white; padding: 2px 12px; border-radius: 20px; font-size: 0.8rem; }}
                .back-link {{ display: inline-block; margin: 20px 0; color: #714B67; text-decoration: none; font-weight: bold; }}
                .task-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                .task-table th, .task-table td {{ padding: 8px; border-bottom: 1px solid #eee; text-align: left; }}
                .task-table th {{ background: #f8f9fc; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #714B67; color: white; border-radius: 30px; text-decoration: none; margin-top: 10px; }}
                .btn-group {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px; }}
                .btn-group .btn {{ margin: 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="javascript:history.back()" class="back-link"><i class="fas fa-arrow-left"></i> Voltar</a>
                <h1><i class="fas fa-folder-open" style="color:#714B67;"></i> Projeto: {project_name}</h1>
                <div class="grid">
                    <div class="stat"><h3>1</h3><p>📁 Projeto</p></div>
                    <div class="stat"><h3>{stats.get('total_tarefas', 0)}</h3><p>✅ Tarefas</p></div>
                    <div class="stat"><h3>{len(stats.get('stats_stages', []))}</h3><p>📊 Stages</p></div>
                    <div class="stat"><h3>{len(stats.get('user_stats', []))}</h3><p>👥 Colaboradores</p></div>
                </div>
                <div class="card charts-grid">
                    <div class="chart-wrapper">
                        <h3>Tarefas por Stage</h3>
                        <div class="chart-box">
                            <canvas id="stageChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-wrapper">
                        <h3>Tarefas por Criador</h3>
                        <div class="chart-box">
                            <canvas id="userChart"></canvas>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <h2>Evolução (últimos 30 dias)</h2>
                    <div style="height:200px; overflow:hidden; position:relative;">
                        <canvas id="burndownChart" style="width:100%; height:100%;"></canvas>
                    </div>
                </div>
                <div class="card">
                    <h2>Detalhe por Stage</h2>
                    {''.join([f'<div class="list-item"><span>{s["nome"]}</span><span class="badge">{s["count"]}</span></div>' for s in stats.get('stats_stages', [])])}
                    {('<p>Nenhuma tarefa</p>' if not stats.get('stats_stages') else '')}
                </div>
                <div class="card">
                    <h2>Tarefas</h2>
                    {f'<table class="task-table"><thead><tr><th>Tarefa</th><th>Stage</th><th>Atribuída a</th><th>Criada em</th></tr></thead><tbody>{task_rows}</tbody></table>' if tasks else '<p>Nenhuma tarefa.</p>'}
                </div>
                <div class="btn-group">
                    <a href="/assistente/relatorio/{projeto_id}" class="btn"><i class="fas fa-file-pdf"></i> Gerar Relatório PDF</a>
                    <a href="/assistente/exportar/{projeto_id}" class="btn" style="background:#28a745;"><i class="fas fa-file-csv"></i> Exportar CSV</a>
                    <a href="/assistente" class="btn" style="background:#6c757d;"><i class="fas fa-home"></i> Página Inicial</a>
                </div>
            </div>
            <script>
                new Chart(document.getElementById('stageChart'), {{
                    type: 'pie',
                    data: {{ labels: {stage_labels}, datasets: [{{ data: {stage_data}, backgroundColor: ['#714B67','#875A7A','#A88B9E','#C4A8B8','#E5D0D0','#F0E0E0'] }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
                }});
                new Chart(document.getElementById('userChart'), {{
                    type: 'bar',
                    data: {{ labels: {user_labels}, datasets: [{{ label: 'Tarefas', data: {user_data}, backgroundColor: '#714B67' }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
                }});
                new Chart(document.getElementById('burndownChart'), {{
                    type: 'line',
                    data: {{ labels: {dates}, datasets: [{{ label: 'Tarefas criadas', data: {counts}, borderColor: '#714B67', fill: false }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false }}
                }});
            </script>
        </body>
        </html>
        """

    @http.route('/assistente/relatorio/<int:projeto_id>', type='http', auth='user')
    def relatorio_pdf(self, projeto_id):
        try:
            pdf_data = generate_pdf_report(projeto_id)
            if pdf_data is None:
                return Response("Projeto não encontrado", status=404)
            content_type = 'application/pdf' if REPORTLAB_AVAILABLE else 'text/plain'
            extension = 'pdf' if REPORTLAB_AVAILABLE else 'txt'
            return Response(
                pdf_data,
                headers=[
                    ('Content-Type', content_type),
                    ('Content-Disposition', f'attachment; filename=relatorio_projeto_{projeto_id}.{extension}'),
                ],
                status=200,
            )
        except Exception as e:
            _logger.error(f"Erro ao gerar relatório: {e}")
            return Response(f"Erro ao gerar relatório: {str(e)}", status=500)

    @http.route('/assistente/exportar/<int:projeto_id>', type='http', auth='user')
    def exportar_csv(self, projeto_id):
        try:
            Task = http.request.env['project.task']
            tasks = Task.search([('project_id', '=', projeto_id), ('name', '!=', False), ('name', '!=', '')])
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Tarefa', 'Stage', 'Atribuída a', 'Criada em'])
            for t in tasks:
                stage = 'Sem Stage' if not t.stage_id else t.stage_id.name
                assignee_obj = getattr(t, 'user_id', None) or getattr(t, 'create_uid', None)
                assignee = assignee_obj.name if assignee_obj else 'Não atribuído'
                create_date_str = t.create_date.strftime('%d/%m/%Y') if t.create_date else '-'
                writer.writerow([t.name, stage, assignee, create_date_str])
            return Response(
                output.getvalue(),
                headers=[
                    ('Content-Type', 'text/csv'),
                    ('Content-Disposition', f'attachment; filename=projeto_{projeto_id}.csv'),
                ],
                status=200,
            )
        except Exception as e:
            _logger.error(f"Erro ao exportar CSV: {e}")
            return Response(f"Erro ao exportar CSV: {str(e)}", status=500)

    @http.route('/assistente/meus-projetos', type='http', auth='user', website=True)
    def meus_projetos(self):
        user = http.request.env.user
        projetos = http.request.env['project.project'].search([('create_uid', '=', user.id)])
        tarefas = http.request.env['project.task'].search([('create_uid', '=', user.id)])
        html = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Meus Projetos</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
            .item { background: #f8f9fc; padding: 10px; border-radius: 8px; }
            .back-link { display: inline-block; margin: 20px 0; color: #714B67; text-decoration: none; font-weight: bold; }
            .btn { display: inline-block; padding: 12px 24px; background: #714B67; color: white; border-radius: 30px; text-decoration: none; margin-top: 10px; }
        </style>
        </head>
        <body>
            <div class="container">
                <a href="/assistente" class="back-link"><i class="fas fa-arrow-left"></i> Voltar</a>
                <h1><i class="fas fa-user" style="color:#714B67;"></i> Meus Projetos</h1>
                <div class="card">
                    <h2>Projetos que criei</h2>
                    <div class="grid">
        """
        if not projetos:
            html += '<p>Nenhum projeto criado por si.</p>'
        else:
            for p in projetos:
                html += f'<div class="item"><a href="/assistente/projeto/{p.id}">📁 {p.name}</a></div>'
        html += """
                    </div>
                </div>
                <div class="card">
                    <h2>Tarefas que criei</h2>
                    <ul>
        """
        if not tarefas:
            html += '<li>Nenhuma tarefa criada por si.</li>'
        else:
            for t in tarefas:
                html += f'<li>{t.name} (Projeto: {t.project_id.name})</li>'
        html += """
                    </ul>
                </div>
                <a href="/assistente" class="btn"><i class="fas fa-home"></i> Página Inicial</a>
            </div>
        </body>
        </html>
        """
        return html
