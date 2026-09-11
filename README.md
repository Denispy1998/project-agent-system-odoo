# 🤖 Ecossistema IA — Gestão de Projetos

**Dissertação de Mestrado em Engenharia Informática e de Computadores**
Instituto Superior Técnico, Universidade de Lisboa · 2026/2027

| | |
|---|---|
| **Autor** | Denilson Fragoso Da Silva Santos (IST-1113142) |
| **Orientador** | Prof. Alberto Rodrigues da Silva |
| **Repositório** | https://github.com/Denispy1998/project-agent-system-odoo |

---

## 📖 Descrição

Sistema multiagente integrado no **Odoo 19** que permite gerir projetos, tarefas e stages através de **linguagem natural em português**. O agente interpreta comandos do utilizador, executa as operações no Odoo via XML-RPC e devolve respostas formatadas em tempo real.

O ecossistema disponibiliza 14 ferramentas estruturadas, um dashboard interativo com gráficos (Chart.js), sub-dashboards por projeto, relatórios PDF profissionais e exportação CSV.

---

## ✨ Funcionalidades

### Comandos suportados (14 ferramentas)

| # | Comando | Descrição |
|---|---------|-----------|
| 1 | `Lista os projetos existentes` | Lista todos os projetos com contagem de tarefas |
| 2 | `Cria o projeto "Nome" com tarefas A, B, C` | Cria um projeto e respetivas tarefas |
| 3 | `Adiciona a tarefa "X" ao projeto "Nome"` | Adiciona uma tarefa a projeto existente |
| 4 | `Lista as tarefas do projeto "Nome"` | Lista tarefas com respetivo stage |
| 5 | `Lista os stages do projeto "Nome"` | Lista stages configurados |
| 6 | `Cria o stage "REVIEW" com sequência 15 para o projeto "Nome"` | Cria stage personalizado |
| 7 | `Move todas as tarefas do projeto "Nome" para o stage "REVIEW"` | Movimentação em lote (cria stage se não existir) |
| 8 | `Move a tarefa "A" do projeto "Nome" para o stage "FASE_2"` | Movimentação individual (cria stage se não existir) |
| 9 | `Elimina a tarefa "A" do projeto "Nome"` | Elimina tarefa |
| 10 | `Elimina o stage "REVIEW" do projeto "Nome"` | Elimina stage (apenas se estiver vazio) |
| 11 | `Elimina o projeto "Nome"` | Elimina projeto e todas as tarefas |
| 12 | `Analisa os riscos do projeto "Nome"` | Calcula probabilidade de atraso |
| 13 | `Prioriza as tarefas do projeto "Nome"` | Ordena por criticidade (sem stage primeiro) |
| 14 | `Dá-me um resumo do projeto "Nome"` | Gera resumo com distribuição por stages |

### Outros componentes

- **Interface de chat** — design moderno, responsivo, com exemplos de comandos
- **Dashboard geral** — KPIs, 4 gráficos (doughnut, bar, pie, horizontal)
- **Sub-dashboards por projeto** — tabela de tarefas, evolução 30 dias, 3 gráficos
- **Relatórios PDF** — cabeçalho, tabela formatada, análise de riscos
- **Exportação CSV** — ficheiro com cabeçalho informativo e separador `;`
- **Sistema de feedback** — avaliação do chat (0-10) com modal interativo
- **Controlo de acessos** — grupos "Gestor de Projeto" e "Membro de Equipa"

---

## 🛠️ Tecnologias

| Componente | Tecnologia | Versão |
|-----------|------------|--------|
| Plataforma | Odoo Community | 19.0 |
| Backend | Python | 3.14 |
| Base de dados | PostgreSQL | 18 |
| LLM | Groq (openai/gpt-oss-20b) | — |
| Frontend | HTML5, CSS3, JavaScript | — |
| Gráficos | Chart.js | 4.x |
| PDF | ReportLab | 4.x |
| Integração | XML-RPC | — |

---

## 🏗️ Arquitetura

```
┌──────────────────────────────────┐
│        Utilizador (Browser)      │
└────────────────┬─────────────────┘
                 │ HTTP
                 ▼
┌──────────────────────────────────┐
│       Odoo 19 + Módulo IA        │
│  ┌────────────────────────────┐  │
│  │  Controllers (chatbot.py)  │  │
│  │  Rotas: /assistente/*      │  │
│  └──────────────┬─────────────┘  │
└─────────────────┼────────────────┘
                  │ XML-RPC
                  ▼
┌──────────────────────────────────┐
│    Agente IA (chat_agent.py)     │
│  ┌──────────────┐ ┌────────────┐ │
│  │Fallback Regex│ │ Groq LLM   │ │
│  └──────┬───────┘ └─────┬──────┘ │
│         └───────┬───────┘        │
│                 ▼                │
│         14 Ferramentas           │
└──────────────────────────────────┘
```

---

## 📁 Estrutura do Repositório

```
project-agent-system-odoo/
├── agent/                          # Agente IA
│   ├── chat_agent.py               # 14 ferramentas + fallback + LLM
│   └── setup_users.py              # Script universal de utilizadores
├── odoo-module/                    # Módulo Odoo
│   ├── __manifest__.py
│   ├── __init__.py
│   ├── controllers/
│   │   ├── chatbot.py              # Rotas HTTP + lógica de integração
│   │   └── dashboard_utils.py      # Cálculo de KPIs
│   ├── security/
│   │   ├── groups.xml
│   │   └── ir.model.access.csv
│   ├── static/description/
│   │   └── icon.png
│   └── views/
│       └── menu.xml                # Menus do Odoo
├── docs/                           # Documentação adicional
└── README.md
```

---

## 🚀 Instalação Rápida

### Pré-requisitos

- Windows com **WSL 2** (Ubuntu 24.04 ou superior)
- Python 3.14
- PostgreSQL 18
- Odoo Community 19
- Chave API Groq (gratuita em https://console.groq.com)

### 1. Clonar o repositório

```bash
cd ~
git clone https://github.com/Denispy1998/project-agent-system-odoo.git
cd project-agent-system-odoo
```

### 2. Configurar o agente

```bash
mkdir -p ~/project-agent-system
cp agent/chat_agent.py ~/project-agent-system/
cp agent/setup_users.py ~/project-agent-system/
cd ~/project-agent-system
```

Cria o ficheiro `.env`:

```bash
nano .env
```

Conteúdo:

```env
GROQ_API_KEY=gsk_...tua_chave_aqui
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin
```

### 3. Copiar o módulo para o Odoo

```bash
sudo cp -r odoo-module /opt/odoo/odoo19/addons/meu_assistente_ia
sudo chown -R $USER:$USER /opt/odoo/odoo19/addons/meu_assistente_ia
```

### 4. Instalar dependências Python no venv do Odoo

```bash
cd /opt/odoo/odoo19
source ../venv-19/bin/activate
pip install groq python-dotenv reportlab
```

### 5. Instalar os módulos base e o módulo IA

```bash
# Módulos base (obrigatórios)
python odoo-bin -c ~/odoo19.conf -d odoo -i project,mail,website --stop-after-init

# Módulo do ecossistema
python odoo-bin -c ~/odoo19.conf -d odoo -i meu_assistente_ia --stop-after-init
```

### 6. Criar utilizadores de teste

```bash
cd ~/project-agent-system
python3 -m venv venv
source venv/bin/activate
pip install groq python-dotenv
python setup_users.py
```

O script cria automaticamente:
- Grupo **Gestor de Projeto** (se não existir)
- Grupo **Membro de Equipa** (se não existir)
- Utilizador **joao** (senha: joao) — Membro de Equipa
- Utilizador **jose** (senha: jose) — Membro de Equipa
- Associa o **admin** ao grupo Gestor de Projeto

### 7. Arrancar o Odoo

```bash
cd /opt/odoo/odoo19
source ../venv-19/bin/activate
python odoo-bin -c ~/odoo19.conf
```

Acede a `http://localhost:8069` no browser.

---

## 🎯 Como Aceder ao Ecossistema

### A partir do menu principal do Odoo

Depois de fazer login em `http://localhost:8069`:

1. **Barra superior** → aparece o ícone **"Ecossistema IA"**
2. Clicar no ícone abre o menu com 5 submenus:

| Submenu | Rota | Descrição |
|---------|------|-----------|
| 🏠 **Início** | `/assistente` | Página inicial com KPIs e cards de navegação |
| 💬 **Chat** | `/assistente/page` | Interface de conversação com o agente IA |
| 📊 **Dashboard** | `/assistente/dashboard` | Gráficos e estatísticas globais |
| 📁 **Projetos** | `/assistente/projetos` | Lista de projetos (acesso aos sub-dashboards) |
| 👤 **Meus Projetos** | `/assistente/meus-projetos` | Projetos e tarefas criados pelo utilizador |

### Acesso direto via URL

| Página | URL |
|--------|-----|
| Página inicial | `http://localhost:8069/assistente` |
| Chat | `http://localhost:8069/assistente/page` |
| Dashboard geral | `http://localhost:8069/assistente/dashboard` |
| Lista de projetos | `http://localhost:8069/assistente/projetos` |
| Sub-dashboard de projeto | `http://localhost:8069/assistente/projeto/<id>` |
| Meus projetos | `http://localhost:8069/assistente/meus-projetos` |
| Relatório PDF | `http://localhost:8069/assistente/relatorio/<id>` |
| Exportar CSV | `http://localhost:8069/assistente/exportar/<id>` |

---

## 🔐 Credenciais de Teste

| Utilizador | Password | Papel | Acesso |
|-----------|----------|-------|--------|
| `admin` | `admin` | Gestor de Projeto | Total (criar, editar, eliminar) |
| `joao` | `joao` | Membro de Equipa | Apenas leitura + análise |
| `jose` | `jose` | Membro de Equipa | Apenas leitura + análise |

### Diferenças de permissão

| Ação | Admin | Membro |
|------|:-----:|:------:|
| Listar projetos/tarefas | ✅ | ✅ |
| Analisar riscos | ✅ | ✅ |
| Priorizar tarefas | ✅ | ✅ |
| Ver resumos | ✅ | ✅ |
| Criar projeto/tarefa | ✅ | ❌ |
| Mover tarefas/stages | ✅ | ❌ |
| Eliminar artefactos | ✅ | ❌ |

---

## 📊 Exemplos de Utilização

### Criar projeto com tarefas

```
Utilizador: Cria o projeto "Website" com tarefas Design, Dev, Testes
Agente: SUCESSO: Projeto 'Website' (ID 12) criado com 3 tarefas.
```

### Mover tarefas (criação automática de stage)

```
Utilizador: Move todas as tarefas do projeto "Website" para o stage "SPRINT_1"
Agente: SUCESSO: 3 tarefas movidas para 'SPRINT_1'.
```

### Análise de riscos

```
Utilizador: Analisa os riscos do projeto "Website"
Agente: Análise de riscos para o projeto 'Website':
  • Total de tarefas: 3
  • Tarefas sem stage definido: 0
  • Probabilidade estimada de atraso: 0.0%
  • Recomendação: O projeto parece estar bem organizado.
```

### Permissão negada

```
Utilizador (joao): Cria o projeto "Teste"
Agente: Permissão negada. Apenas gestores de projeto podem criar projetos.
```

---

## 🧪 Comandos de Teste (checklist)

### Administrador (admin)

- [ ] `Lista os projetos existentes`
- [ ] `Cria o projeto "TesteAdmin" com tarefas A, B, C`
- [ ] `Adiciona a tarefa "D" ao projeto "TesteAdmin"`
- [ ] `Lista as tarefas do projeto "TesteAdmin"`
- [ ] `Cria o stage "REVIEW" com sequência 10 para o projeto "TesteAdmin"`
- [ ] `Lista os stages do projeto "TesteAdmin"`
- [ ] `Move todas as tarefas do projeto "TesteAdmin" para o stage "REVIEW"`
- [ ] `Move a tarefa "A" do projeto "TesteAdmin" para o stage "NovoStage"`
- [ ] `Elimina a tarefa "B" do projeto "TesteAdmin"`
- [ ] `Elimina o stage "REVIEW" do projeto "TesteAdmin"`
- [ ] `Elimina o projeto "TesteAdmin"`
- [ ] `Analisa os riscos do projeto "Vendas"`
- [ ] `Prioriza as tarefas do projeto "Vendas"`
- [ ] `Dá-me um resumo do projeto "Vendas"`

### Membro de Equipa (joao/jose)

- [ ] `Lista os projetos existentes` → OK
- [ ] `Cria o projeto "TesteMembro"` → Permissão negada
- [ ] `Adiciona a tarefa "X" ao projeto "Vendas"` → Permissão negada
- [ ] `Elimina o projeto "Teste"` → Permissão negada
- [ ] `Analisa os riscos do projeto "Vendas"` → OK
- [ ] `Prioriza as tarefas do projeto "Vendas"` → OK
- [ ] `Dá-me um resumo do projeto "Vendas"` → OK

---

## 🐛 Resolução de Problemas

### Agente indisponível

Verifica se o `groq` e `python-dotenv` estão instalados no venv do Odoo:
```bash
cd /opt/odoo/odoo19
source ../venv-19/bin/activate
pip list | grep -E "(groq|dotenv)"
```

### Erro de autenticação no login

Executa o script universal de utilizadores:
```bash
cd ~/project-agent-system
python setup_users.py
```

### Módulo não aparece nos menus

```bash
python odoo-bin -c ~/odoo19.conf -u meu_assistente_ia --stop-after-init
```

### Logs em tempo real

```bash
tail -f ~/odoo.log | grep -E "(⏱️|👤|📩|✅|❌)"
```

---

## 📚 Documentação Adicional

- [`docs/`](docs/) — documentação técnica adicional
- [Dissertação completa] — disponível no repositório institucional do IST
- [Groq API](https://console.groq.com/docs) — documentação do modelo LLM

---

## 🎓 Contexto Académico

Este projeto foi desenvolvido no âmbito da unidade curricular **PIC2 — Projeto Integrador de 2º Ciclo em Engenharia Informática e de Computadores** (2026/2027) e suporta a dissertação de mestrado:

> **"Ecossistema de Agentes IA para Gestão de Projetos: Planeamento, Execução e Tomada de Decisão"**

Orientado pelo **Prof. Alberto Rodrigues da Silva** no âmbito do grupo **IDSS** do **INESC-ID**.

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License** — consulta o ficheiro [LICENSE](LICENSE) para detalhes.

---

**⭐ Se este projeto te foi útil, considera deixar uma estrela no repositório!**
