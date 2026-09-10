# -*- coding: utf-8 -*-
from odoo import http
from datetime import datetime, timedelta

def _valid_count(domain):
    """Conta tarefas válidas (nome preenchido e com projeto)."""
    Task = http.request.env['project.task']
    full_domain = domain + [
        ('name', '!=', False),
        ('name', '!=', ''),
        ('project_id', '!=', False),
    ]
    return Task.search_count(full_domain)

def get_project_stats(project_id=None, user_id=None):
    Project = http.request.env['project.project']
    Task = http.request.env['project.task']
    Stage = http.request.env['project.task.type']
    User = http.request.env['res.users']

    if project_id:
        project = Project.browse(project_id)
        if not project.exists():
            return None
        project_data = project.read(['name', 'description'])[0]
        if not project_data:
            return None

        tasks = Task.search([
            ('project_id', '=', project_id),
            ('name', '!=', False),
            ('name', '!=', ''),
        ])
        total_tarefas = len(tasks)

        no_stage_count = _valid_count([
            ('project_id', '=', project_id),
            ('stage_id', '=', False),
        ])

        stats_stages = []
        for stage in Stage.search([]):
            if stage.name and stage.name.upper() == 'NO_STAGE':
                continue
            count = _valid_count([
                ('project_id', '=', project_id),
                ('stage_id', '=', stage.id),
            ])
            if count > 0:
                stats_stages.append({'nome': stage.name, 'count': count})

        if no_stage_count > 0:
            stats_stages.append({'nome': 'Sem Stage', 'count': no_stage_count})

        user_stats = []
        for user in User.search([]):
            count = _valid_count([
                ('project_id', '=', project_id),
                ('create_uid', '=', user.id),
            ])
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
                ('create_date', '<', (d + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')),
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
        # ============ DASHBOARD GERAL ============
        # Conta apenas PROJECTOS reais
        projetos = Project.search([])
        total_projetos = len(projetos)

        # Conta apenas TAREFAS COM PROJETO (ignora to-dos pessoais)
        total_tarefas = Task.search_count([
            ('name', '!=', False),
            ('name', '!=', ''),
            ('project_id', '!=', False),
        ])

        # Stages: apenas os que têm pelo menos 1 tarefa COM PROJETO
        stats_stages = []
        for stage in Stage.search([]):
            if stage.name and stage.name.upper() == 'NO_STAGE':
                continue
            count = Task.search_count([
                ('stage_id', '=', stage.id),
                ('name', '!=', False),
                ('name', '!=', ''),
                ('project_id', '!=', False),
            ])
            if count > 0:
                stats_stages.append({'nome': stage.name, 'count': count})

        # "Sem Stage" conta tarefas válidas sem stage
        no_stage_count = Task.search_count([
            ('stage_id', '=', False),
            ('name', '!=', False),
            ('name', '!=', ''),
            ('project_id', '!=', False),
        ])
        if no_stage_count > 0:
            stats_stages.append({'nome': 'Sem Stage', 'count': no_stage_count})

        # Utilizadores: apenas os que criaram tarefas VÁLIDAS (com projeto)
        user_stats = []
        for user in User.search([]):
            count = Task.search_count([
                ('create_uid', '=', user.id),
                ('name', '!=', False),
                ('name', '!=', ''),
                ('project_id', '!=', False),
            ])
            if count > 0:
                user_stats.append({'nome': user.name, 'count': count})

        # Lead time: apenas tarefas sem stage E com projeto
        tasks_no_stage = Task.search([
            ('stage_id', '=', False),
            ('name', '!=', False),
            ('name', '!=', ''),
            ('project_id', '!=', False),
        ])
        avg_lead_time = 0
        if tasks_no_stage:
            total_days = 0
            for t in tasks_no_stage:
                if t.create_date:
                    delta = datetime.now() - t.create_date
                    total_days += delta.days
            avg_lead_time = total_days / len(tasks_no_stage)

        week_ago = datetime.now() - timedelta(days=7)
        tasks_week = Task.search_count([
            ('create_date', '>=', week_ago.strftime('%Y-%m-%d %H:%M:%S')),
            ('name', '!=', False),
            ('name', '!=', ''),
            ('project_id', '!=', False),
        ])
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
