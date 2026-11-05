# 🌐 Ecossistema Multiagente de IA para Gestão de Projetos (v3.0.0)

[![Odoo 19](https://img.shields.io/badge/Odoo-19-875A7B.svg)](https://www.odoo.com/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.175.0-FF6B6B.svg)](https://github.com/joaomdmoura/crewAI)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-44%20Passed-success.svg)]()
[![Certification](https://img.shields.io/badge/Certification-30%2F30-brightgreen.svg)]()

Este repositório contém o código-fonte do ecossistema multiagente de Inteligência Artificial desenvolvido para a dissertação do Mestrado em Engenharia Informática e de Computadores (MEIC) do Instituto Superior Técnico (IST).

O objetivo principal é integrar agentes autónomos baseados em LLMs diretamente na plataforma ERP **Odoo 19**, automatizando o planeamento, execução e tomada de decisão na gestão de projetos.

---

## ✨ Funcionalidades Principais

* **6 Agentes Especializados:** Project Manager, Team Member, Reporting, Diagram, Planning e Risk.
* **20 Ferramentas Idempotentes:** CRUD completo (Projetos, Tarefas, Stages), análise de riscos, priorização, geração de diagramas Mermaid e Macros de engenharia (ex: `setup_agile_project`).
* **Router Híbrido (Regex + LLM):** ~90% dos comandos comuns são resolvidos localmente (latência de 0.05s) sem gastar tokens de LLM. O fallback para o CrewAI + Groq (LLM) só acontece para pedidos complexos.
* **BackOffice de Governança:** Menu nativo no Odoo para gestão dinâmica de *System Prompts* (Templates), permitindo alterar a personalidade dos agentes sem tocar no código.
* **Controlo de Acesso (RBAC) em 2 Camadas:** Validação na interface Odoo e verificação *server-side* (FastAPI) para prevenir falsificação de identidade (*spoofing*).
* **Hard Guardrails e Workspaces:** Bloqueio de segurança a nível de código (ex: palavras proibidas) e gestão de agentes contextuais diretamente dentro de cada Projeto/Workspace.
* **Cache Inteligente (FastAPI):** Sistema de cache em memória (TTL de 5 minutos) com *invalidação automática* em operações de escrita para garantir dados sempre frescos.
* **Blindagem Thread-Safe:** Conexão XML-RPC isolada por thread (`threading.local()`) para suportar pedidos simultâneos sem falhas.

## 🏗️ Arquitetura

O sistema assenta numa arquitetura de 3 camadas:
1. **Interface:** Módulo Odoo 19 (HTML/CSS/JS) acessível via browser.
2. **Orquestração:** Microserviço FastAPI (Python 3.12) + CrewAI (0.175.0) + Groq (qwen/qwen3.8-27b).
3. **Base de Dados:** PostgreSQL 18.

*(Para visualizar o diagrama completo, consulte o ficheiro `docs/specs/` ou o relatório PIC2.)*

## 🚀 Quick Start

### Pré-requisitos
* Odoo 19 (Community) instalado e a correr na porta `8069`.
* Python 3.12 e PostgreSQL 18.
* Chave de API da Groq (`GROQ_API_KEY`).

### Configuração
1. Clonar o repositório:
   `git clone https://github.com/Denispy1998/project-agent-system-odoo.git`
2. Copiar o `.env.example` para `.env` e preencher as tuas credenciais.
3. Instalar dependências e arrancar o FastAPI:
   `pip install -r agent/agents_api/requirements.txt`
   `uvicorn agents_api.main:app --host 127.0.0.1 --port 8001`

## 🧪 Qualidade e Testes

O ecossistema é validado por uma suíte rigorosa de testes:
* **44 Testes Unitários (Pytest):** Cobrem o router, ferramentas e orquestrador.
* **16 Testes de Integração (Smoke Test):** Validam a comunicação com o Odoo.
* **Certificação End-to-End (30/30):** Testa os 6 agentes, RBAC, Cache, Guardrails e geração de diagramas.
* **CI/CD:** GitHub Actions corre o Lint (Ruff) e os testes a cada push.

## 📚 Documentação Adicional
* 📄 [Relatório Técnico e Limitações](docs/LIMITATIONS.md)
* 📜 [Changelog de Engenharia (T1-T15)](docs/CHANGELOG_TECHNICAL.md)
* 📐 [Especificações RSL/ASL](docs/specs/)

## 👨‍🎓 Autor
**Denilson Fragoso Da Silva Santos** (IST-1113142)
* Orientador: Prof. Alberto Rodrigues da Silva
* Instituto Superior Técnico, Universidade de Lisboa
* Ano Letivo: 2026/2027
