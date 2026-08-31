from . import controllers

def create_groups(cr, registry):
    """
    Função chamada após a instalação para criar os grupos de utilizadores.
    """
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Verifica se os grupos já existem
    group_manager = env['res.groups'].search([('name', '=', 'Gestor de Projeto')])
    group_member = env['res.groups'].search([('name', '=', 'Membro de Equipa')])

    if not group_manager:
        group_manager = env['res.groups'].create({
            'name': 'Gestor de Projeto',
            'implied_ids': [(4, env.ref('base.group_user').id)],
        })
        print("✅ Grupo 'Gestor de Projeto' criado.")

    if not group_member:
        group_member = env['res.groups'].create({
            'name': 'Membro de Equipa',
            'implied_ids': [(4, env.ref('base.group_user').id)],
        })
        print("✅ Grupo 'Membro de Equipa' criado.")
