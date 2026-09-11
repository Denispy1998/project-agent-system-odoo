# Ecossistema IA para Gestão de Projetos

**Dissertação de Mestrado em Engenharia Informática e de Computadores**  
Instituto Superior Técnico, Universidade de Lisboa  
Autor: Denilson Fragoso Da Silva Santos (IST-1113142)  
Orientador: Prof. Alberto Rodrigues da Silva  
Ano: 2026/2027

---

## 📖 Descrição

Sistema multiagente integrado no Odoo 19 que permite gerir projetos via linguagem natural. Inclui 14 ferramentas para criação de projetos, tarefas, stages, análise de riscos, priorização automática e geração de resumos.

## 🛠️ Tecnologias

- Odoo Community 19
- Python 3.14
- Groq API (openai/gpt-oss-20b)
- PostgreSQL 18
- HTML5, CSS3, JavaScript (Chart.js)

## 📁 Estrutura
project-agent-system-odoo/
├── agent/ # Agente IA
│ ├── chat_agent.py
│ └── setup_users.py # Script universal
├── odoo-module/ # Módulo Odoo
│ ├── manifest.py
│ ├── controllers/
│ ├── security/
│ ├── static/
│ └── views/
├── docs/ # Documentação
└── README.md

text

## 🚀 Instalação Rápida

### 1. Pré-requisitos

- WSL (Ubuntu)
- PostgreSQL 18
- Python 3.14

### 2. Clonar o repositório

```bash
git clone https://github.com/Denispy1998/project-agent-system-odoo.git
cd project-agent-system-odoo

3. Configurar o agente
bash
mkdir -p ~/project-agent-system
cp agent/chat_agent.py ~/project-agent-system/
cp agent/setup_users.py ~/project-agent-system/
cd ~/project-agent-system
nano .env

4. Copiar o módulo para o Odoo
bash
sudo cp -r odoo-module /opt/odoo/odoo19/addons/meu_assistente_ia

5. Instalar o módulo
bash
cd /opt/odoo/odoo19
source ../venv-19/bin/activate
pip install groq python-dotenv
python odoo-bin -c ~/odoo19.conf -d odoo -i project,mail,website --stop-after-init
python odoo-bin -c ~/odoo19.conf -d odoo -i meu_assistente_ia --stop-after-init

6. Criar utilizadores de teste
bash
cd ~/project-agent-system
python3 -m venv venv
source venv/bin/activate
pip install groq python-dotenv
python setup_users.py

7. Arrancar
bash
cd /opt/odoo/odoo19
source ../venv-19/bin/activate
python odoo-bin -c ~/odoo19.conf
Aceder a: http://localhost:8069/assistente

🔐 Credenciais de Teste

Utilizador	Password	Papel
admin	admin	Gestor de Projeto
joao	joao	Membro de Equipa
jose	jose	Membro de Equipa

📊 Funcionalidades

O agente entende comandos em português:

Lista os projetos existentes

Cria o projeto "Vendas" com tarefas A, B, C

Adiciona a tarefa "D" ao projeto "Vendas"

Cria o stage "REVIEW" com sequência 15 para o projeto "Vendas"

Move todas as tarefas do projeto "Vendas" para o stage "REVIEW"

Move a tarefa "A" do projeto "Vendas" para o stage "FASE_2"

Analisa os riscos do projeto "Vendas"

Prioriza as tarefas do projeto "Vendas"

Dá-me um resumo do projeto "Vendas"

Elimina o projeto "Vendas"

📄 Licença
MIT
