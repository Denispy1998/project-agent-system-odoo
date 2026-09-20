/*******************************************************************************************
 * AI Project Management Ecosystem - ASL Specification
 * 
 * Generated from RSL specification
 * 
 * Contains:
 * - Package and System
 * - Data Entities and Enumerations
 * - Actors
 * - User Interface Elements
 *******************************************************************************************/

Package AIProjectManagementEcosystem

System AIProjectManagement "AI Project Management Ecosystem" : Application [
    description "Web-based platform integrating AI for project management."
]

// Data Enumerations
DataEnumeration AIModelProvider values (Groq, OpenAI, Anthropic)
DataEnumeration UserRole values (ProjectManager, TeamMember, ProductManager, Administrator)
DataEnumeration TaskStatus values (NoStage, InProgress, Completed, OnHold)

// Data Entities
DataEntity e_Project "Project" : Master [
    attribute projectId : Integer [constraints (PrimaryKey)]
    attribute projectName : String(100) [constraints (NotNull)]
    attribute taskCount : Integer
]

DataEntity e_User "User" : Master [
    attribute userId : Integer [constraints (PrimaryKey)]
    attribute username : String(50) [constraints (NotNull)]
    attribute email : String(100) [constraints (NotNull)]
    attribute userRole : String(30)
]

DataEntity e_Task "Task" : Transaction [
    attribute taskId : Integer [constraints (PrimaryKey)]
    attribute taskName : String(200) [constraints (NotNull)]
    attribute stage : String(50)
    attribute taskStatus : String(30)
    attribute projectId : Integer [constraints (NotNull ForeignKey (e_Project))]
]

DataEntity e_Stage "Stage" : Reference [
    attribute stageId : Integer [constraints (PrimaryKey)]
    attribute stageName : String(50) [constraints (NotNull)]
    attribute sequence : Integer [constraints (NotNull)]
    attribute projectId : Integer [constraints (NotNull ForeignKey (e_Project))]
]

DataEntity e_AISession "AI Session" : Transaction [
    attribute sessionId : Integer [constraints (PrimaryKey)]
    attribute sessionName : String(100) [constraints (NotNull)]
    attribute modelProvider : String(30)
    attribute userId : Integer [constraints (NotNull ForeignKey (e_User))]
]

DataEntity e_Agent "Agent" : Reference [
    attribute agentId : Integer [constraints (PrimaryKey)]
    attribute agentName : String(50) [constraints (NotNull)]
    attribute agentType : String(50) [constraints (NotNull)]
]

// Actors
Actor a_ProjectManager "Project Manager" : User
Actor a_TeamMember "Team Member" : User
Actor a_ProductManager "Product Manager" : User
Actor a_Administrator "Administrator" : User

// User Interface Elements
UIContainer ui_MainDashboard "Main Dashboard" [
    description "Central hub for project management activities"
]

UIComponent ui_ProjectList "Project List" : Table [
    parent ui_MainDashboard
    dataEntity e_Project
    columns [
        projectName,
        taskCount
    ]
    actions [
        ui_CreateProject,
        ui_ViewProjectDetails
    ]
]

UIComponent ui_CreateProject "Create Project" : Form [
    parent ui_MainDashboard
    fields [
        projectName : String(100) [required]
    ]
    submitAction ui_SubmitCreateProject
]

UIAction ui_SubmitCreateProject "Submit Create Project" [
    trigger ui_CreateProject.submit
    operation e_Project.create
]

UIComponent ui_TaskBoard "Task Board" : Kanban [
    parent ui_MainDashboard
    dataEntity e_Task
    columns [
        NoStage,
        InProgress,
        Completed,
        OnHold
    ]
    actions [
        ui_AddTask,
        ui_MoveTask,
        ui_DeleteTask
    ]
]

UIComponent ui_AddTask "Add Task" : Form [
    parent ui_TaskBoard
    fields [
        taskName : String(200) [required],
        projectId : Integer [required]
    ]
    submitAction ui_SubmitAddTask
]

UIAction ui_SubmitAddTask "Submit Add Task" [
    trigger ui_AddTask.submit
    operation e_Task.create
]

UIComponent ui_AIChat "AI Chat" : Chat [
    parent ui_MainDashboard
    dataEntity e_AISession
    modelProviders [
        Groq,
        OpenAI,
        Anthropic
    ]
    actions [
        ui_SwitchAIModel
    ]
]

UIComponent ui_SwitchAIModel "Switch AI Model" : Dropdown [
    parent ui_AIChat
    options AIModelProvider
    changeAction ui_UpdateAIModel
]

UIAction ui_UpdateAIModel "Update AI Model" [
    trigger ui_SwitchAIModel.change
    operation e_AISession.update
]

UIComponent ui_Settings "Settings" : Form [
    parent ui_MainDashboard
    fields [
        userRole : String(30) [options UserRole]
    ]
    submitAction ui_SaveSettings
]

UIAction ui_SaveSettings "Save Settings" [
    trigger ui_Settings.submit
    operation e_User.update
]

UIComponent ui_ReportGenerator "Report Generator" : Report [
    parent ui_MainDashboard
    dataEntity e_Project
    formats [
        PDF,
        CSV
    ]
    actions [
        ui_GenerateReport
    ]
]

UIAction ui_GenerateReport "Generate Report" [
    trigger ui_ReportGenerator.generate
    operation e_Project.read
]

UIComponent ui_DataExporter "Data Exporter" : Export [
    parent ui_MainDashboard
    dataEntity e_Project
    formats [
        CSV,
        JSON
    ]
    actions [
        ui_ExportData
    ]
]

UIAction ui_ExportData "Export Data" [
    trigger ui_DataExporter.export
    operation e_Project.read
]
