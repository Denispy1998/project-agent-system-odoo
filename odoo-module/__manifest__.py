# -*- coding: utf-8 -*-
{
    'name': 'AI Project Management Ecosystem',
    'version': '2.0.0',
    'category': 'Project',
    'summary': 'Multi-agent AI ecosystem for project management (Odoo 19)',
    'description': """
AI Project Management Ecosystem v2.0
=====================================
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
        'security/ir.model.access.csv',
        'views/menu.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
