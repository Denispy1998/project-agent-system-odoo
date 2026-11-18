# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AIWorkspace(models.Model):
    _name = 'ai.workspace'
    _description = 'AI Workspace (Project/Project Workspace)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Workspace Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Organization', required=True, default=lambda self: self.env.company)
    description = fields.Text(string='Description')
    
    project_id = fields.Many2one('project.project', string='Odoo Project', help="The Odoo project linked to this workspace.")
    
    agent_ids = fields.One2many('ai.agent', 'workspace_id', string='Agents')
    session_ids = fields.One2many('ai.session', 'workspace_id', string='Chat Sessions')
    
    active = fields.Boolean(default=True)
