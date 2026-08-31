# -*- coding: utf-8 -*-
import io
import logging
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from odoo import http

_logger = logging.getLogger(__name__)

def generate_project_report(project_id):
    """Gera um relatório PDF para um projeto."""
    Project = http.request.env['project.project']
    Task = http.request.env['project.task']
    project = Project.browse(project_id)
    if not project.exists():
        return None

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 2*cm, f"Relatório do Projeto: {project.name}")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 3*cm, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawString(2*cm, height - 3.8*cm, f"Descrição: {project.description or 'Sem descrição'}")

    # Tarefas
    tasks = Task.search([('project_id', '=', project.id)])
    y = height - 5*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, f"Tarefas ({len(tasks)})")
    y -= 0.8*cm
    c.setFont("Helvetica", 10)
    for t in tasks[:20]:  # limite para não sobrecarregar
        stage = t.stage_id.name if t.stage_id else "NO_STAGE"
        assignee = t.user_id.name if t.user_id else "Não atribuído"
        c.drawString(2*cm, y, f"- {t.name} (Stage: {stage}, Atribuída a: {assignee})")
        y -= 0.6*cm
        if y < 2*cm:
            c.showPage()
            y = height - 2*cm

    # Análise de riscos (simples)
    y -= 1*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Análise de Riscos")
    y -= 0.8*cm
    c.setFont("Helvetica", 10)
    no_stage = Task.search_count([('project_id', '=', project.id), ('stage_id', '=', False)])
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

    # Rodapé
    c.setFont("Helvetica", 8)
    c.drawString(2*cm, 1*cm, f"Gerado automaticamente pelo Ecossistema IA - {datetime.now().year}")

    c.save()
    buffer.seek(0)
    return buffer
