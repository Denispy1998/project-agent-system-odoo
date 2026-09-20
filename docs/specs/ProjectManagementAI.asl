System AI_Project_Ecosystem : Application : Web_Application {

    title "AI Project Management Ecosystem"
    version "2.0"
    description "Multi-agent AI ecosystem integrated with Odoo 19 for project management"

    // ============================================================
    // AI MODELS
    // ============================================================
    AIModel groq_qwen_27b : Generative {
        provider "Groq"
        modelId "qwen/qwen3.8-27b"
        capability Text, ToolUse
        role Primary
    }

    AIModel groq_gpt_oss_20b : Generative {
        provider "Groq"
        modelId "openai/gpt-oss-20b"
        capability Text, ToolUse
        role Alternative
    }

    AIModel openai_gpt4o : Generative {
        provider "OpenAI"
        modelId "gpt-4o"
        capability Text, ToolUse, Vision
        role Alternative
    }

    AIModel anthropic_claude_35 : Generative {
        provider "Anthropic"
        modelId "claude-3-5-sonnet-20241022"
        capability Text, ToolUse
        role Alternative
    }

    // ============================================================
    // TOOLS (Odoo XML-RPC)
    // ============================================================
    Tool list_projects {
        description "List all projects in Odoo."
        type Read
    }

    Tool list_tasks {
        description "List tasks of a project."
        type Read
    }

    Tool list_stages {
        description "List stages of a project."
        type Read
    }

    Tool analyze_risks {
        description "Analyze project risk based on tasks without stage."
        type Read
    }

    Tool prioritize_tasks {
        description "Prioritize tasks with no stage first."
        type Read
    }

    Tool project_summary {
        description "Full project summary with tasks, stages, risks."
        type Read
    }

    Tool create_project {
        description "Create a new project. Idempotent."
        type Write
    }

    Tool add_task {
        description "Add a task to a project. Idempotent."
        type Write
    }

    Tool create_stage {
        description "Create a new stage in a project. Idempotent."
        type Write
    }

    Tool move_single_task {
        description "Move one task to another stage."
        type Write
    }

    Tool move_tasks {
        description "Move multiple tasks to a target stage."
        type Write
    }

    Tool delete_task {
        description "Delete a task from a project."
        type Write
    }

    Tool delete_stage {
        description "Delete a stage if it has no tasks."
        type Write
    }

    Tool delete_project {
        description "Delete a project and all its tasks."
        type Write
    }

    Tool generate_mermaid_diagram {
        description "Generate a Mermaid diagram from description."
        type Generation
    }

    // ============================================================
    // AI AGENTS
    // ============================================================
    AIAgent project_manager_agent : Validator {
        role "Project Manager"
        objective "Manage projects, tasks, stages and risks in Odoo."
        instruction "Use tools to create, list, move and delete data. Respond in English. Call EXACTLY ONE tool per request."
        model groq_qwen_27b
        tool list_projects, list_tasks, list_stages, analyze_risks,
             prioritize_tasks, project_summary,
             create_project, add_task, create_stage,
             move_single_task, move_tasks,
             delete_task, delete_stage, delete_project
        maxIterations 1
    }

    AIAgent team_member_agent : Assistant {
        role "Team Member"
        objective "Consult projects, tasks, stages, risks and priorities."
        instruction "You have READ-ONLY access. Respond in English. Call EXACTLY ONE tool per request."
        model groq_qwen_27b
        tool list_projects, list_tasks, list_stages,
             analyze_risks, prioritize_tasks, project_summary
        maxIterations 1
    }

    AIAgent reporting_agent : Reporter {
        role "Reporting Specialist"
        objective "Generate status reports for projects and ecosystem."
        instruction "Produce concise, well-formatted status reports. Respond in English."
        model groq_qwen_27b
        tool list_projects, list_tasks, analyze_risks
        maxIterations 1
    }

    AIAgent diagram_agent : Generator {
        role "Diagram Generator"
        objective "Generate Mermaid diagrams from natural language."
        instruction "Produce syntactically valid Mermaid code. Respond in English."
        model groq_qwen_27b
        tool generate_mermaid_diagram
        maxIterations 1
    }

    // ============================================================
    // ORCHESTRATION
    // ============================================================
    AIOrchestration orchestrator : Router {
        description "Route user requests to the appropriate agent based on intent and user role."

        step detect_intent : Analyse {
            input user_message
            output agent_type
        }

        step check_permission : Validate {
            input user_role, user_message
            condition "if not manager and write intent then DENIED"
        }

        step delegate : Invoke {
            input agent_type
            agent project_manager_agent, team_member_agent,
                  reporting_agent, diagram_agent
        }

        step handle_rate_limit : Retry {
            input llm_error
            condition "if rate_limit then wait 65s and retry (max 3)"
        }

        start detect_intent
        transition to_check from detect_intent to check_permission
        transition to_delegate from check_permission to delegate
        transition to_retry from delegate to handle_rate_limit
    }

    // ============================================================
    // CONTAINERS
    // ============================================================
    Container odoo_server : Server {
        technology "Odoo 19 Community"
        port 8069
        responsibility "Web UI, ORM, business logic, chat controller, dashboards, PDF/CSV export, cron jobs"
    }

    Container agent_microservice : Server {
        technology "FastAPI + CrewAI 0.175.0"
        port 8001
        responsibility "Hosts the multi-agent orchestrator; exposes /agent/run and /health"
    }

    Container postgres_db : Database {
        technology "PostgreSQL 18"
        responsibility "Persistent storage of Odoo models including ai.session"
    }

    Container llm_router : Gateway {
        technology "LLM APIs"
        responsibility "Route AI requests to Groq, OpenAI or Anthropic based on session configuration"
    }

    // ============================================================
    // UI
    // ============================================================
    UIContainer ai_ecosystem_ui : Web_UI {
        technology "HTML5 + CSS3 + JavaScript (Chart.js + Font Awesome)"

        UIComponent home_page : Dashboard {
            description "Compact home with role badge, KPIs and 4 action cards."
        }

        UIComponent chat_page : Chat {
            description "Multi-session chat with sidebar, model selector and role badge."
        }

        UIComponent dashboard_page : Dashboard {
            description "Global dashboard with donut/bar charts + detail breakdowns."
        }

        UIComponent projects_page : List {
            description "Grid of all projects with task count."
        }

        UIComponent project_detail_page : Detail {
            description "Per-project tasks, charts, PDF and CSV export."
        }

        UIComponent my_workspace_page : Personal_View {
            description "Manager: all projects. Team Member: only assigned tasks."
        }

        UIComponent footer : Copyright {
            description "Denilson Fragoso Da Silva Santos · IST · 2026"
        }
    }

    // ============================================================
    // DATA MODELS
    // ============================================================
    DataModel AISession {
        name "ai.session"
        description "Chat session per user with model preference and JSON messages."
        field user_id "res.users"
        field model_name "Char"
        field messages "Text (JSON)"
    }

    DataModel ProjectTaskExt {
        name "project.task (extended)"
        description "Uses user_ids (many2many) for Odoo 19 compatibility."
    }

    DataModel ProjectProjectExt {
        name "project.project (extended)"
        description "Adds _send_weekly_report() model method."
    }

    // ============================================================
    // CRON / AUTOMATION
    // ============================================================
    Automation weekly_report_cron {
        name "Weekly AI Ecosystem Report"
        schedule "every 1 week"
        action "_send_weekly_report on project.project"
        output "mail.mail record with HTML body"
    }
}
