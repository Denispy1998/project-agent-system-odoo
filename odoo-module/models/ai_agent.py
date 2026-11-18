# -*- coding: utf-8 -*-
from odoo import models, fields

class AIAgent(models.Model):
    _name = 'ai.agent'
    _description = 'AI Agent Instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Agent Name', required=True, tracking=True)
    workspace_id = fields.Many2one('ai.workspace', string='Workspace', required=True, ondelete='cascade')
    template_id = fields.Many2one('ai.template', string='Agent Template', required=True)
    company_id = fields.Many2one('res.company', string='Organization', required=True, default=lambda self: self.env.company)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('stopped', 'Stopped'),
    ], string='Status', default='draft')

    tool_ids = fields.Many2many('ai.tool', 'ai_agent_tool_rel', 'agent_id', 'tool_id', string='Tools')

    active = fields.Boolean(default=True)

    def action_start(self):
        self.write({'state': 'running'})

    def action_stop(self):
        self.write({'state': 'stopped'})
