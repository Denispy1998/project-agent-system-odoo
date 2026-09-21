# -*- coding: utf-8 -*-
import json
import logging
import traceback
import time
import csv
from io import StringIO, BytesIO
from datetime import datetime
from odoo import http
from odoo.http import request, Response
from functools import lru_cache
import requests

AGENT_API_URL = "http://127.0.0.1:8001/agent/run"
AGENTE_ATIVO = True

_logger = logging.getLogger(__name__)

from .dashboard_utils import get_project_stats


CHART_COLORS = [
    "#714B67", "#9C6B87", "#B889A1", "#C8A97E", "#8AA89E",
    "#9C8AA5", "#7A5A78", "#C4A5B5", "#A68A9E", "#D4C2CE",
    "#B5A0AC", "#8B7B94",
]


def _chart_colors(n):
    return [CHART_COLORS[i % len(CHART_COLORS)] for i in range(n)]


def call_agent_api(message, user_id, is_manager, model_name="groq", deep_thinking=False):
    try:
        r = requests.post(
            AGENT_API_URL,
            json={"message": message, "user_id": user_id,
                  "is_manager": is_manager, "model_name": model_name,
                  "deep_thinking": bool(deep_thinking)},
            timeout=180,
        )
        r.raise_for_status()
        return r.json().get("response", "No response")
    except requests.exceptions.ConnectionError:
        _logger.error("Agent API not reachable.")
        return "Agent service unavailable. Please try again later."
    except Exception as e:
        _logger.error(f"Agent API error: {e}")
        return f"Agent error: {e}"


@lru_cache(maxsize=128)
def _is_user_manager(user_id):
    try:
        user = request.env['res.users'].browse(user_id)
        if not user.exists():
            return False
        if user.login == 'admin' or user.has_group('base.group_system'):
            return True
        grp = request.env['res.groups'].search([('name', '=', 'Gestor de Projeto')], limit=1)
        if grp and grp.id in user.groups_id.ids:
            return True
        try:
            grp2 = request.env.ref('meu_assistente_ia.group_project_manager', raise_if_not_found=False)
            if grp2 and grp2.id in user.groups_id.ids:
                return True
        except Exception:
            pass
        return False
    except Exception:
        return False


def _get_user_role_label(user):
    if _is_user_manager(user.id):
        return 'Manager'
    return 'Team Member'


SHARED_CSS = """
<style>
    :root {
        --primary: #714B67;
        --primary-dark: #5a3b51;
        --primary-light: #875A7A;
        --bg: #f0f2f5;
        --card: #ffffff;
        --text: #2c2c2c;
        --muted: #6b7280;
        --border: #e5e7eb;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', -apple-system, sans-serif; background: var(--bg); color: var(--text); }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }

    .back-btn {
        position: fixed; top: 20px; left: 20px; z-index: 1000;
        background: var(--card); border: 1px solid var(--border);
        padding: 10px 18px; border-radius: 30px;
        text-decoration: none; color: var(--primary);
        font-weight: 600; font-size: 0.9rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
        display: inline-flex; align-items: center; gap: 8px;
    }
    .back-btn:hover { background: var(--primary); color: white; transform: translateX(-2px); }

    .hero {
        background: linear-gradient(135deg, var(--primary), var(--primary-light));
        border-radius: 20px; padding: 40px 30px;
        color: white; text-align: center; margin-bottom: 30px;
        box-shadow: 0 8px 24px rgba(113, 75, 103, 0.25);
    }
    .hero h1 { font-size: 2.2rem; margin-bottom: 10px; }
    .hero p { font-size: 1.05rem; opacity: 0.9; }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 18px; margin-bottom: 30px;
    }
    .stat-card {
        background: var(--card); border-radius: 16px; padding: 24px 16px;
        text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stat-card:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
    .stat-card h3 { font-size: 2.2rem; color: var(--primary); margin-bottom: 4px; }
    .stat-card p { color: var(--muted); font-size: 0.9rem; }

    .action-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 20px;
    }
    .action-card {
        background: var(--card); border-radius: 20px; padding: 30px 20px;
        text-align: center; text-decoration: none; color: inherit;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        transition: all 0.25s ease; border: 2px solid transparent;
    }
    .action-card:hover {
        transform: translateY(-6px); border-color: var(--primary);
        box-shadow: 0 12px 30px rgba(113,75,103,0.15);
    }
    .action-card i { font-size: 2.8rem; color: var(--primary); margin-bottom: 15px; display: block; }
    .action-card h3 { margin-bottom: 6px; color: var(--text); }
    .action-card p { color: var(--muted); font-size: 0.9rem; }

    .btn {
        display: inline-flex; align-items: center; gap: 8px;
        background: var(--primary); color: white;
        padding: 10px 22px; border-radius: 30px;
        text-decoration: none; font-weight: 600;
        border: none; cursor: pointer; font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    .btn:hover { background: var(--primary-dark); transform: translateY(-2px); }
    .btn-secondary { background: var(--card); color: var(--primary); border: 2px solid var(--primary); }
    .btn-secondary:hover { background: var(--primary); color: white; }

    .chart-card {
        background: var(--card); border-radius: 16px; padding: 24px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06); margin-bottom: 20px;
    }
    .chart-card h3 {
        margin-bottom: 20px; color: var(--primary);
        display: flex; align-items: center; gap: 8px;
    }

    .detail-section {
        background: var(--card); border-radius: 16px; padding: 24px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06); margin-top: 20px;
    }
    .detail-section h3 { color: var(--primary); margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
    .detail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 12px;
    }
    .detail-item {
        padding: 14px 16px; border-radius: 12px;
        background: #f8f9fc; display: flex; justify-content: space-between;
        align-items: center; border-left: 4px solid var(--primary);
    }
    .detail-item .label { font-weight: 600; font-size: 0.88rem; color: var(--text); }
    .detail-item .value {
        background: var(--primary); color: white; padding: 4px 12px;
        border-radius: 20px; font-weight: 700; font-size: 0.85rem;
    }

    .data-table { width: 100%; border-collapse: collapse; }
    .data-table th {
        background: #f8f9fc; padding: 14px 12px;
        text-align: left; font-weight: 600;
        color: var(--muted); font-size: 0.85rem;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .data-table td { padding: 12px; border-bottom: 1px solid var(--border); }
    .data-table tr:hover { background: #fafbfc; }

    .project-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 20px;
    }

    .my-project-list { display: flex; flex-direction: column; gap: 12px; }
    .my-project-row {
        background: var(--card); border-radius: 14px; padding: 20px 24px;
        display: flex; align-items: center; gap: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        text-decoration: none; color: inherit;
        border-left: 5px solid var(--primary);
        transition: all 0.2s ease;
    }
    .my-project-row:hover {
        transform: translateX(4px);
        box-shadow: 0 6px 20px rgba(113,75,103,0.12);
    }
    .my-project-row .icon-box {
        width: 48px; height: 48px; border-radius: 12px;
        background: linear-gradient(135deg, var(--primary), var(--primary-light));
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }
    .my-project-row .icon-box i { color: white; font-size: 1.4rem; }
    .my-project-row .info { flex: 1; }
    .my-project-row .info h3 { font-size: 1.05rem; margin-bottom: 4px; }
    .my-project-row .info p { font-size: 0.85rem; color: var(--muted); }
    .my-project-row .count-badge {
        background: #f8f9fc; color: var(--primary);
        padding: 6px 14px; border-radius: 20px;
        font-weight: 700; font-size: 0.85rem;
        border: 2px solid var(--primary);
    }

    .site-footer {
        text-align: center; padding: 24px 20px 30px 20px;
        color: #9ca3af; font-size: 0.82rem;
        border-top: 1px solid #e5e7eb; margin-top: 30px;
    }
    .site-footer strong { color: #714B67; }
    .site-footer i { color: #714B67; margin-right: 4px; }
</style>
"""


def _page(title, content, back_url="/assistente", back_text="Back"):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{title}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{SHARED_CSS}
</head>
<body>
<a href="{back_url}" class="back-btn"><i class="fas fa-arrow-left"></i> {back_text}</a>
{content}
<footer class="site-footer">
    <i class="fas fa-copyright"></i>
    <strong>Denilson Fragoso Da Silva Santos</strong>
    &nbsp;·&nbsp; Instituto Superior Técnico &nbsp;·&nbsp; 2026
</footer>
</body>
</html>"""


try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def _generate_pdf(projeto_id):
    Project = request.env['project.project']
    Task = request.env['project.task']
    project = Project.browse(projeto_id)
    if not project.exists():
        return None

    if not REPORTLAB_AVAILABLE:
        tasks = Task.search([('project_id', '=', project.id)])
        lines = [f"Project Report: {project.name}", "=" * 40,
                 f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}"]
        for t in tasks:
            lines.append(f"  - {t.name}")
        return "\n".join(lines).encode('utf-8')

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    primary = HexColor("#714B67")
    light = HexColor("#875A7A")

    c.setFillColor(primary)
    c.rect(0, height - 3.5 * cm, width, 3.5 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(2 * cm, height - 2 * cm, f"{project.name}")
    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, height - 2.8 * cm, "AI Project Management Ecosystem — Report")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, height - 4.5 * cm, f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawString(2 * cm, height - 5 * cm, f"Description: {project.description or 'No description'}")

    tasks = Task.search([('project_id', '=', project.id)])
    y = height - 6 * cm
    c.setFillColor(primary)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, f"Tasks ({len(tasks)})")
    y -= 0.8 * cm

    c.setFillColor(light)
    c.rect(2 * cm, y - 0.3 * cm, width - 4 * cm, 0.6 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.2 * cm, y - 0.1 * cm, "Name")
    c.drawString(8 * cm, y - 0.1 * cm, "Stage")
    c.drawString(12 * cm, y - 0.1 * cm, "Assignee")
    c.drawString(16 * cm, y - 0.1 * cm, "Created")
    y -= 0.7 * cm

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    for i, t in enumerate(tasks):
        if y < 3 * cm:
            c.showPage()
            y = height - 2 * cm
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.black)
        if i % 2 == 0:
            c.setFillColor(HexColor("#F8F9FC"))
            c.rect(2 * cm, y - 0.2 * cm, width - 4 * cm, 0.5 * cm, fill=1, stroke=0)
            c.setFillColor(colors.black)
        stage = t.stage_id.name if t.stage_id else "—"
        assignee = t.create_uid.name if t.create_uid else "—"
        created = t.create_date.strftime('%d/%m/%Y') if t.create_date else "—"
        c.drawString(2.2 * cm, y, (t.name or "")[:40])
        c.drawString(8 * cm, y, stage[:20])
        c.drawString(12 * cm, y, assignee[:20])
        c.drawString(16 * cm, y, created)
        y -= 0.5 * cm

    y -= 0.5 * cm
    if y < 4 * cm:
        c.showPage()
        y = height - 2 * cm
    c.setFillColor(primary)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "Risk Analysis")
    y -= 0.8 * cm
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 11)
    total = len(tasks)
    no_stage = sum(1 for t in tasks if not t.stage_id)
    risk = (no_stage / total * 100) if total else 0
    c.drawString(2 * cm, y, f"Total tasks: {total}")
    y -= 0.6 * cm
    c.drawString(2 * cm, y, f"Tasks without stage: {no_stage} ({risk:.1f}%)")
    y -= 0.6 * cm
    if risk > 70:
        c.setFillColor(HexColor("#DC2626"))
        rec = "HIGH RISK — Prioritize stage definition immediately."
    elif risk > 40:
        c.setFillColor(HexColor("#D97706"))
        rec = "MEDIUM RISK — Consider assigning stages."
    else:
        c.setFillColor(HexColor("#059669"))
        rec = "LOW RISK — Project is well organized."
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, rec)

    c.setFillColor(HexColor("#9CA3AF"))
    c.setFont("Helvetica", 8)
    c.drawString(2 * cm, 1 * cm, "Generated by AI Project Management Ecosystem v2.0 — Denilson Fragoso Da Silva Santos (IST-1113142)")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


class ChatbotController(http.Controller):

    # -------------------------------------------------------------------------
    # HOME — Larger cards, tighter layout
    # -------------------------------------------------------------------------
    @http.route('/assistente', type='http', auth='user', website=True)
    def home(self):
        stats = get_project_stats()
        user = request.env.user
        is_manager = _is_user_manager(user.id)
        role_label = "Manager" if is_manager else "Team Member"
        role_color = "#059669" if is_manager else "#D97706"
        role_icon = "fa-user-tie" if is_manager else "fa-user"
        role_desc = ("Full access — create, move, delete projects and tasks"
                     if is_manager
                     else "Read-only access — view projects, tasks, risks and reports")

        content = f"""
        <style>
            .home-hero {{
                background: linear-gradient(135deg, #714B67, #875A7A);
                border-radius: 18px; padding: 30px 28px;
                color: white; text-align: center; margin-bottom: 22px;
                box-shadow: 0 8px 22px rgba(113, 75, 103, 0.25);
            }}
            .home-hero h1 {{ font-size: 2rem; margin-bottom: 6px; }}
            .home-hero p {{ font-size: 1.05rem; opacity: 0.92; }}
            .home-role-pill {{
                display: inline-flex; align-items: center; gap: 10px;
                margin-top: 14px; padding: 8px 22px;
                background: rgba(255,255,255,0.24); border-radius: 30px;
                font-weight: 600; font-size: 0.95rem;
            }}
            .home-access {{
                background: white; border-left: 6px solid {role_color};
                border-radius: 14px; padding: 18px 26px; margin-bottom: 22px;
                display: flex; align-items: center; gap: 16px;
                box-shadow: 0 3px 12px rgba(0,0,0,0.06);
            }}
            .home-access i {{ font-size: 1.7rem; color: {role_color}; }}
            .home-access .acc-title {{ font-weight: 700; font-size: 1.1rem; }}
            .home-access .acc-desc {{ font-size: 0.95rem; color: #6b7280; margin-top: 2px; }}
            .home-stats {{
                display: grid; grid-template-columns: repeat(5, 1fr);
                gap: 16px; margin-bottom: 22px;
            }}
            .home-stat {{
                background: white; border-radius: 16px; padding: 24px 12px;
                text-align: center; box-shadow: 0 3px 12px rgba(0,0,0,0.06);
                transition: transform 0.22s ease, box-shadow 0.22s ease;
            }}
            .home-stat:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 22px rgba(113,75,103,0.12);
            }}
            .home-stat h3 {{ font-size: 2.2rem; color: #714B67; margin: 0 0 6px 0; }}
            .home-stat p {{ color: #6b7280; font-size: 0.9rem; }}
            .home-actions {{
                display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px;
            }}
            .home-action {{
                background: white; border-radius: 20px; padding: 32px 20px;
                text-align: center; text-decoration: none; color: inherit;
                box-shadow: 0 4px 16px rgba(0,0,0,0.07);
                transition: all 0.24s ease; border: 2px solid transparent;
            }}
            .home-action:hover {{
                transform: translateY(-6px); border-color: #714B67;
                box-shadow: 0 14px 30px rgba(113,75,103,0.16);
            }}
            .home-action i {{ font-size: 2.8rem; color: #714B67; margin-bottom: 14px; display: block; }}
            .home-action h3 {{ margin-bottom: 6px; color: #2c2c2c; font-size: 1.15rem; }}
            .home-action p {{ color: #6b7280; font-size: 0.88rem; }}
        </style>

        <div class="container" style="padding-top: 70px; padding-bottom: 10px;">
            <div class="home-hero">
                <h1><i class="fas fa-robot"></i> AI Ecosystem</h1>
                <p>Multi-Agent Project Management · v2.0</p>
                <div class="home-role-pill">
                    <i class="fas {role_icon}"></i>
                    <span>Signed in as <strong>{user.name}</strong> · {role_label}</span>
                </div>
            </div>

            <div class="home-access">
                <i class="fas {role_icon}"></i>
                <div>
                    <div class="acc-title">
                        Access Level: <span style="color: {role_color};">{role_label}</span>
                    </div>
                    <div class="acc-desc">{role_desc}</div>
                </div>
            </div>

            <div class="home-stats">
                <div class="home-stat"><h3>{stats.get('total_projects', 0)}</h3><p>Projects</p></div>
                <div class="home-stat"><h3>{stats.get('total_tasks', 0)}</h3><p>Tasks</p></div>
                <div class="home-stat"><h3>{len(stats.get('stats_stages', []))}</h3><p>Stages</p></div>
                <div class="home-stat"><h3>{stats.get('avg_lead_time', 0):.1f}</h3><p>Lead Time</p></div>
                <div class="home-stat"><h3>{stats.get('throughput', 0):.1f}</h3><p>Tasks/day</p></div>
            </div>

            <div class="home-actions">
                <a href="/assistente/page" class="home-action">
                    <i class="fas fa-comment-dots"></i>
                    <h3>Chat</h3>
                    <p>{'Multi-session with write access' if is_manager else 'Read-only chat'}</p>
                </a>
                <a href="/assistente/dashboard" class="home-action">
                    <i class="fas fa-chart-pie"></i>
                    <h3>Dashboard</h3>
                    <p>Global metrics & charts</p>
                </a>
                <a href="/assistente/projetos" class="home-action">
                    <i class="fas fa-folder-open"></i>
                    <h3>All Projects</h3>
                    <p>Browse every project</p>
                </a>
                <a href="/assistente/meus-projetos" class="home-action">
                    <i class="fas fa-user-tie"></i>
                    <h3>My Workspace</h3>
                    <p>{'Your managed projects' if is_manager else 'Your assigned tasks'}</p>
                </a>
            </div>
        </div>
        """
        return _page("AI Ecosystem", content, back_url="/web", back_text="Odoo Home")

    # -------------------------------------------------------------------------
    # CHAT PAGE
    # -------------------------------------------------------------------------
    @http.route('/assistente/page', type='http', auth='user', website=True)
    def chat_page(self):
        user = request.env.user
        is_manager = _is_user_manager(user.id)
        mode_badge = ("<span style='background:#059669;color:white;padding:4px 12px;"
                      "border-radius:20px;font-size:0.75rem;font-weight:700;'>MANAGER</span>"
                      if is_manager else
                      "<span style='background:#D97706;color:white;padding:4px 12px;"
                      "border-radius:20px;font-size:0.75rem;font-weight:700;'>TEAM MEMBER</span>")

        return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>AI Assistant</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root { --primary: #714B67; --primary-dark: #5a3b51; --primary-light: #875A7A; }
    * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
    body { background: #f0f2f5; display: flex; height: 100vh; overflow: hidden; }

    .sidebar { width: 300px; background: #1f1f1f; color: white; display: flex; flex-direction: column; }
    .sidebar-header { padding: 20px; border-bottom: 1px solid #333; display: flex; align-items: center; gap: 12px; }
    .sidebar-header h3 { font-size: 1.05rem; }
    .session-list { flex: 1; overflow-y: auto; padding: 12px; }
    .session-item {
        padding: 12px 14px; border-radius: 10px; cursor: pointer;
        margin-bottom: 6px; font-size: 0.9rem;
        display: flex; align-items: center; gap: 10px;
        transition: background 0.15s ease;
    }
    .session-item:hover { background: #2f2f2f; }
    .session-item.active { background: var(--primary); }
    .session-item i { font-size: 0.8rem; opacity: 0.7; }
    .session-name { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .new-session {
        margin: 12px; padding: 12px; background: var(--primary); color: white;
        border: none; border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 0.9rem;
        display: flex; align-items: center; justify-content: center; gap: 8px;
        transition: background 0.2s ease;
    }
    .new-session:hover { background: var(--primary-dark); }

    .main { flex: 1; display: flex; flex-direction: column; background: #f8f9fc; }
    .chat-header {
        background: white; padding: 14px 24px;
        display: flex; align-items: center; gap: 14px;
        border-bottom: 1px solid #e9ecef;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .chat-back-btn {
        display: inline-flex; align-items: center; gap: 8px;
        background: #f8f9fc; color: var(--primary);
        padding: 9px 16px; border-radius: 30px;
        text-decoration: none; font-weight: 600; font-size: 0.85rem;
        border: 1px solid #e5e7eb;
        transition: all 0.2s ease; flex-shrink: 0;
    }
    .chat-back-btn:hover { background: var(--primary); color: white; }
    .chat-header i.robot { color: var(--primary); font-size: 1.3rem; }
    .chat-header h2 { font-size: 1.1rem; color: #2c2c2c; flex: 1; }
    .chat-header select {
        padding: 8px 14px; border-radius: 10px;
        border: 1px solid #e5e7eb; background: white;
        font-size: 0.9rem; cursor: pointer; outline: none;
    }
    .chat-header select:focus { border-color: var(--primary); }

    .chat-messages { flex: 1; overflow-y: auto; padding: 30px; display: flex; flex-direction: column; }

    .welcome-container {
        flex: 1; display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        padding: 40px; text-align: center;
    }
    .welcome-container .icon-badge {
        width: 90px; height: 90px; border-radius: 50%;
        background: linear-gradient(135deg, var(--primary), #875A7A);
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 24px; box-shadow: 0 10px 30px rgba(113,75,103,0.3);
    }
    .welcome-container .icon-badge i { font-size: 2.5rem; color: white; }
    .welcome-container h1 { font-size: 1.8rem; color: #2c2c2c; margin-bottom: 12px; }
    .welcome-container p { color: #6b7280; font-size: 1rem; max-width: 500px; margin-bottom: 30px; line-height: 1.6; }
    .welcome-actions { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }
    .welcome-btn {
        padding: 12px 24px; border-radius: 30px;
        border: none; cursor: pointer; font-weight: 600;
        font-size: 0.95rem; display: inline-flex; align-items: center; gap: 8px;
        transition: all 0.2s ease;
    }
    .welcome-btn.primary { background: var(--primary); color: white; box-shadow: 0 4px 12px rgba(113,75,103,0.3); }
    .welcome-btn.primary:hover { background: var(--primary-dark); transform: translateY(-2px); }
    .welcome-btn.secondary { background: white; color: var(--primary); border: 2px solid #e5e7eb; }
    .welcome-btn.secondary:hover { border-color: var(--primary); }
    .welcome-hint {
        margin-top: 40px; padding: 16px 20px;
        background: white; border-radius: 12px;
        border-left: 4px solid var(--primary);
        font-size: 0.88rem; color: #6b7280; max-width: 560px;
    }
    .welcome-hint strong { color: var(--primary); }

    .message { display: flex; margin-bottom: 18px; animation: fadeIn 0.2s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
    .message.user { justify-content: flex-end; }
    .message.bot { justify-content: flex-start; }
    .bubble {
        max-width: 70%; padding: 14px 20px; border-radius: 20px;
        font-size: 0.95rem; line-height: 1.55;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        white-space: pre-wrap; word-wrap: break-word;
    }
    .message.user .bubble {
        background: linear-gradient(135deg, var(--primary), #875A7A);
        color: white; border-bottom-right-radius: 6px;
    }
    .message.bot .bubble {
        background: white; border: 1px solid #e9ecef;
        border-bottom-left-radius: 6px;
    }
    .message.bot .bubble.typing { color: #9ca3af; font-style: italic; }
    .message.bot .bubble.denied {
        background: #fef3c7; border-color: #f59e0b; color: #92400e;
    }

    .input-area {
        padding: 18px 28px; background: white;
        display: flex; gap: 12px; align-items: center;
        border-top: 1px solid #e9ecef;
    }
    .input-area input {
        flex: 1; padding: 14px 22px;
        border: 2px solid #e9ecef; border-radius: 30px;
        outline: none; font-size: 0.95rem;
        transition: border-color 0.2s ease;
    }
    .input-area input:focus { border-color: var(--primary); }
    .input-area input:disabled { background: #f5f5f5; cursor: not-allowed; }
    .input-area button {
        background: var(--primary); color: white;
        border: none; width: 48px; height: 48px;
        border-radius: 50%; cursor: pointer;
        font-size: 1rem; transition: all 0.2s ease;
        display: flex; align-items: center; justify-content: center;
    }
    .input-area button:hover:not(:disabled) { background: var(--primary-dark); transform: scale(1.05); }
    .input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
        .session-item { position: relative; display: flex; align-items: center; gap: 8px; }
        .session-item .session-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .session-item .session-actions { display: none; gap: 6px; padding-left: 6px; }
        .session-item:hover .session-actions { display: flex; }
        .session-item .session-actions i { cursor: pointer; opacity: 0.5; font-size: 0.75rem; transition: opacity 0.15s; }
        .session-item .session-actions i:hover { opacity: 1; color: #fff; }
        .session-item .session-actions .fa-trash:hover { color: #ff6b6b; }
        .deep-toggle { display: flex; align-items: center; gap: 6px; margin-left: 12px; padding: 6px 12px; border-radius: 8px; background: #f4f1f3; color: #714B67; font-size: 0.85rem; cursor: pointer; user-select: none; }
        .deep-toggle input { cursor: pointer; }
        .deep-toggle:hover { background: #ebe4ea; }
</style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <i class="fas fa-comments" style="color: #875A7A;"></i>
            <h3>Chats</h3>
        </div>
        <div class="session-list" id="sessionList"></div>
        <button class="new-session" onclick="createSession()">
            <i class="fas fa-plus"></i> New Chat
        </button>
    </div>

    <div class="main">
        <div class="chat-header">
            <a href="/assistente" class="chat-back-btn">
                <i class="fas fa-arrow-left"></i> Back
            </a>
            <i class="fas fa-robot robot"></i>
            <h2 id="sessionTitle">AI Assistant</h2>
            """ + mode_badge + """
            <label class="deep-toggle" title="Deep thinking: more reasoning steps for complex queries">
                <input type="checkbox" id="deepThinking">
                <i class="fas fa-brain"></i> Deep
            </label>
            <select id="modelSelect" onchange="changeModel()">
                <option value="groq">Groq · Qwen 3.8 27B</option>
                <option value="openai">OpenAI · GPT-4o</option>
                <option value="anthropic">Anthropic · Claude 3.5</option>
            </select>
        </div>

        <div class="chat-messages" id="chatMessages"></div>

        <div class="input-area">
            <input type="text" id="userInput" placeholder="Type your message..." disabled
                   onkeypress="if(event.key==='Enter') sendMessage()">
            <button id="sendBtn" onclick="sendMessage()" disabled>
                <i class="fas fa-paper-plane"></i>
            </button>
        </div>
    </div>

    <script>
        let currentSessionId = null;
        let sessions = [];
        const IS_MANAGER = """ + ("true" if is_manager else "false") + """;

        function renderWelcome() {
            const chat = document.getElementById('chatMessages');
            chat.innerHTML = `
                <div class="welcome-container">
                    <div class="icon-badge"><i class="fas fa-robot"></i></div>
                    <h1>Welcome to AI Assistant</h1>
                    <p>Your multi-agent companion for project management. ${IS_MANAGER ? 'You have full write access — you can create, move, and delete projects and tasks.' : 'You have read-only access — you can list, analyze, and report on projects and tasks.'}</p>
                    <div class="welcome-actions">
                        <button class="welcome-btn primary" onclick="createSession()">
                            <i class="fas fa-plus"></i> Create New Chat
                        </button>
                        <button class="welcome-btn secondary" onclick="alert('Select an existing chat from the sidebar on the left.')">
                            <i class="fas fa-list"></i> Select Existing Chat
                        </button>
                    </div>
                    <div class="welcome-hint">
                        <strong>Tip:</strong> ${IS_MANAGER ? 'Try "list all projects", "create a project called Demo with 3 tasks", or "generate a flowchart".' : 'Try "list all projects", "list all tasks", or "generate a flowchart".'}
                    </div>
                </div>
            `;
            document.getElementById('userInput').disabled = true;
            document.getElementById('sendBtn').disabled = true;
            document.getElementById('userInput').placeholder = "Create or select a chat to start...";
        }

        async function loadSessions() {
            try {
                const res = await fetch('/assistente/sessions');
                sessions = await res.json();
                const list = document.getElementById('sessionList');
                list.innerHTML = '';
                if (!sessions.length) {
                    list.innerHTML = '<div style="color:#666;padding:20px;text-align:center;font-size:0.85rem;">No chats yet</div>';
                    return;
                }
                sessions.forEach(s => {
                    const div = document.createElement('div');
                    div.className = 'session-item' + (s.id === currentSessionId ? ' active' : '');
                    const safeName = (s.name || '').replace(/'/g, "\\'");
                    div.innerHTML = `<i class="fas fa-comment"></i><span class="session-name">${s.name}</span><span class="session-actions"><i class="fas fa-pen" title="Rename" onclick="event.stopPropagation(); renameSession(${s.id}, '${safeName}')"></i><i class="fas fa-trash" title="Delete" onclick="event.stopPropagation(); deleteSession(${s.id}, '${safeName}')"></i></span>`;
                    div.onclick = () => selectSession(s.id);
                    list.appendChild(div);
                });
            } catch (e) { console.error('loadSessions error', e); }
        }

        async function renameSession(id, currentName) {
            const newName = prompt('New session name:', currentName);
            if (!newName || newName === currentName) return;
            try {
                const res = await fetch('/assistente/sessions/' + id + '/rename', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: newName })
                });
                if (!res.ok) { alert('Rename failed (' + res.status + ')'); return; }
                await loadSessions();
                if (currentSessionId === id) {
                    document.getElementById('sessionTitle').textContent = newName;
                }
            } catch (e) { alert('Rename error: ' + e); }
        }

        async function deleteSession(id, currentName) {
            if (!confirm('Delete session "' + currentName + '"? This cannot be undone.')) return;
            try {
                const res = await fetch('/assistente/sessions/' + id + '/delete', { method: 'POST' });
                if (!res.ok) { alert('Delete failed (' + res.status + ')'); return; }
                if (currentSessionId === id) {
                    currentSessionId = null;
                    renderWelcome();
                }
                await loadSessions();
            } catch (e) { alert('Delete error: ' + e); }
        }

        async function createSession() {
            const name = prompt('Session name:', 'New Chat');
            if (!name) return;
            try {
                const res = await fetch('/assistente/sessions/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                if (!res.ok) { alert('Error creating session: ' + res.status); return; }
                const data = await res.json();
                currentSessionId = data.id;
                await loadSessions();
                await selectSession(data.id);
                document.getElementById('userInput').focus();
            } catch (e) { alert('Error: ' + e); }
        }

        async function selectSession(id) {
            currentSessionId = id;
            try {
                const res = await fetch('/assistente/sessions/' + id);
                const data = await res.json();
                document.getElementById('sessionTitle').textContent = data.name;
                document.getElementById('modelSelect').value = data.model_name || 'groq';
                const chat = document.getElementById('chatMessages');
                chat.innerHTML = '';
                if (!data.messages || !data.messages.length) {
                    chat.innerHTML = `
                        <div class="welcome-container">
                            <div class="icon-badge"><i class="fas fa-comments"></i></div>
                            <h1>${data.name}</h1>
                            <p>This conversation is empty. Start by typing a message below.</p>
                            <div class="welcome-hint">
                                <strong>Try:</strong> "list all projects" or "generate a flowchart".
                            </div>
                        </div>
                    `;
                } else {
                    data.messages.forEach(m => addMessage(m.content, m.role === 'user'));
                }
                document.getElementById('userInput').disabled = false;
                document.getElementById('sendBtn').disabled = false;
                document.getElementById('userInput').placeholder = "Type your message...";
                document.getElementById('userInput').focus();
                await loadSessions();
            } catch (e) { console.error('selectSession error', e); }
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;
            if (!currentSessionId) { alert('Please create or select a session first.'); return; }
            input.value = '';
            addMessage(text, true);
            const typing = addTyping();
            document.getElementById('userInput').disabled = true;
            document.getElementById('sendBtn').disabled = true;
            try {
                await fetch('/assistente/sessions/' + currentSessionId + '/messages', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ role: 'user', content: text })
                });
                const deepCb = document.getElementById('deepThinking');
                const deepValue = deepCb ? deepCb.checked : false;
                const res = await fetch('/assistente/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mensagem: text, session_id: currentSessionId, deep_thinking: deepValue })
                });
                const data = await res.json();
                const reply = data.resposta || data.erro || 'No response';
                typing.remove();
                const isDenied = reply.startsWith('DENIED:');
                addMessage(reply, false, isDenied);
                await fetch('/assistente/sessions/' + currentSessionId + '/messages', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ role: 'assistant', content: reply })
                });
            } catch (e) {
                typing.remove();
                addMessage('Error: ' + e, false);
            } finally {
                document.getElementById('userInput').disabled = false;
                document.getElementById('sendBtn').disabled = false;
                document.getElementById('userInput').focus();
            }
        }

        function addMessage(text, isUser, isDenied) {
            const chat = document.getElementById('chatMessages');
            const welcome = chat.querySelector('.welcome-container');
            if (welcome) welcome.remove();
            const div = document.createElement('div');
            div.className = 'message ' + (isUser ? 'user' : 'bot');
            const bubble = document.createElement('div');
            bubble.className = 'bubble' + (isDenied ? ' denied' : '');
            bubble.textContent = text;
            div.appendChild(bubble);
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
            return div;
        }

        function addTyping() {
            const chat = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = 'message bot';
            const deepOn = document.getElementById('deepThinking');
            const label = (deepOn && deepOn.checked) ? 'Thinking deeply…' : 'Thinking…';
            div.innerHTML = '<div class="bubble typing">' + label + '</div>';
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
            return div;
        }

        async function changeModel() {
            if (!currentSessionId) return;
            const model = document.getElementById('modelSelect').value;
            await fetch('/assistente/sessions/' + currentSessionId + '/model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_name: model })
            });
        }

        (async () => {
            renderWelcome();
            await loadSessions();
        })();
    </script>
</body>
</html>"""

    # -------------------------------------------------------------------------
    # CHAT ENDPOINT
    # -------------------------------------------------------------------------
    @http.route('/assistente/chat', type='http', auth='user', methods=['POST'], csrf=False)
    def chat_endpoint(self):
        try:
            data = json.loads(request.httprequest.data)
            pergunta = data.get('mensagem', '').strip()
            session_id = data.get('session_id')
            if not pergunta:
                return Response(json.dumps({'erro': 'Empty message'}), status=400)

            deep_thinking = bool(data.get('deep_thinking', False))
            user = request.env.user
            is_manager = _is_user_manager(user.id)
            model_name = "groq"
            if session_id:
                session = request.env['ai.session'].browse(session_id)
                if session.exists():
                    model_name = session.model_name or "groq"

            _logger.info(f"USER {user.login} role: {'manager' if is_manager else 'member'} model: {model_name} deep: {deep_thinking}")
            inicio = time.time()
            resposta = call_agent_api(pergunta, user.id, is_manager, model_name, deep_thinking)
            _logger.info(f"Response in {time.time()-inicio:.3f}s")
            return Response(json.dumps({'resposta': resposta or 'No response'}), content_type='application/json')
        except Exception as e:
            _logger.error(traceback.format_exc())
            return Response(json.dumps({'erro': str(e)}), status=500)

    # -------------------------------------------------------------------------
    # DASHBOARD
    # -------------------------------------------------------------------------
    @http.route('/assistente/dashboard', type='http', auth='user', website=True)
    def dashboard_geral(self):
        stats = get_project_stats()
        stage_list = stats.get('stats_stages', [])
        user_list = stats.get('user_stats', [])

        stage_labels = json.dumps([s['name'] for s in stage_list])
        stage_data = json.dumps([s['count'] for s in stage_list])
        stage_colors = json.dumps(_chart_colors(len(stage_list)))

        user_labels = json.dumps([u['name'] for u in user_list])
        user_data = json.dumps([u['count'] for u in user_list])

        stage_detail = ''.join(
            f'<div class="detail-item"><span class="label">{s["name"]}</span><span class="value">{s["count"]}</span></div>'
            for s in stage_list
        ) or '<p style="color:#9ca3af;">No data</p>'

        user_detail = ''.join(
            f'<div class="detail-item"><span class="label">{u["name"]}</span><span class="value">{u["count"]}</span></div>'
            for u in user_list
        ) or '<p style="color:#9ca3af;">No data</p>'

        content = f"""
        <div class="container" style="padding-top: 80px;">
            <h1 style="color: var(--primary); margin-bottom: 6px;"><i class="fas fa-chart-pie"></i> Global Dashboard</h1>
            <p style="color: var(--muted); margin-bottom: 30px;">Overview of all projects and tasks</p>

            <div class="stats-grid">
                <div class="stat-card"><h3>{stats.get('total_projects', 0)}</h3><p>Projects</p></div>
                <div class="stat-card"><h3>{stats.get('total_tasks', 0)}</h3><p>Tasks</p></div>
                <div class="stat-card"><h3>{len(stage_list)}</h3><p>Stages</p></div>
                <div class="stat-card"><h3>{stats.get('avg_lead_time', 0):.1f}</h3><p>Lead Time</p></div>
                <div class="stat-card"><h3>{stats.get('throughput', 0):.1f}</h3><p>Tasks/day</p></div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="chart-card">
                    <h3><i class="fas fa-circle-notch"></i> Tasks by Stage</h3>
                    <canvas id="stageChart" style="max-height: 320px;"></canvas>
                </div>
                <div class="chart-card">
                    <h3><i class="fas fa-users"></i> Tasks by Creator</h3>
                    <canvas id="userChart" style="max-height: 320px;"></canvas>
                </div>
            </div>

            <div class="detail-section">
                <h3><i class="fas fa-list-check"></i> Detailed Stage Breakdown</h3>
                <div class="detail-grid">{stage_detail}</div>
            </div>

            <div class="detail-section">
                <h3><i class="fas fa-user-friends"></i> Detailed Creator Breakdown</h3>
                <div class="detail-grid">{user_detail}</div>
            </div>

            <script>
                new Chart(document.getElementById('stageChart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: {stage_labels},
                        datasets: [{{ data: {stage_data}, backgroundColor: {stage_colors}, borderWidth: 2, borderColor: '#fff' }}]
                    }},
                    options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
                }});
                new Chart(document.getElementById('userChart'), {{
                    type: 'bar',
                    data: {{
                        labels: {user_labels},
                        datasets: [{{ label: 'Tasks', data: {user_data}, backgroundColor: '#714B67', borderRadius: 8 }}]
                    }},
                    options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }},
                                scales: {{ y: {{ beginAtZero: true }} }} }}
                }});
            </script>
        </div>
        """
        return _page("Dashboard", content)

    # -------------------------------------------------------------------------
    # PROJECTS LIST
    # -------------------------------------------------------------------------
    @http.route('/assistente/projetos', type='http', auth='user', website=True)
    def lista_projetos(self):
        projetos = request.env['project.project'].search([])
        rows = ''
        for p in projetos:
            task_count = request.env['project.task'].search_count([('project_id', '=', p.id)])
            rows += f"""
                <a href="/assistente/projeto/{p.id}" class="action-card" style="text-align: left;">
                    <i class="fas fa-folder"></i>
                    <h3>{p.name}</h3>
                    <p>{task_count} tasks</p>
                </a>
            """
        if not rows:
            rows = '<p style="color: var(--muted); text-align: center; grid-column: 1/-1;">No projects found.</p>'

        content = f"""
        <div class="container" style="padding-top: 80px;">
            <h1 style="color: var(--primary); margin-bottom: 6px;"><i class="fas fa-folder-open"></i> All Projects</h1>
            <p style="color: var(--muted); margin-bottom: 30px;">Browse every project in the ecosystem</p>
            <div class="project-grid">{rows}</div>
        </div>
        """
        return _page("All Projects", content)

    # -------------------------------------------------------------------------
    # PROJECT DETAIL
    # -------------------------------------------------------------------------
    @http.route('/assistente/projeto/<int:projeto_id>', type='http', auth='user', website=True)
    def dashboard_projeto(self, projeto_id):
        stats = get_project_stats(projeto_id)
        if stats is None:
            return _page("Not Found", "<div class='container'><h1>Project not found</h1></div>",
                         back_url="/assistente/projetos")

        project_name = stats.get('project_name', 'Project')
        tasks = stats.get('task_list', [])
        total = len(tasks)

        stage_counts = {}
        assignee_counts = {}
        for t in tasks:
            s = t.get('stage') or 'No Stage'
            stage_counts[s] = stage_counts.get(s, 0) + 1
            a = t.get('assignee') or 'Unassigned'
            assignee_counts[a] = assignee_counts.get(a, 0) + 1

        stage_labels = json.dumps(list(stage_counts.keys()))
        stage_data = json.dumps(list(stage_counts.values()))
        stage_colors = json.dumps(_chart_colors(len(stage_counts)))

        assignee_labels = json.dumps(list(assignee_counts.keys()))
        assignee_data = json.dumps(list(assignee_counts.values()))

        rows = ''.join(
            f'<tr><td><strong>{t["name"]}</strong></td><td>{t["stage"]}</td><td>{t["assignee"]}</td><td>{t["create_date"]}</td></tr>'
            for t in tasks
        ) or '<tr><td colspan="4" style="text-align:center;color:#9ca3af;">No tasks</td></tr>'

        content = f"""
        <div class="container" style="padding-top: 80px;">
            <h1 style="color: var(--primary); margin-bottom: 6px;"><i class="fas fa-project-diagram"></i> {project_name}</h1>
            <p style="color: var(--muted); margin-bottom: 30px;">{total} tasks · {len(stage_counts)} stages</p>

            <div class="stats-grid">
                <div class="stat-card"><h3>{total}</h3><p>Total Tasks</p></div>
                <div class="stat-card"><h3>{len(stage_counts)}</h3><p>Stages</p></div>
                <div class="stat-card"><h3>{len(assignee_counts)}</h3><p>Contributors</p></div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="chart-card">
                    <h3><i class="fas fa-chart-pie"></i> Tasks by Stage</h3>
                    <canvas id="stageChart" style="max-height: 300px;"></canvas>
                </div>
                <div class="chart-card">
                    <h3><i class="fas fa-user-friends"></i> Tasks by Assignee</h3>
                    <canvas id="assigneeChart" style="max-height: 300px;"></canvas>
                </div>
            </div>

            <div class="chart-card">
                <h3><i class="fas fa-list-check"></i> Task List</h3>
                <table class="data-table">
                    <thead>
                        <tr><th>Name</th><th>Stage</th><th>Assignee</th><th>Created</th></tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>

            <div style="display: flex; gap: 12px; margin-top: 24px;">
                <a href="/assistente/relatorio/{projeto_id}" class="btn">
                    <i class="fas fa-file-pdf"></i> Download PDF Report
                </a>
                <a href="/assistente/exportar/{projeto_id}" class="btn btn-secondary">
                    <i class="fas fa-file-csv"></i> Export CSV
                </a>
            </div>

            <script>
                new Chart(document.getElementById('stageChart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: {stage_labels},
                        datasets: [{{ data: {stage_data}, backgroundColor: {stage_colors}, borderWidth: 2, borderColor: '#fff' }}]
                    }},
                    options: {{ responsive: true, plugins: {{ legend: {{ position: 'bottom' }} }} }}
                }});
                new Chart(document.getElementById('assigneeChart'), {{
                    type: 'bar',
                    data: {{
                        labels: {assignee_labels},
                        datasets: [{{ label: 'Tasks', data: {assignee_data}, backgroundColor: '#714B67', borderRadius: 8 }}]
                    }},
                    options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }},
                                scales: {{ y: {{ beginAtZero: true }} }} }}
                }});
            </script>
        </div>
        """
        return _page(project_name, content, back_url="/assistente/projetos", back_text="Projects")

    # -------------------------------------------------------------------------
    # PDF
    # -------------------------------------------------------------------------
    @http.route('/assistente/relatorio/<int:projeto_id>', type='http', auth='user', website=True)
    def relatorio_pdf(self, projeto_id):
        pdf = _generate_pdf(projeto_id)
        if pdf is None:
            return "Project not found"
        return request.make_response(
            pdf,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename=report_{projeto_id}.pdf')
            ]
        )

    # -------------------------------------------------------------------------
    # CSV
    # -------------------------------------------------------------------------
    @http.route('/assistente/exportar/<int:projeto_id>', type='http', auth='user', website=True)
    def exportar_csv(self, projeto_id):
        Project = request.env['project.project']
        Task = request.env['project.task']
        project = Project.browse(projeto_id)
        if not project.exists():
            return "Project not found"
        tasks = Task.search([('project_id', '=', projeto_id)])
        output = StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(['Project', project.name])
        writer.writerow(['Date', datetime.now().strftime('%d/%m/%Y %H:%M')])
        writer.writerow([])
        writer.writerow(['Name', 'Stage', 'Creator', 'Created'])
        for t in tasks:
            stage = t.stage_id.name if t.stage_id else 'No Stage'
            creator = t.create_uid.name if t.create_uid else 'Unknown'
            writer.writerow([t.name, stage, creator,
                             t.create_date.strftime('%d/%m/%Y') if t.create_date else '-'])
        return request.make_response(
            output.getvalue().encode('utf-8'),
            headers=[
                ('Content-Type', 'text/csv; charset=utf-8'),
                ('Content-Disposition', f'attachment; filename=project_{projeto_id}.csv')
            ]
        )

    # -------------------------------------------------------------------------
    # MY WORKSPACE (role-filtered)
    # -------------------------------------------------------------------------
    @http.route('/assistente/meus-projetos', type='http', auth='user', website=True)
    def meus_projetos(self):
        user = request.env.user
        is_manager = _is_user_manager(user.id)
        Project = request.env['project.project']
        Task = request.env['project.task']

        rows = []
        if is_manager:
            projetos = Project.search([])
            for p in projetos:
                task_count = Task.search_count([('project_id', '=', p.id)])
                rows.append(
                    f'<a href="/assistente/projeto/{p.id}" class="my-project-row">'
                    f'<div class="icon-box"><i class="fas fa-briefcase"></i></div>'
                    f'<div class="info"><h3>{p.name}</h3>'
                    f'<p>Project Manager view · full access</p></div>'
                    f'<span class="count-badge">{task_count} tasks</span></a>'
                )
        else:
            my_task_ids = Task.search([('user_ids', 'in', [user.id])]).ids
            my_project_ids = list({t.project_id.id for t in Task.browse(my_task_ids) if t.project_id})
            if my_project_ids:
                projetos = Project.browse(my_project_ids)
                for p in projetos:
                    my_task_count = Task.search_count([
                        ('project_id', '=', p.id),
                        ('user_ids', 'in', [user.id])
                    ])
                    total_count = Task.search_count([('project_id', '=', p.id)])
                    rows.append(
                        f'<a href="/assistente/projeto/{p.id}" class="my-project-row">'
                        f'<div class="icon-box" style="background: linear-gradient(135deg, #D97706, #B45309);">'
                        f'<i class="fas fa-tasks"></i></div>'
                        f'<div class="info"><h3>{p.name}</h3>'
                        f'<p>{my_task_count} tasks assigned to you · {total_count} total</p></div>'
                        f'<span class="count-badge">{my_task_count}</span></a>'
                    )

        rows_html = ''.join(rows) or (
            '<p style="color: var(--muted); text-align: center; padding: 40px;">'
            + ('No projects found.' if is_manager else 'You have no tasks assigned yet.')
            + '</p>'
        )

        if is_manager:
            header_icon = "fa-user-tie"
            header_grad = "linear-gradient(135deg, #714B67, #875A7A)"
            subtitle = f"Welcome, {user.name} — Manager view (all projects)"
            title = "My Workspace"
            section_title = "All Projects (Manager View)"
        else:
            header_icon = "fa-tasks"
            header_grad = "linear-gradient(135deg, #D97706, #B45309)"
            subtitle = f"Welcome, {user.name} — Team Member view"
            title = "My Tasks"
            section_title = "Projects where you have assigned tasks"

        content = f"""
        <div class="container" style="padding-top: 80px;">
            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 30px;">
                <div style="width: 60px; height: 60px; border-radius: 16px;
                            background: {header_grad};
                            display: flex; align-items: center; justify-content: center;
                            box-shadow: 0 6px 16px rgba(0,0,0,0.15);">
                    <i class="fas {header_icon}" style="color: white; font-size: 1.7rem;"></i>
                </div>
                <div>
                    <h1 style="color: var(--primary);">{title}</h1>
                    <p style="color: var(--muted);">{subtitle}</p>
                </div>
            </div>

            <div class="chart-card">
                <h3><i class="fas fa-list"></i> {section_title}</h3>
                <div class="my-project-list">
                    {rows_html}
                </div>
            </div>
        </div>
        """
        return _page(title, content)

    # -------------------------------------------------------------------------
    # SESSION MANAGEMENT
    # -------------------------------------------------------------------------
    @http.route('/assistente/sessions', type='http', auth='user', methods=['GET'], csrf=False)
    def list_sessions(self):
        try:
            sessions = request.env['ai.session'].search([('user_id', '=', request.env.user.id)])
            data = [{
                'id': s.id,
                'name': s.name,
                'model_name': s.model_name or 'groq',
                'create_date': s.create_date.isoformat() if s.create_date else None,
            } for s in sessions]
            return Response(json.dumps(data), content_type='application/json')
        except Exception as e:
            _logger.error(f"list_sessions error: {e}")
            return Response(json.dumps([]), content_type='application/json')

    @http.route('/assistente/sessions/create', type='http', auth='user', methods=['POST'], csrf=False)
    def create_session(self):
        try:
            data = json.loads(request.httprequest.data)
            name = data.get('name', 'New Chat')
            session = request.env['ai.session'].create({
                'name': name,
                'user_id': request.env.user.id,
                'model_name': data.get('model_name', 'groq'),
                'messages': json.dumps([]),
            })
            return Response(
                json.dumps({'id': session.id, 'name': session.name}),
                content_type='application/json'
            )
        except Exception as e:
            _logger.error(f"create_session error: {e}")
            return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    @http.route('/assistente/sessions/<int:session_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def get_session(self, session_id):
        session = request.env['ai.session'].browse(session_id)
        if not session.exists() or session.user_id.id != request.env.user.id:
            return Response(json.dumps({'error': 'Session not found'}), status=404)
        return Response(json.dumps({
            'id': session.id,
            'name': session.name,
            'model_name': session.model_name or 'groq',
            'messages': json.loads(session.messages or '[]'),
        }), content_type='application/json')

    @http.route('/assistente/sessions/<int:session_id>/messages', type='http', auth='user', methods=['POST'], csrf=False)
    def add_message(self, session_id):
        session = request.env['ai.session'].browse(session_id)
        if not session.exists() or session.user_id.id != request.env.user.id:
            return Response(json.dumps({'error': 'Session not found'}), status=404)
        data = json.loads(request.httprequest.data)
        messages = json.loads(session.messages or '[]')
        messages.append({'role': data.get('role', 'user'), 'content': data.get('content', '')})
        session.messages = json.dumps(messages)
        return Response(json.dumps({'status': 'ok'}), content_type='application/json')

    @http.route('/assistente/sessions/<int:session_id>/model', type='http', auth='user', methods=['POST'], csrf=False)
    def change_model(self, session_id):
        session = request.env['ai.session'].browse(session_id)
        if not session.exists() or session.user_id.id != request.env.user.id:
            return Response(json.dumps({'error': 'Session not found'}), status=404)
        data = json.loads(request.httprequest.data)
        session.model_name = data.get('model_name', 'groq')
        return Response(json.dumps({'status': 'ok'}), content_type='application/json')

    @http.route('/assistente/sessions/<int:session_id>/rename', type='http', auth='user', methods=['POST'], csrf=False)
    def rename_session(self, session_id):
        session = request.env['ai.session'].browse(session_id)
        if not session.exists() or session.user_id.id != request.env.user.id:
            return Response(json.dumps({'error': 'Session not found'}), status=404)
        data = json.loads(request.httprequest.data)
        new_name = (data.get('name') or '').strip()
        if not new_name:
            return Response(json.dumps({'error': 'Empty name'}), status=400)
        session.name = new_name
        return Response(json.dumps({'status': 'ok', 'name': new_name}), content_type='application/json')

    @http.route('/assistente/sessions/<int:session_id>/delete', type='http', auth='user', methods=['POST'], csrf=False)
    def delete_session(self, session_id):
        session = request.env['ai.session'].browse(session_id)
        if not session.exists() or session.user_id.id != request.env.user.id:
            return Response(json.dumps({'error': 'Session not found'}), status=404)
        session.unlink()
        return Response(json.dumps({'status': 'ok'}), content_type='application/json')
