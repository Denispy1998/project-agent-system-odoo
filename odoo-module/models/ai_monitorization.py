# -*- coding: utf-8 -*-
from odoo import models, fields

class AIMonitorization(models.Model):
    _name = 'ai.monitorization'
    _description = 'AI Agent Monitorization Logs'

    agent_id = fields.Many2one('ai.agent', string='Agent', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Organization', required=True, default=lambda self: self.env.company)
    
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
    tokens_used = fields.Integer(string='Tokens Used')
    execution_time = fields.Float(string='Execution Time (s)')
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
    ], string='Status', required=True)
    
    log_message = fields.Text(string='Log/Error Message')
