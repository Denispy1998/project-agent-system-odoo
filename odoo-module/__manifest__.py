# -*- coding: utf-8 -*-
{
    'name': 'AI Project Management Ecosystem',
    'version': '19.0.4.0.0',
    'category': 'Project',
    'summary': 'Multi-agent AI ecosystem for project management (Odoo 19)',
    'description': """
AI Project Management Ecosystem v4.0.0 (MCP & Multi-Tenant)
=====================================================================
Multi-agent AI ecosystem for project management with:
- CrewAI orchestrator (Project Manager, Team Member, Reporting, Diagram agents)
- Multi-session chat with persistent context
- Model selection (Groq / OpenAI / Anthropic)
- Dashboard with Chart.js
- PDF and CSV export
- Weekly automated ecosystem reports

Author: Denilson Fragoso Da Silva Santos (IST-1113142)
    """,
    'author': 'Denilson Fragoso Da Silva Santos',
    'website': 'https://github.com/Denispy1998/project-agent-system-odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'project', 'mail', 'website'],
    'data': [
        'security/groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/task_views.xml',
        'views/project_project_views.xml',
        'views/ai_template_views.xml',
        'views/ai_workspace_views.xml',
        'views/ai_agent_views.xml',
        'views/ai_tool_views.xml',
        'views/ai_monitorization_views.xml',
        'views/ai_menu_views.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
