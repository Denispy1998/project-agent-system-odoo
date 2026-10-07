Package AIProjectManagementEcosystem

System AIProjectManagement "AI Project Management Ecosystem" : Application [
    version "2.0"
    vendor "IST-MEIC"
    description "Application-level view of the AI Project Management Ecosystem."
]

// ============ Data Enumerations ============
DataEnumeration TaskStatusKind values (InBacklog "In Backlog", InProgress "In Progress", Concluded "Concluded")
DataEnumeration TaskTypeKind values (TaskManagement "Management", TaskEngineering "Engineering", TaskOperational "Operational")
DataEnumeration UserRoleKind values (ProjectManager, TeamMember, ProductManager, Administrator)
DataEnumeration AIProviderKind values (Groq, OpenAI, Anthropic)
DataEnumeration AgentTypeKind values (ProjectManagerAgent, TeamMemberAgent, ReportingAgent, DiagramAgent)
DataEnumeration ChatSessionStatusKind values (SessionActive "Active", SessionArchived "Archived")
DataEnumeration PersonProjectRoleKind values (Manager, Contributor, Observer)

// ============ Data Entities ============
DataEntity e_Person "Person" : Master [
    attribute ID "Person identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name "Full name" : String(100) [constraints (NotNull)]
    attribute EmailAddress "Email address" : String(100) [constraints (NotNull Unique)]
    attribute LoginName "Login" : String(50) [constraints (NotNull Unique)]
    attribute IsActive "Is active" : Boolean
    attribute UserRole "System role" : DataEnumeration UserRoleKind [constraints (NotNull)]
    description "Users of the ecosystem."
]

DataEntity e_Project "Project" : Master [
    attribute ID "Project identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name "Project name" : String(100) [constraints (NotNull)]
    attribute Description "Project description" : Text
    attribute CreatedDate "Creation date" : Date [constraints (NotNull)]
    attribute ManagerID "Project manager" : Integer [constraints (NotNull ForeignKey (e_Person))]
    description "Projects managed in the ecosystem."
]

DataEntity e_PersonProject "Person-Project assignment" : Transaction [
    attribute ID "Assignment identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute PersonID "Person" : Integer [constraints (NotNull ForeignKey (e_Person))]
    attribute ProjectID "Project" : Integer [constraints (NotNull ForeignKey (e_Project))]
    attribute ProjectRole "Role in project" : DataEnumeration PersonProjectRoleKind [constraints (NotNull)]
    description "Assignment of persons to projects with a project-level role."
]

DataEntity e_ProjectStage "Project stage" : Reference [
    attribute ID "Stage identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name "Stage name" : String(50) [constraints (NotNull)]
    attribute StageSequence "Order" : Integer [constraints (NotNull)]
    attribute ProjectID "Project" : Integer [constraints (NotNull ForeignKey (e_Project))]
    description "Workflow stages of a project."
]

DataEntity e_Task "Task" : Transaction [
    attribute ID "Task identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name "Task name" : String(200) [constraints (NotNull)]
    attribute Description "Task description" : Text
    attribute ProjectID "Project" : Integer [constraints (NotNull ForeignKey (e_Project))]
    attribute StageID "Stage" : Integer [constraints (ForeignKey (e_ProjectStage))]
    attribute TaskType "Task type" : DataEnumeration TaskTypeKind [constraints (NotNull)]
    attribute TaskStatus "Task status" : DataEnumeration TaskStatusKind [constraints (NotNull)]
    attribute CreatedDate "Creation date" : Date [constraints (NotNull)]
    attribute ConcludedDate "Conclusion date" : Date
    description "Tasks grouped by project, stage and type."
]

DataEntity e_ChatFolder "Chat folder" : Master [
    attribute ID "Folder identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name "Folder name" : String(100) [constraints (NotNull)]
    attribute PersonID "Owner" : Integer [constraints (NotNull ForeignKey (e_Person))]
    description "Organizes chat sessions."
]

DataEntity e_ChatSession "Chat session" : Transaction [
    attribute ID "Session identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name "Session name" : String(100) [constraints (NotNull)]
    attribute PersonID "Owner" : Integer [constraints (NotNull ForeignKey (e_Person))]
    attribute FolderID "Folder" : Integer [constraints (ForeignKey (e_ChatFolder))]
    attribute Provider "AI provider" : DataEnumeration AIProviderKind [constraints (NotNull)]
    attribute SessionStatus "Session status" : DataEnumeration ChatSessionStatusKind [constraints (NotNull)]
    description "Conversation sessions with the AI agents."
]

DataEntity e_StreamChat "Chat message" : Transaction [
    attribute ID "Message identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute SessionID "Session" : Integer [constraints (NotNull ForeignKey (e_ChatSession))]
    attribute MessageRole "Message role" : String(20) [constraints (NotNull)]
    attribute MessageContent "Message content" : Text [constraints (NotNull)]
    attribute SentAt "Timestamp" : Datetime [constraints (NotNull)]
    description "Individual messages inside a chat session."
]

DataEntity e_AgentTemplate "Agent template" : Reference [
    attribute ID "Template identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name "Template name" : String(50) [constraints (NotNull)]
    attribute AgentType "Agent type" : DataEnumeration AgentTypeKind [constraints (NotNull)]
    attribute Prompt "Prompt template" : Text [constraints (NotNull)]
    description "Template definition of a specialized AI agent."
]

DataEntity e_AgentInstance "Agent instance" : Transaction [
    attribute ID "Instance identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute TemplateID "Template" : Integer [constraints (NotNull ForeignKey (e_AgentTemplate))]
    attribute ProjectID "Project" : Integer [constraints (ForeignKey (e_Project))]
    attribute StartTime "Start time" : Datetime [constraints (NotNull)]
    attribute EndTime "End time" : Datetime
    attribute Results "Results" : Text
    description "Concrete execution of an agent template."
]

DataEntity e_AgentTask "Agent task" : Transaction [
    attribute ID "Agent task identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute InstanceID "Instance" : Integer [constraints (NotNull ForeignKey (e_AgentInstance))]
    attribute TaskOrder "Order" : Integer [constraints (NotNull)]
    attribute Instruction "Instruction" : Text [constraints (NotNull)]
    description "Ordered task executed by an agent instance."
]

// ============ Actors ============
Actor a_ProjectManager "Project Manager" : User [
    description "Manages projects, tasks, stages, AI sessions and diagrams."
]
Actor a_TeamMember "Team Member" : User [
    description "Read-only access to projects, tasks and reports."
]
Actor a_ProductManager "Product Manager" : User [
    description "Manages product backlog and priorities."
]
Actor a_Administrator "Administrator" : User [
    description "Configures the ecosystem and manages users."
]
Actor a_LLMProvider "LLM Provider" : ExternalSystem [
    description "Provides AI reasoning and tool-use capabilities."
]

// ============ UI Containers ============
UIContainer cAssistantShell "Assistant shell" : Window [
    isDefault
    isLandmark
    description "Main application shell for the AI assistant."
]

UIContainer cAssistantSidebar "Chat sidebar" : Window [
    description "Left sidebar with chat folders and sessions."
]

UIContainer cAssistantMain "Chat main area" : Window [
    description "Main chat area with messages and input."
]

UIContainer cDashboardShell "Dashboard shell" : Window [
    description "Dashboard shell with KPIs and charts."
]

// ============ UI Components ============
UIComponent uiRoleBadge "Role badge" : Form [
    description "Displays the current user's role (Manager or Team Member)."
]

UIComponent uiProviderSelector "AI provider selector" : Form [
    description "Selects the AI provider (Groq, OpenAI, Anthropic)."
]

UIComponent uiDeepThinkingToggle "Deep thinking toggle" : Form [
    description "Enables the deep thinking reasoning mode."
]

UIComponent uiFolderList "Folder list" : List [
    description "Lists chat folders owned by the user."
]

UIComponent uiSessionList "Session list" : List [
    description "Lists chat sessions with rename and delete actions."
]

UIComponent uiMessageList "Message list" : List [
    description "Displays the conversation with the AI agents."
]

UIComponent uiMessageInput "Message input" : Form [
    description "Text input for user messages."
]

UIComponent uiKpiGrid "KPI grid" : List [
    description "Displays the dashboard KPIs as cards."
]

UIComponent uiStageChart "Tasks by stage chart" : List [
    description "Donut chart of tasks by stage."
]

UIComponent uiCreatorChart "Tasks by creator chart" : List [
    description "Bar chart of tasks by creator."
]

UIComponent uiTaskList "Task list" : List [
    description "Lists tasks of a project."
]

UIComponent uiProjectList "Project list" : List [
    description "Lists all projects with task counts."
]

// ============ UI Pages ============
UIPage pAssistantHome "AI Assistant Home" : Application [
    UIContainer homeShell : Window [
        UIComponent homeForm : Form [
            event startChat : Submit
        ]
    ]
]

UIPage pChatPage "AI Assistant Chat" : Application [
    UIContainer chatSidebar : Window [
        UIComponent folderList : List
        UIComponent sessionList : List
    ]
    UIContainer chatMain : Window [
        UIComponent messageList : List
        UIComponent messageInput : Form [
            event messageSubmitted : Submit
        ]
    ]
]

UIPage pDashboardPage "Global Dashboard" : Application [
    UIContainer dashboardShell : Window [
        UIComponent kpiGrid : List
        UIComponent stageChart : List
        UIComponent creatorChart : List
    ]
]

UIPage pProjectsPage "Projects" : Application [
    UIContainer projectsShell : Window [
        UIComponent projectList : List [
            event projectSelected : Submit
        ]
    ]
]

UIPage pProjectDetailPage "Project Detail" : Application [
    UIContainer detailShell : Window [
        UIComponent taskList : List
    ]
]

UIPage pMyWorkspacePage "My Workspace" : Application [
    UIContainer workspaceShell : Window [
        UIComponent ownedProjectsList : List
    ]
]

// ============ UI Routes ============
UIRoute rHome "Home route" : Page [
    path "/assistente"
    page pAssistantHome
]

UIRoute rChat "Chat route" : Page [
    path "/assistente/page"
    page pChatPage
]

UIRoute rDashboard "Dashboard route" : Page [
    path "/assistente/dashboard"
    page pDashboardPage
]

UIRoute rProjects "Projects route" : Page [
    path "/assistente/projetos"
    page pProjectsPage
]

UIRoute rProjectDetail "Project detail route" : Page [
    path "/assistente/projeto/:id"
    page pProjectDetailPage
]

UIRoute rMyWorkspace "My workspace route" : Page [
    path "/assistente/meus-projetos"
    page pMyWorkspacePage
]

UIRouteSet assistantRoutes "Assistant routes" : Authenticated [
    route rHome
    route rChat
    route rDashboard
    route rProjects
    route rProjectDetail
    route rMyWorkspace
    defaultRoute rHome
]