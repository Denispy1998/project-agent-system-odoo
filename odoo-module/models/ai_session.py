# -*- coding: utf-8 -*-
from odoo import models, fields

class AISession(models.Model):
    _name = 'ai.session'
    _description = 'AI Chat Session'
    _order = 'create_date desc'

    name = fields.Char(string='Session Name', required=True)
    user_id = fields.Many2one('res.users', string='User',
                              required=True,
                              default=lambda self: self.env.user)
    model_name = fields.Char(string='Model', default='groq')
    messages = fields.Text(string='Messages (JSON)', default='[]')
    
    company_id = fields.Many2one('res.company', string='Organization', required=True, default=lambda self: self.env.company)
    workspace_id = fields.Many2one('ai.workspace', string='Workspace')
    
    active = fields.Boolean(default=True)
