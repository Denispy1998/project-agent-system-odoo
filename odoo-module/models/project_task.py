# -*- coding: utf-8 -*-
"""Extend project.task with task_status (In Backlog / In Progress / Concluded).

Aligned with RSL v2 TaskStatusKind. When task_status becomes 'concluded',
date_end is auto-filled. When it moves away from 'concluded', date_end
is cleared. Works both via UI (onchange) and via XML-RPC (write override).
"""
from odoo import models, fields, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    task_status = fields.Selection(
        selection=[
            ('in_backlog', 'In Backlog'),
            ('in_progress', 'In Progress'),
            ('concluded', 'Concluded'),
        ],
        string='Task Status',
        default='in_backlog',
        required=True,
        tracking=True,
        help='Simple progress status: In Backlog / In Progress / Concluded.',
    )

    @api.onchange('task_status')
    def _onchange_task_status(self):
        for task in self:
            if task.task_status == 'concluded' and not task.date_end:
                task.date_end = fields.Datetime.now()
            elif task.task_status != 'concluded':
                task.date_end = False

    def write(self, vals):
        if 'task_status' in vals:
            if vals['task_status'] == 'concluded':
                if 'date_end' not in vals:
                    vals['date_end'] = fields.Datetime.now()
            else:
                vals['date_end'] = False
        return super().write(vals)
