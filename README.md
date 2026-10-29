<div align="center">
  <h1>🤖 AI Project Management Ecosystem (v2.8.0)</h1>
  <p><strong>Planeamento, Execução e Tomada de Decisão com Agentes de IA Integrados no Odoo 19</strong></p>

  ![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67?style=for-the-badge&logo=odoo)
  ![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)
  ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)
  ![CrewAI](https://img.shields.io/badge/CrewAI-0.175-FF6B6B?style=for-the-badge)
  ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?style=for-the-badge&logo=postgresql)
  ![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions)
  ![Status](https://img.shields.io/badge/Status-CERTIFIED_30%2F30-success?style=for-the-badge)
</div>

---

## 📌 Sobre o Projeto
Este repositório contém o ecossistema multiagente de Inteligência Artificial desenvolvido no âmbito da dissertação de Mestrado (MEIC) no Instituto Superior Técnico. O sistema integra um agente conversacional (CrewAI + Groq) com o ERP Odoo 19, permitindo a gestão de projetos através de linguagem natural, com elevada performance, segurança e governança.

### 🚀 Principais Funcionalidades (v2.8.0)
- **Hybrid Router:** Comandos simples resolvidos por Regex (0.05s) e comandos complexos delegados ao LLM (2-5s).
- **17+ Ferramentas Idempotentes:** CRUD de projetos, tarefas e stages; análise de riscos; diagramas Mermaid; Macros de engenharia (ex: `setup_agile_project`).
- **BackOffice Nativo no Odoo:** Gestão dinâmica de *System Prompts* (Templates) e instanciação de agentes.
- **Colaboração Multiagente:** 6 agentes especializados (Project Manager, Team Member, Reporting, Diagram, **Planning**, **Risk**).
- **Segurança RBAC (2 Camadas):** Verificação de permissões no Odoo e *server-side* no FastAPI.
- **Automação:** Relatório semanal automático por email (Cron Job).
- **Interface Otimizada:** Chat multi-sessão, dashboards interativos com Chart.js e exportação PDF/CSV.

---

## 🏗️ Arquitetura do Sistema

O ecossistema segue uma arquitetura de três camadas, complementada por um router híbrido interno:

1. **Interface (Odoo 19):** UI em HTML5/CSS3/JS, chat multi-sessão e dashboards.
2. **Orquestração (FastAPI + CrewAI):** Microserviço que interpreta a linguagem natural e coordena os agentes.
3. **Dados (PostgreSQL 18):** Persistência nativa do Odoo e estado das sessões de IA.

> 📌 *Os diagramas detalhados da arquitetura (Figuras 1 e 2 do relatório PIC2) estão disponíveis no documento oficial submetido no Fénix.*

---

## 🛠️ Tecnologias Utilizadas

| Componente | Tecnologia | Versão | Justificação |
| :--- | :--- | :--- | :--- |
| **Plataforma** | Odoo Community | 19 | ERP com módulo de projetos e XML-RPC |
| **Orquestração** | CrewAI | 0.175.0 | Framework multiagente com ferramentas |
| **LLM Padrão** | Groq (qwen3.8-27b) | max_tokens=512 | Rápido, gratuito e de alta performance |
| **Microserviço** | FastAPI | 0.115.6 | Framework web de alto desempenho |
| **Backend** | Python | 3.12 | Linguagem do Odoo e CrewAI |
| **Base de Dados** | PostgreSQL | 18 | Sistema de gestão do Odoo |
| **Frontend** | HTML5, CSS3, JS | — | Interface leve e responsiva |
| **Diagramas** | Mermaid.js | — | Renderização SVG no chat |
| **CI/CD** | GitHub Actions | — | Lint + Pytest automáticos |

---

## 🚦 Como Executar o Projeto

### Pré-requisitos
- WSL2 (Ubuntu 22.04+) ou Linux
- Odoo 19 instalado (`/opt/odoo/odoo19`)
- PostgreSQL 18
- Python 3.12 (venv_agents)

### Instalação e Arranque
```bash
# 1. Clonar o repositório
git clone https://github.com/Denispy1998/project-agent-system-odoo.git
cd project-agent-system-odoo

# 2. Configurar o ambiente virtual (venv_agents)
python3.12 -m venv venv_agents
source venv_agents/bin/activate
pip install -r requirements.txt

# 3. Configurar as variáveis de ambiente (.env)
# (Adicionar GROQ_API_KEY, ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD)

# 4. Iniciar os serviços
bash ~/start_all.sh
```

---

## 🧪 Testes e Certificação

O ecossistema é validado de forma contínua através de:
- **44 Testes Unitários:** Lógica do router, ferramentas e helpers.
- **16 Testes de Integração (Smoke Test):** UI, API, RBAC e LLM.
- **30 Pontos de Certificação End-to-End:** Validação completa do sistema em execução.
- **Testes Enterprise:** Validação de idempotência das Macros e colaboração entre agentes.

Para executar a certificação:
```bash
source venv_agents/bin/activate
python tests/certify.py
```

---

## 📚 Documentação Adicional

- [Especificações RSL v3.2 e ASL v3.3](docs/specs/)
- [Guia de Limitações (L1-L8)](docs/LIMITATIONS.md)
- [Casos de Estudo Técnicos (T1-T11)](docs/CHANGELOG_TECHNICAL.md)

---

## 👨‍💻 Autor

**Denilson Fragoso Da Silva Santos** (IST-1113142)
*Mestrado em Engenharia Informática e de Computadores (MEIC)*
Instituto Superior Técnico, Universidade de Lisboa
*Orientador: Prof. Alberto Rodrigues da Silva*

---
<div align="center">
  <sub>Desenvolvido com ❤️ para a dissertação MEIC 2026/2027</sub>
</div>