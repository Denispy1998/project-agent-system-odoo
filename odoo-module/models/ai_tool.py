# -*- coding: utf-8 -*-
from odoo import models, fields

class AITool(models.Model):
    _name = 'ai.tool'
    _description = 'AI Tool (MCP Server or Built-in)'

    name = fields.Char(string='Tool Name', required=True, help="e.g., create_jira_issue, list_projects")
    description = fields.Text(string='Description')
    tool_type = fields.Selection([
        ('mcp_server', 'MCP Server'),
        ('built_in', 'Built-in Function'),
    ], string='Type', default='mcp_server', required=True)
    
    mcp_server_url = fields.Char(string='MCP Server URL', help="URL of the MCP Server exposing this tool.")
    company_id = fields.Many2one('res.company', string='Organization', required=True, default=lambda self: self.env.company)
    
    agent_ids = fields.Many2many('ai.agent', 'ai_agent_tool_rel', 'tool_id', 'agent_id', string='Agents using this tool')
    active = fields.Boolean(default=True)
