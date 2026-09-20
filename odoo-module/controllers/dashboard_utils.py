# -*- coding: utf-8 -*-
import logging
from odoo.http import request

_logger = logging.getLogger(__name__)


def get_project_stats(project_id=None):
    """Return statistics for the dashboard. Safe: never raises."""
    try:
        env = request.env
        Project = env['project.project']
        Task = env['project.task']

        # ---- Project-specific stats ----
        if project_id:
            project = Project.browse(project_id)
            if not project.exists():
                return None

            tasks = Task.search([('project_id', '=', project.id)])
            task_list = []
            for t in tasks:
                stage_name = t.stage_id.name if t.stage_id else 'No Stage'
                assignee = t.create_uid.name if t.create_uid else 'Unassigned'
                task_list.append({
                    'name': t.name,
                    'stage': stage_name,
                    'assignee': assignee,
                    'create_date': t.create_date.strftime('%d/%m/%Y') if t.create_date else '-',
                })
            return {
                'project_name': project.name,
                'task_list': task_list,
                'total_tasks': len(tasks),
            }

        # ---- Global stats ----
        total_projects = Project.search_count([])
        total_tasks = Task.search_count([('name', '!=', False)])

        # Stats by stage (safe)
        stats_stages = []
        try:
            groups = Task.read_group(
                domain=[('name', '!=', False), ('name', '!=', '')],
                fields=['id'],
                groupby=['stage_id'],
            )
            for g in groups:
                stage = g.get('stage_id')
                name = stage[1] if stage else 'No Stage'
                count = g.get('stage_id_count', 0) or g.get('__count', 0)
                stats_stages.append({'name': name, 'count': count})
        except Exception as e:
            _logger.warning(f"Stage grouping failed: {e}")

        # Stats by creator (safe)
        user_stats = []
        try:
            groups = Task.read_group(
                domain=[('name', '!=', False), ('name', '!=', '')],
                fields=['id'],
                groupby=['create_uid'],
            )
            for g in groups:
                user = g.get('create_uid')
                name = user[1] if user else 'Unknown'
                count = g.get('create_uid_count', 0) or g.get('__count', 0)
                user_stats.append({'name': name, 'count': count})
        except Exception as e:
            _logger.warning(f"User grouping failed: {e}")

        return {
            'total_projects': total_projects,
            'total_tasks': total_tasks,
            'stats_stages': stats_stages,
            'user_stats': user_stats,
            'avg_lead_time': 0.0,
            'throughput': 0.0,
        }
    except Exception as e:
        _logger.error(f"get_project_stats error: {e}")
        return {
            'total_projects': 0,
            'total_tasks': 0,
            'stats_stages': [],
            'user_stats': [],
            'avg_lead_time': 0.0,
            'throughput': 0.0,
        }
