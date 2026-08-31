# -*- coding: utf-8 -*-
from odoo import http
from datetime import datetime, timedelta

def _valid_count(domain):
    Task = http.request.env['project.task']
    return Task.search_count(domain + [('name', '!=', False), ('name', '!=', '')])

def get_project_stats(project_id=None, user_id=None):
    Project = http.request.env['project.project']
    Task = http.request.env['project.task']
    Stage = http.request.env['project.task.type']
    User = http.request.env['res.users']

    if project_id:
        project = Project.browse(project_id)
        if not project.exists():
            return None

        # Pré‑carregar os dados do projeto para evitar cursor fechado
        project_data = project.read(['name', 'description'])[0] if project.exists() else None
        if not project_data:
            return None

        tasks = Task.search([('project_id', '=', project_id), ('name', '!=', False), ('name', '!=', '')])
        total_tarefas = len(tasks)

        no_stage_count = _valid_count([('project_id', '=', project_id), ('stage_id', '=', False)])

        stats_stages = []
        for stage in Stage.search([]):
            if stage.name and stage.name.upper() == 'NO_STAGE':
                continue
            count = _valid_count([('project_id', '=', project_id), ('stage_id', '=', stage.id)])
            if count > 0:
                stats_stages.append({'nome': stage.name, 'count': count})

        if no_stage_count > 0:
            stats_stages.append({'nome': 'Sem Stage', 'count': no_stage_count})

        user_stats = []
        for user in User.search([]):
            count = _valid_count([('project_id', '=', project_id), ('create_uid', '=', user.id)])
            if count > 0:
                user_stats.append({'nome': user.name, 'count': count})

        task_list = []
        for t in tasks:
            stage = 'Sem Stage' if not t.stage_id else t.stage_id.name
            assignee_obj = getattr(t, 'user_id', None) or getattr(t, 'create_uid', None)
            assignee = assignee_obj.name if assignee_obj else 'Não atribuído'
            create_date_str = t.create_date.strftime('%d/%m/%Y') if t.create_date else '-'
            task_list.append({
                'name': t.name,
                'stage': stage,
                'assignee': assignee,
                'create_date': create_date_str,
            })

        today = datetime.now()
        start_date = today - timedelta(days=30)
        dates = []
        counts = []
        for i in range(30):
            d = start_date + timedelta(days=i)
            count = _valid_count([
                ('project_id', '=', project_id),
                ('create_date', '>=', d.strftime('%Y-%m-%d %H:%M:%S')),
                ('create_date', '<', (d + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'))
            ])
            dates.append(d.strftime('%d/%m'))
            counts.append(count)

        return {
            'project': project_data,
            'project_id': project_id,
            'project_name': project_data['name'],
            'total_projetos': 1,
            'total_tarefas': total_tarefas,
            'stats_stages': stats_stages,
            'user_stats': user_stats,
            'task_list': task_list,
            'burndown_dates': dates,
            'burndown_counts': counts,
        }

    else:
        # Dashboard geral
        projetos = Project.search([])
        total_projetos = len(projetos)
        total_tarefas = _valid_count([])

        stats_stages = []
        for stage in Stage.search([]):
            if stage.name and stage.name.upper() == 'NO_STAGE':
                continue
            count = _valid_count([('stage_id', '=', stage.id)])
            if count > 0:
                stats_stages.append({'nome': stage.name, 'count': count})

        no_stage_count = _valid_count([('stage_id', '=', False)])
        if no_stage_count > 0:
            stats_stages.append({'nome': 'Sem Stage', 'count': no_stage_count})

        user_stats = []
        for user in User.search([]):
            count = _valid_count([('create_uid', '=', user.id)])
            if count > 0:
                user_stats.append({'nome': user.name, 'count': count})

        tasks_no_stage = Task.search([('stage_id', '=', False), ('name', '!=', False), ('name', '!=', '')])
        avg_lead_time = 0
        if tasks_no_stage:
            total_days = 0
            for t in tasks_no_stage:
                if t.create_date:
                    delta = datetime.now() - t.create_date
                    total_days += delta.days
            avg_lead_time = total_days / len(tasks_no_stage)

        week_ago = datetime.now() - timedelta(days=7)
        tasks_week = _valid_count([('create_date', '>=', week_ago.strftime('%Y-%m-%d %H:%M:%S'))])
        throughput = tasks_week / 7 if tasks_week else 0

        return {
            'total_projetos': total_projetos,
            'total_tarefas': total_tarefas,
            'stats_stages': stats_stages,
            'user_stats': user_stats,
            'projetos': projetos,
            'avg_lead_time': avg_lead_time,
            'throughput': throughput,
        }
