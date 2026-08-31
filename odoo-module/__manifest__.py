{
    'name': 'Ecossistema IA - Gestão de Projetos',
    'version': '1.0',
    'category': 'Project',
    'summary': 'Agente IA com Linguagem Natural e Controlo de Acessos',
    'author': 'Denilson Fragoso Da Silva Santos',
    'license': 'LGPL-3',
    'depends': ['base', 'project', 'mail'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'post_init': 'create_groups',  # chama a função create_groups no __init__.py
}
