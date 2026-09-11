# -*- coding: utf-8 -*-
{
    'name': 'Ecossistema IA — Gestão de Projetos',
    'version': '19.0.1.0.0',
    'category': 'Project',
    'summary': 'Agente IA conversacional integrado no Odoo 19 para gestão de projetos',
    'description': """
Ecossistema IA para Gestão de Projetos
=======================================

Sistema multiagente que permite interagir com projetos, tarefas e stages
em linguagem natural, integrado na plataforma Odoo 19.

Funcionalidades principais:
---------------------------
* Criação de projetos com tarefas via linguagem natural
* Gestão de stages (criação automática ao mover tarefas)
* Movimentação de tarefas (em lote ou individual)
* Análise de riscos e priorização automática
* Geração de resumos detalhados
* Dashboard com KPIs e gráficos interativos
* Exportação de relatórios PDF e CSV
* Sistema de permissões (Gestor vs. Membro de Equipa)

Autor: Denilson Fragoso Da Silva Santos (IST-1113142)
Orientador: Prof. Alberto Rodrigues da Silva
Instituição: Instituto Superior Técnico, Universidade de Lisboa
    """,
    'author': 'Denilson Fragoso Da Silva Santos',
    'website': 'https://github.com/Denispy1998/project-agent-system-odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'project', 'mail', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
