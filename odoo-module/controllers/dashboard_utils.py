# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from odoo.http import request

_logger = logging.getLogger(__name__)

def get_project_stats(project_id=None):
    try:
        env = request.env
        if project_id:
            Project = env['project.project']
            Task = env['project.task']
        else:
            Project = env['project.project'].sudo()
            Task = env['project.task'].sudo()

        if project_id:
            project = Project.browse(project_id)
            if not project.exists():
                return None
            tasks = Task.search([('project_id', '=', project.id)])
            task_list = []
            for t in tasks:
                stage_name = t.stage_id.name if t.stage_id else 'No Stage'
                assignee = t.create_uid.name if t.create_uid else 'Unassigned'
                status_label = dict(t._fields['task_status'].selection).get(t.task_status or 'in_backlog', 'In Backlog')
                task_list.append({
                    'id': t.id, 'name': t.name, 'stage': stage_name, 'assignee': assignee,
                    'create_date': t.create_date.strftime('%d/%m/%Y') if t.create_date else '-',
                    'task_status': t.task_status or 'in_backlog', 'task_status_label': status_label,
                })
            return {'project_name': project.name, 'task_list': task_list, 'total_tasks': len(tasks)}

        total_projects = Project.search_count([])
        total_tasks = Task.search_count([('name', '!=', False)])

        # Stats by stage (Odoo 19 _read_group)
        stats_stages = []
        try:
            groups = Task._read_group(
                domain=[('name', '!=', False), ('name', '!=', '')],
                groupby=['stage_id'],
                aggregates=['id:count'],
            )
            for stage, count in groups:
                name = stage.display_name if stage else 'No Stage'
                stats_stages.append({'name': name, 'count': count})
        except Exception as e:
            _logger.warning(f"Stage grouping failed: {e}")

        # Stats by creator (Odoo 19 _read_group)
        user_stats = []
        try:
            groups = Task._read_group(
                domain=[('name', '!=', False), ('name', '!=', '')],
                groupby=['create_uid'],
                aggregates=['id:count'],
            )
            for user, count in groups:
                name = user.display_name if user else 'Unknown'
                user_stats.append({'name': name, 'count': count})
        except Exception as e:
            _logger.warning(f"User grouping failed: {e}")

        avg_lead_time = 0.0
        try:
            completed = Task.search([('task_status', '=', 'concluded'), ('date_end', '!=', False), ('name', '!=', False)])
            if completed:
                days = []
                for t in completed:
                    if t.create_date and t.date_end:
                        d = (t.date_end - t.create_date).days
                        if d >= 0: days.append(d)
                if days: avg_lead_time = round(sum(days) / len(days), 1)
        except Exception as e:
            _logger.warning(f"Lead time calculation failed: {e}")

        throughput = 0.0
        try:
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent = Task.search_count([('write_date', '>=', seven_days_ago), ('name', '!=', False)])
            throughput = round(recent / 7.0, 1)
        except Exception as e:
            _logger.warning(f"Activity calculation failed: {e}")

        burndown_labels, burndown_data = [], []
        try:
            today_d = datetime.now().date()
            for i in range(13, -1, -1):
                d = today_d - timedelta(days=i)
                day_end = datetime.combine(d, datetime.max.time())
                open_count = Task.search_count([('create_date', '<=', day_end), '|', ('date_end', '=', False), ('date_end', '>', day_end)])
                burndown_labels.append(d.strftime('%d/%m'))
                burndown_data.append(open_count)
        except Exception as e:
            _logger.warning(f"Burndown failed: {e}")

        velocity_labels, velocity_data = [], []
        try:
            today_d = datetime.now().date()
            monday_this_week = today_d - timedelta(days=today_d.weekday())
            for i in range(7, -1, -1):
                week_start_d = monday_this_week - timedelta(days=i * 7)
                week_end_d = week_start_d + timedelta(days=6)
                ws_dt = datetime.combine(week_start_d, datetime.min.time())
                we_dt = datetime.combine(week_end_d, datetime.max.time())
                count = Task.search_count([('date_end', '>=', ws_dt), ('date_end', '<=', we_dt)])
                velocity_labels.append(week_start_d.strftime('%d/%m'))
                velocity_data.append(count)
        except Exception as e:
            _logger.warning(f"Velocity failed: {e}")

        return {
            'total_projects': total_projects, 'total_tasks': total_tasks,
            'stats_stages': stats_stages, 'user_stats': user_stats,
            'avg_lead_time': avg_lead_time, 'throughput': throughput,
            'burndown_labels': burndown_labels, 'burndown_data': burndown_data,
            'velocity_labels': velocity_labels, 'velocity_data': velocity_data,
        }
    except Exception as e:
        _logger.error(f"get_project_stats error: {e}")
        return {'total_projects': 0, 'total_tasks': 0, 'stats_stages': [], 'user_stats': [], 'avg_lead_time': 0.0, 'throughput': 0.0, 'burndown_labels': [], 'burndown_data': [], 'velocity_labels': [], 'velocity_data': []}
