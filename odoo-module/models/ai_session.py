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
    messages = fields.Text(string='Messages (JSON)', default='[]')
    model_name = fields.Char(string='Model', default='groq')
    active = fields.Boolean(default=True)
