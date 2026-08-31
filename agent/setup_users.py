#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar/utilizadores no Odoo 19 com password funcional.
Usa XML-RPC, sem dependências externas.
"""

import xmlrpc.client

ODOO_URL = "http://localhost:8069"
ODOO_DB = "odoo"
ODOO_USER = "admin"
ODOO_PASSWORD = "admin"

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
if not uid:
    raise ConnectionError("Falha na autenticação com o Odoo.")

models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

def criar_ou_atualizar(login, nome, email, password, grupo_id=33):
    # Verifica se o utilizador já existe
    user_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'res.users', 'search', [[('login', '=', login)]])
    if user_ids:
        user_id = user_ids[0]
        # Atualiza a password
        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'res.users', 'write', [[user_id], {'password': password}])
        print(f"✅ Utilizador '{login}' atualizado (password).")
    else:
        # Cria novo utilizador
        user_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'res.users', 'create', [{
            'name': nome,
            'login': login,
            'password': password,
            'email': email,
        }])
        print(f"✅ Utilizador '{login}' criado (ID {user_id}).")
    # Atribui grupo Membro de Equipa (ID 33)
    models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'res.users', 'write', [[user_id], {'groups_id': [(4, grupo_id)]}])
    print(f"✅ Grupo 'Membro de Equipa' atribuído a '{login}'.")

if __name__ == "__main__":
    criar_ou_atualizar('joao', 'Joao Silva', 'joao@example.com', 'joao')
    criar_ou_atualizar('jose', 'Jose Silva', 'jose@example.com', 'jose')
    print("\n🎯 Processo concluído. Logins: joao/joao, jose/jose")
