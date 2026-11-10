# 🌐 Ecossistema Multiagente de IA para Gestão de Projetos (v3.2.0)

[![Odoo 19](https://img.shields.io/badge/Odoo-19-875A7B.svg)](https://www.odoo.com/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.175.0-FF6B6B.svg)](https://github.com/joaomdmoura/crewAI)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg)](https://fastapi.tiangolo.com/)
[![Jira](https://img.shields.io/badge/Jira-REST_API-0052CC.svg)](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
[![Tests](https://img.shields.io/badge/Tests-44%20Passed-success.svg)]()
[![Certification](https://img.shields.io/badge/Certification-30%2F30-brightgreen.svg)]()

Este repositório contém o código-fonte do ecossistema multiagente de Inteligência Artificial desenvolvido para a dissertação do Mestrado em Engenharia Informática e de Computadores (MEIC) do Instituto Superior Técnico (IST).

O objetivo principal é integrar agentes autónomos baseados em LLMs diretamente na plataforma ERP **Odoo 19**, automatizando o planeamento, execução e tomada de decisão na gestão de projetos, com integração nativa ao **Jira**.

---

## ✨ Funcionalidades Principais

* **6 Agentes Especializados:** Project Manager, Team Member, Reporting, Diagram, Planning e Risk.
* **22 Ferramentas Idempotentes:** 20 ferramentas Odoo (CRUD, riscos, diagramas, macros) + 2 ferramentas Jira (listar projetos, criar issues).
* **Multi-LLM Integrado (Gratuito):** Suporte nativo para **Groq** (Qwen 3.8), **Google Gemini** (3.6 Flash) e **OpenRouter** (Nemotron 3 Ultra), com fallback automático em caso de falha ou rate limit.
* **Router Híbrido (Regex + LLM):** ~90% dos comandos comuns são resolvidos localmente (latência de 0.05s) sem gastar tokens de LLM. O fallback para o CrewAI só acontece para pedidos complexos.
* **BackOffice de Governança:** Menu nativo no Odoo para gestão dinâmica de *System Prompts* (Templates).
* **Controlo de Acesso (RBAC) em 2 Camadas:** Validação na interface Odoo e verificação *server-side* (FastAPI).
* **Cache Inteligente:** Sistema de cache em memória (TTL de 5 min) com *invalidação automática* em operações de escrita.
* **Blindagem Thread-Safe:** Conexão XML-RPC isolada por thread (`threading.local()`).

## 🏗️ Arquitetura

O sistema assenta numa arquitetura de 3 camadas:
1. **Interface:** Módulo Odoo 19 (HTML/CSS/JS) acessível via browser.
2. **Orquestração:** Microserviço FastAPI (Python 3.12) + CrewAI (0.175.0) + Multi-LLM (Groq, Gemini, OpenRouter).
3. **Base de Dados:** PostgreSQL 18.

## 🚀 Quick Start

### Pré-requisitos
* Odoo 19 (Community) a correr na porta `8069`.
* Python 3.12 e PostgreSQL 18.
* Chaves de API para: `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`.
* Credenciais do Jira: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`.

### Configuração
1. Clonar o repositório: `git clone https://github.com/Denispy1998/project-agent-system-odoo.git`
2. Copiar o `.env.example` para `.env` e preencher as credenciais.
3. Instalar dependências:
   `pip install -r agent/agents_api/requirements.txt`
4. Configurar utilizadores de teste:
   `python scripts/setup_users.py`
5. Arrancar o FastAPI:
   `uvicorn agents_api.main:app --host 127.0.0.1 --port 8001`

## 🧪 Qualidade e Testes

* **44 Testes Unitários (Pytest):** Cobrem o router, ferramentas e orquestrador.
* **16 Testes de Integração (Smoke Test):** Validam a comunicação com o Odoo.
* **Certificação End-to-End (30/30):** Testa os 6 agentes, RBAC, Cache, Guardrails e diagramas.
* **CI/CD:** GitHub Actions corre o Lint e os testes a cada push.

## 📚 Documentação Adicional
* 📄 [Limitações e Rigor Científico](docs/LIMITATIONS.md)
* 📜 [Changelog de Engenharia](docs/CHANGELOG_TECHNICAL.md)
* 📐 [Especificações RSL/ASL](docs/specs/)

## 👨‍🎓 Autor
**Denilson Fragoso Da Silva Santos** (IST-1113142)
* Orientador: Prof. Alberto Rodrigues da Silva
* Instituto Superior Técnico, Universidade de Lisboa
* Ano Letivo: 2026/2027
