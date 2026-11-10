#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script universal de configuração de utilizadores e grupos para o
Ecossistema IA. Funciona em qualquer instalação Odoo 19 sem depender de IDs fixos.
"""

import xmlrpc.client
import sys

# ========== CONFIGURAÇÃO ==========
ODOO_URL = "http://localhost:8069"
ODOO_DB = "odoo"
ODOO_USER = "admin"
ODOO_PASSWORD = "admin"

# ========== CONEXÃO ==========
try:
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        print("❌ Falha na autenticação. Verifica as credenciais.")
        sys.exit(1)
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    print(f"✅ Conectado ao Odoo (uid={uid})")
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
    sys.exit(1)


# ========== FUNÇÕES AUXILIARES ==========

def get_or_create_group(group_name: str) -> int:
    """Procura o grupo pelo nome; se não existir, cria-o. Devolve o ID."""
    group_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.groups', 'search',
        [[('name', '=', group_name)]]
    )
    if group_ids:
        print(f"   → Grupo '{group_name}' encontrado (ID {group_ids[0]})")
        return group_ids[0]

    # Criar o grupo
    print(f"   → Grupo '{group_name}' não existe. A criar...")
    new_id = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.groups', 'create',
        [{'name': group_name}]
    )
    print(f"   ✅ Grupo '{group_name}' criado (ID {new_id})")
    return new_id


def get_or_create_user(login: str, name: str, email: str, password: str) -> int:
    """Procura o utilizador pelo login; se não existir, cria-o. Devolve o ID."""
    user_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.users', 'search',
        [[('login', '=', login)]]
    )
    if user_ids:
        user_id = user_ids[0]
        # Atualiza a password
        models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.users', 'write',
            [[user_id], {'password': password}]
        )
        print(f"   → Utilizador '{login}' já existia (ID {user_id}). Password atualizada.")
        return user_id

    # Criar utilizador
    user_id = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.users', 'create',
        [{
            'name': name,
            'login': login,
            'password': password,
            'email': email,
        }]
    )
    print(f"   ✅ Utilizador '{login}' criado (ID {user_id})")
    return user_id


def add_user_to_group(user_id: int, group_id: int) -> None:
    """Adiciona um utilizador a um grupo (usa o campo 'group_ids' correto do Odoo 19)."""
    models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.users', 'write',
        [[user_id], {'group_ids': [(4, group_id)]}]
    )


# ========== PROGRAMA PRINCIPAL ==========

def main():
    print("\n🔧 A configurar grupos...")
    group_manager = get_or_create_group("Gestor de Projeto")
    group_member = get_or_create_group("Membro de Equipa")

    print("\n🔧 A configurar admin como Gestor de Projeto...")
    add_user_to_group(uid, group_manager)
    print("   ✅ Admin adicionado ao grupo 'Gestor de Projeto'")

    print("\n🔧 A criar utilizadores de teste...")
    print("   • joao (Membro de Equipa)")
    joao_id = get_or_create_user('joao', 'Joao Silva', 'joao@example.com', 'joao')
    add_user_to_group(joao_id, group_member)
    print("   ✅ joao adicionado ao grupo 'Membro de Equipa'")

    print("   • jose (Membro de Equipa)")
    jose_id = get_or_create_user('jose', 'Jose Silva', 'jose@example.com', 'jose')
    add_user_to_group(jose_id, group_member)
    print("   ✅ jose adicionado ao grupo 'Membro de Equipa'")

    print("\n" + "="*60)
    print("🎯 CONFIGURAÇÃO CONCLUÍDA")
    print("="*60)
    print(f"   • Gestor de Projeto → admin (uid={uid})")
    print(f"   • Membro de Equipa  → joao (uid={joao_id}), jose (uid={jose_id})")
    print("\n   Logins de teste:")
    print("   • admin / admin  (Gestor)")
    print("   • joao  / joao   (Membro)")
    print("   • jose  / jose   (Membro)")
    print("="*60)


if __name__ == "__main__":
    main()
