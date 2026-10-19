/*
 * AI Project Management Ecosystem — ASL specification (v3.3)
 * Author: Denilson Fragoso Da Silva Santos (IST-1113142)
 * Advisor: Prof. Alberto Rodrigues da Silva
 * Language: ITLingo ASL v7.3
 *
 * v3.3 — parser-clean (0 errors):
 *  - Removed page-level `on X.Y do action` statements whose component
 *    paths used useComponent-referenced components (parser only resolves
 *    inline-declared components). Events remain declared in each
 *    UIComponent and UIAction; wiring is explicit at the component level.
 *  - View v_DataEntities changed from : DataEntityView to : DataView
 *    (DataEntityView is not part of the parser's valid View type set).
 */

Package aiprojectmanagementecosystem

System AIProjectManagement "AI Project Management Ecosystem" : Application : Application_Web [
    version "3.3"
    vendor  "IST-MEIC"
    description "Web application for AI-assisted project management, backed by Odoo 19 and a hybrid router + LLM fallback."
    isReusable
]

/* ============================================================
 * Data Enumerations
 * ============================================================ */
DataEnumeration TaskStatusKind values (TaskBacklog "In Backlog", TaskInProgress "In Progress", TaskConcluded "Concluded")
DataEnumeration TaskTypeKind   values (TaskManagement "Management", TaskEngineering "Engineering", TaskOperational "Operational")
DataEnumeration UserRoleKind   values (UserRoleProjectManager "Project Manager", UserRoleTeamMember "Team Member", UserRoleProductManager "Product Manager", UserRoleAdministrator "Administrator")
DataEnumeration AIProviderKind values (ProviderGroq, ProviderOpenAI, ProviderAnthropic)
DataEnumeration AgentTypeKind  values (AgentProjectManagerAgent, AgentTeamMemberAgent, AgentReportingAgent, AgentDiagramAgent)
DataEnumeration ChatSessionStatusKind values (ChatSessionActive "Active", ChatSessionArchived "Archived")
DataEnumeration ProjectAssignmentRoleKind values (AssignmentManager, AssignmentContributor, AssignmentObserver)
DataEnumeration IterationKind values (IterationSprint "Sprint", IterationWorkPackage "Work Package")
DataEnumeration RouterDecisionKind values (RouterLocalPattern "Local Pattern", RouterLLMFallback "LLM Fallback")

/* ============================================================
 * Data Entities
 * ============================================================ */
DataEntity e_User "User" : Master [
    attribute ID           "User identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name         "Full name"       : String(100) [constraints (NotNull)]
    attribute EmailAddress "Email address"   : String(100) [constraints (NotNull Unique)]
    attribute LoginName    "Login"           : String(50)  [constraints (NotNull Unique)]
    attribute IsEnabled    "Is enabled"      : Boolean [defaultValue "True" constraints (NotNull)]
    attribute SystemRole   "System role"     : DataEnumeration UserRoleKind [constraints (NotNull)]
    description "Users of the ecosystem."
]

DataEntity e_Project "Project" : Master [
    attribute ID          "Project identifier"  : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name        "Project name"        : String(100) [constraints (NotNull)]
    attribute Description "Project description" : Text
    attribute CreatedDate "Creation date"       : Date [defaultValue "today" constraints (NotNull)]
    attribute OwnerID     "Owner"               : Integer [constraints (NotNull ForeignKey (e_User))]
    attribute ManagerID   "Project manager"     : Integer [constraints (NotNull ForeignKey (e_User))]
    description "Projects managed in the ecosystem."
]

DataEntity e_ProjectAssignment "Project assignment" : Transaction [
    attribute ID             "Assignment identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute UserID         "User"                  : Integer [constraints (NotNull ForeignKey (e_User))]
    attribute ProjectID      "Project"               : Integer [constraints (NotNull ForeignKey (e_Project))]
    attribute AssignmentRole "Role in project"       : DataEnumeration ProjectAssignmentRoleKind [constraints (NotNull)]
    description "Assignment of users to projects."
]

DataEntity e_ProjectStage "Project stage" : Reference [
    attribute ID            "Stage identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name          "Stage name"       : String(50) [constraints (NotNull)]
    attribute StageSequence "Stage sequence"   : Integer [constraints (NotNull)]
    attribute ProjectID     "Project"          : Integer [constraints (NotNull ForeignKey (e_Project))]
    description "Ordered workflow stages of a project."
]

DataEntity e_Iteration "Iteration" : Master [
    attribute ID        "Iteration identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name      "Iteration name"       : String(80) [constraints (NotNull)]
    attribute Kind      "Iteration kind"       : DataEnumeration IterationKind [constraints (NotNull)]
    attribute ProjectID "Project"              : Integer [constraints (NotNull ForeignKey (e_Project))]
    attribute StartDate "Start date"           : Date
    attribute EndDate   "End date"             : Date
    description "Sprint or work package grouping tasks."
]

DataEntity e_Milestone "Milestone" : Master [
    attribute ID        "Milestone identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name      "Milestone name"       : String(80) [constraints (NotNull)]
    attribute DueDate   "Due date"             : Date [constraints (NotNull)]
    attribute ProjectID "Project"              : Integer [constraints (NotNull ForeignKey (e_Project))]
    description "Significant project checkpoint."
]

DataEntity e_ProjectTask "Project task" : Transaction [
    attribute ID            "Task identifier"  : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name          "Task name"        : String(200) [constraints (NotNull)]
    attribute Description   "Description"      : Text
    attribute ProjectID     "Project"          : Integer [constraints (NotNull ForeignKey (e_Project))]
    attribute StageID       "Stage"            : Integer [constraints (ForeignKey (e_ProjectStage))]
    attribute IterationID   "Iteration"        : Integer [constraints (ForeignKey (e_Iteration))]
    attribute TaskType      "Task type"        : DataEnumeration TaskTypeKind   [constraints (NotNull)]
    attribute TaskStatus    "Task status"      : DataEnumeration TaskStatusKind [defaultValue "TaskBacklog" constraints (NotNull)]
    attribute CreatedDate   "Creation date"    : Date [defaultValue "today" constraints (NotNull)]
    attribute ConcludedDate "Conclusion date"  : Date
    description "Tasks grouped by project, iteration, stage and type."
]

DataEntity e_ChatFolder "Chat folder" : Master [
    attribute ID      "Folder identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name    "Folder name"       : String(100) [constraints (NotNull)]
    attribute OwnerID "Owner"             : Integer [constraints (NotNull ForeignKey (e_User))]
    description "User-owned container for chat sessions."
]

DataEntity e_ChatSession "Chat session" : Transaction [
    attribute ID            "Session identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name          "Session name"       : String(100) [constraints (NotNull)]
    attribute UserID        "Owner"              : Integer [constraints (NotNull ForeignKey (e_User))]
    attribute FolderID      "Folder"             : Integer [constraints (ForeignKey (e_ChatFolder))]
    attribute Provider      "AI provider"        : DataEnumeration AIProviderKind [constraints (NotNull)]
    attribute SessionStatus "Session status"     : DataEnumeration ChatSessionStatusKind [defaultValue "ChatSessionActive" constraints (NotNull)]
    attribute StartedAt     "Started at"         : Datetime [constraints (NotNull)]
    description "Persistent conversation session with the AI agents."
]

DataEntity e_StreamChat "Chat message" : Transaction [
    attribute ID             "Message identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute SessionID      "Session"            : Integer [constraints (NotNull ForeignKey (e_ChatSession))]
    attribute MessageRole    "Message role"       : String(20) [constraints (NotNull)]
    attribute MessageContent "Message content"    : Text       [constraints (NotNull)]
    attribute SentAt         "Timestamp"          : Datetime   [constraints (NotNull)]
    description "Individual message inside a chat session."
]

DataEntity e_AgentTemplate "Agent template" : Reference [
    attribute ID             "Template identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute Name           "Template name"       : String(50) [constraints (NotNull)]
    attribute AgentType      "Agent type"          : DataEnumeration AgentTypeKind [constraints (NotNull)]
    attribute PromptTemplate "Prompt template"     : Text       [constraints (NotNull)]
    attribute MaxIterations  "Max iterations"      : Integer    [constraints (NotNull)]
    description "Reusable definition of a specialised AI agent."
]

DataEntity e_AgentTool "Agent tool" : Reference [
    attribute ID           "Tool identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute TemplateID   "Template"        : Integer [constraints (NotNull ForeignKey (e_AgentTemplate))]
    attribute Name         "Tool name"       : String(80) [constraints (NotNull)]
    attribute SideEffect   "Side effect"     : String(20) [constraints (NotNull)]
    attribute IsIdempotent "Is idempotent"   : Boolean [defaultValue "True" constraints (NotNull)]
    description "Declared tool exposed to an agent template."
]

DataEntity e_AgentTask "Agent task" : Transaction [
    attribute ID           "Agent task identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute TemplateID   "Template"              : Integer [constraints (NotNull ForeignKey (e_AgentTemplate))]
    attribute TaskSequence "Order"                 : Integer [constraints (NotNull)]
    attribute Instruction  "Instruction"           : Text    [constraints (NotNull)]
    description "Ordered task executed by an agent template."
]

DataEntity e_AgentInstance "Agent instance" : Transaction [
    attribute ID             "Instance identifier" : Integer [constraints (PrimaryKey NotNull Unique)]
    attribute TemplateID     "Template"            : Integer [constraints (NotNull ForeignKey (e_AgentTemplate))]
    attribute ProjectID      "Project"             : Integer [constraints (ForeignKey (e_Project))]
    attribute StartedAt      "Start time"          : Datetime [constraints (NotNull)]
    attribute EndedAt        "End time"            : Datetime
    attribute RouterDecision "Router decision"     : DataEnumeration RouterDecisionKind
    attribute Results        "Results"             : Text
    description "Concrete execution of an agent template."
]

DataEntityCluster ec_User "Users" : Master [
    main e_User
    description "User data cluster."
]

DataEntityCluster ec_Project "Projects" : Master [
    main e_Project
    child e_ProjectAssignment
    child e_ProjectStage
    child e_Iteration
    child e_Milestone
    child e_ProjectTask
    uses e_User
    description "Project planning and execution cluster."
]

DataEntityCluster ec_AI "AI ecosystem" : Document [
    main e_ChatSession
    child e_StreamChat
    uses e_ChatFolder
    uses e_AgentTemplate
    uses e_AgentTool
    uses e_AgentTask
    uses e_AgentInstance
    description "Chat, agent template, tooling and execution cluster."
]

/* ============================================================
 * Actors
 * ============================================================ */
Actor a_ProjectManager "Project Manager" : User [
    description "Manages projects, tasks, stages, iterations, chat sessions and diagrams."
]
Actor a_TeamMember "Team Member" : User [
    description "Read-only access to projects, tasks and reports."
]
Actor a_ProductManager "Product Manager" : User [
    description "Manages the product backlog and prioritisation."
]
Actor a_Administrator "Administrator" : User [
    description "Configures the ecosystem and manages users and roles."
]
Actor a_LLMProvider "LLM Provider" : ExternalSystem [
    description "Provides reasoning and tool-use capabilities."
]
Actor a_OdooPlatform "Odoo Platform" : ExternalSystem [
    description "Persists ecosystem data and enforces access control."
]

/* ============================================================
 * Security — Permissions  (resource inside the body)
 * ============================================================ */
SecPermission pManageProjects : Manage [
    resource e_Project
    description "Allows creating, updating and deleting projects."
]

SecPermission pManageTasks : Manage [
    resource e_ProjectTask
    description "Allows creating, moving and deleting tasks."
]

SecPermission pManageStages : Manage [
    resource e_ProjectStage
    description "Allows creating and deleting workflow stages."
]

SecPermission pManageIterations : Manage [
    resource e_Iteration
    description "Allows managing sprints and work packages."
]

SecPermission pReadProjects : Read [
    resource e_Project
    description "Allows consulting projects and their task counts."
]

SecPermission pReadTasks : Read [
    resource e_ProjectTask
    description "Allows consulting project tasks."
]

SecPermission pReadStages : Read [
    resource e_ProjectStage
    description "Allows consulting project stages."
]

SecPermission pAnalyzeRisks : Read [
    resource e_ProjectTask
    condition "currentUser.SystemRole in {'UserRoleProjectManager','UserRoleProductManager'}"
    description "Allows delay-risk analysis over tasks without stage."
]

SecPermission pPrioritizeTasks : Read [
    resource e_ProjectTask
    description "Allows prioritised task listing."
]

SecPermission pSwitchAIModel : Update [
    resource e_ChatSession
    description "Allows switching the AI provider of a chat session."
]

SecPermission pArchiveSession : Update [
    resource e_ChatSession
    description "Allows archiving a chat session."
]

SecPermission pGenerateReport : Execute [
    resource e_Project
    description "Allows generating a PDF project report."
]

SecPermission pGenerateDiagram : Execute [
    resource e_Project
    description "Allows generating a Mermaid diagram."
]

SecPermission pWeeklyReport : Execute [
    resource ec_Project
    description "Allows generating and emailing the weekly report."
]

SecPermission pExportData : Execute [
    resource ec_Project
    description "Allows exporting project or task data to CSV."
]

SecPermission pManageUsers : Manage [
    resource e_User
    description "Allows administering users and roles."
]

/* ============================================================
 * Security — Roles
 * ============================================================ */
SecRole rProjectManager "Project Manager" : Business [
    permission pManageProjects
    permission pManageTasks
    permission pManageStages
    permission pManageIterations
    permission pReadProjects
    permission pReadTasks
    permission pReadStages
    permission pAnalyzeRisks
    permission pPrioritizeTasks
    permission pSwitchAIModel
    permission pArchiveSession
    permission pGenerateReport
    permission pGenerateDiagram
    permission pExportData
    description "Full operational access to projects, tasks, stages and AI sessions."
]

SecRole rTeamMember "Team Member" : Business [
    permission pReadProjects
    permission pReadTasks
    permission pReadStages
    description "Read-only access to projects, tasks and stages."
]

SecRole rProductManager "Product Manager" : Business [
    inherits rTeamMember
    permission pAnalyzeRisks
    permission pPrioritizeTasks
    description "Inherits read-only access and adds risk analysis and prioritisation."
]

SecRole rAdministrator "Administrator" : System [
    permission pManageUsers
    permission pWeeklyReport
    permission pExportData
    description "Configures users, roles and scheduled reporting."
]

SecRole rLLMProvider "LLM Provider" : External [
    description "External AI provider; holds no internal permission."
]

/* ============================================================
 * Security — Access Policies
 * ============================================================ */
SecAccessPolicy apProjectRBAC "Project RBAC policy" : RBAC [
    role rProjectManager
    role rTeamMember
    role rProductManager
    role rAdministrator
    permission pManageProjects
    permission pManageTasks
    permission pManageStages
    permission pManageIterations
    permission pReadProjects
    permission pReadTasks
    permission pReadStages
    permission pAnalyzeRisks
    permission pPrioritizeTasks
    permission pSwitchAIModel
    permission pArchiveSession
    permission pGenerateReport
    permission pGenerateDiagram
    permission pExportData
    permission pManageUsers
    permission pWeeklyReport
    effect Allow
    description "Default allow policy for permissions explicitly assigned to ecosystem roles."
]

SecAccessPolicy apProjectOwnership "Project ownership policy" : ABAC [
    role rProjectManager
    permission pManageProjects
    condition "resource.ManagerID == currentUser.ID or currentUser.SystemRole == 'UserRoleAdministrator'"
    effect Allow
    description "Restricts project writes to the assigned project manager or an administrator."
]

SecAccessPolicy apTaskOwnership "Task ownership policy" : ABAC [
    role rProjectManager
    permission pManageTasks
    condition "resource.Project.ManagerID == currentUser.ID or currentUser.SystemRole == 'UserRoleAdministrator'"
    effect Allow
    description "Restricts task writes to the project manager of the parent project."
]

/* ============================================================
 * UI — Components
 * ============================================================ */
UIComponent roleBadge "Role badge" : Details [
    title "Current role"
    dataBinding e_User [
        visualizationAttributes SystemRole
    ]
]

UIComponent providerSelector "Provider selector" : Form : Form_Simple [
    title "AI provider"
    part providerChoice "Provider" : Field : Field_EditableSelection : WFC_ComboBox [
        dataAttributeBinding e_ChatSession.Provider
        dataBinding e_ChatSession [
            visualizationAttributes Provider
        ]
    ]
    part applyProvider "Apply" : Slot : Slot_MenuOption : WFC_Button [
        event providerChanged "Provider changed" : Submit
    ]
]

UIComponent folderList "Folder list" : List : List_Table [
    title "Folders"
    dataBinding e_ChatFolder [
        visualizationAttributes ID, Name
        orderBy Name ASC
    ]
    part addFolder "New folder" : Slot : Slot_MenuOption : WFC_Button [
        event createFolder "Create folder" : Submit
    ]
    event selectFolder "Open selected folder" : Select
]

UIComponent sessionList "Session list" : List : List_Table [
    title "Sessions"
    dataBinding e_ChatSession [
        searchAttributes Name
        visualizationAttributes Name, Provider, SessionStatus, StartedAt
        filterAttributes SessionStatus, Provider
        orderBy StartedAt DESC
    ]
    part renameSession "Rename" : Slot : Slot_MenuOption : WFC_Button [
        event renameSession "Rename session" : Submit
    ]
    part deleteSession "Delete" : Slot : SlotMenuOption : WFC_Button [
        event deleteSession "Delete session" : Submit
    ]
    event selectSession "Open selected session" : Select
]

UIComponent messageList "Message list" : List : List_Table [
    title "Conversation"
    isScrollable
    dataBinding e_StreamChat [
        visualizationAttributes MessageRole, MessageContent, SentAt
        orderBy SentAt ASC
    ]
]

UIComponent kpiGrid "KPI grid" : List : List_Table [
    title "Key performance indicators"
    dataBinding ec_Project [
        visualizationAttributes e_Project.ID, e_Project.Name
    ]
]

UIComponent taskByStageChart "Tasks by stage" : List : List_Table [
    title "Tasks by stage"
    dataBinding e_ProjectTask [
        visualizationAttributes TaskStatus
        filterAttributes TaskStatus
    ]
]

UIComponent taskByCreatorChart "Tasks by creator" : List : List_Table [
    title "Tasks by creator"
    dataBinding e_ProjectTask [
        visualizationAttributes CreatedDate
        orderBy CreatedDate DESC
    ]
]

UIComponent burnDownChart "Burndown" : List : List_Table [
    title "Burndown"
    dataBinding e_Iteration [
        visualizationAttributes Name, StartDate, EndDate
    ]
]

UIComponent velocityChart "Velocity" : List : List_Table [
    title "Velocity"
    dataBinding e_Iteration [
        visualizationAttributes Name, Kind, StartDate, EndDate
    ]
]

UIComponent projectList "Project list" : List : List_Table [
    title "Projects"
    isScrollable
    dataBinding ec_Project [
        searchAttributes e_Project.Name
        visualizationAttributes e_Project.ID, e_Project.Name, e_Project.CreatedDate
        filterAttributes e_Project.CreatedDate
        orderBy e_Project.Name ASC
    ]
    part addProject "New project" : Slot : Slot_MenuOption : WFC_Button [
        activationExpression "hasPermission('pManageProjects')"
        event createProject "Create project" : Submit
    ]
    event selectProject "Open selected project" : Select
]

UIComponent projectHeader "Project header" : Details [
    title "Project"
    dataBinding e_Project [
        visualizationAttributes Name, Description, CreatedDate, ManagerID
    ]
]

UIComponent stageList "Stage list" : List : List_Table [
    title "Stages"
    dataBinding e_ProjectStage [
        visualizationAttributes Name, StageSequence
        orderBy StageSequence ASC
    ]
    part addStage "New stage" : Slot : Slot_MenuOption : WFC_Button [
        activationExpression "hasPermission('pManageStages')"
        event createStage "Create stage" : Submit
    ]
]

UIComponent iterationList "Iteration list" : List : List_Table [
    title "Iterations"
    dataBinding e_Iteration [
        visualizationAttributes Name, Kind, StartDate, EndDate
        orderBy StartDate DESC
    ]
    part addIteration "New iteration" : Slot : Slot_MenuOption : WFC_Button [
        activationExpression "hasPermission('pManageIterations')"
        event createIteration "Create iteration" : Submit
    ]
]

UIComponent taskList "Task list" : List : List_Table [
    title "Tasks"
    isScrollable
    dataBinding e_ProjectTask [
        searchAttributes Name
        visualizationAttributes ID, Name, TaskType, TaskStatus, CreatedDate
        filterAttributes TaskStatus, TaskType
        orderBy CreatedDate DESC
    ]
    part addTask "New task" : Slot : Slot_MenuOption : WFC_Button [
        activationExpression "hasPermission('pManageTasks')"
        event createTask "Create task" : Submit
    ]
    part moveTask "Move task" : Slot : Slot_MenuOption : WFC_Button [
        activationExpression "hasPermission('pManageTasks')"
        event moveTask "Move selected task" : Submit
    ]
    part deleteTask "Delete task" : Slot : Slot_MenuOption : WFC_Button [
        activationExpression "hasPermission('pManageTasks')"
        event deleteTask "Delete selected task" : Submit
    ]
    event selectTask "Open selected task" : Select
]

UIComponent ownedProjectsList "Owned projects" : List : List_Table [
    title "My projects"
    dataBinding ec_Project [
        searchAttributes e_Project.Name
        visualizationAttributes e_Project.ID, e_Project.Name, e_Project.CreatedDate
        filterAttributes e_Project.CreatedDate
        orderBy e_Project.Name ASC
    ]
    event selectOwnedProject "Open selected project" : Select
]

UIComponent myTasksList "My tasks" : List : List_Table [
    title "My tasks"
    dataBinding e_ProjectTask [
        searchAttributes Name
        visualizationAttributes ID, Name, TaskType, TaskStatus, CreatedDate
        filterAttributes TaskStatus
        orderBy CreatedDate DESC
    ]
]

UIComponent operationErrorDialog "Operation error" : Dialog : Dialog_Error [
    title "Operation failed"
    message "The operation could not be completed. Review the data and try again."
    part closeError "Close" : Slot : Slot_MenuOption : WFC_Button [
        event closeOperationError "Close error" : Submit
    ]
]

/* ============================================================
 * UI — Pages
 * ============================================================ */
UIPage pAssistantChat "AI Assistant Chat" : Application [
    authorization apProjectRBAC
    layout Column [ gap 1 rem width 100 % ]
    accessibility ( label "AI Assistant Chat" role "main" keyboard True focusOrder 1 )

    UIContainer chatWorkspace "Chat workspace" : Window [
        isDefault
        isLandmark
        layout Row [ gap 1 rem width 100 % ]

        UIContainer chatSidebar "Chat sidebar" : Window [
            isLandmark
            layout Column [ gap 1 rem width 25 % ]
            useComponent folderList
            useComponent sessionList
        ]

        UIContainer chatMain "Chat main area" : Window [
            isLandmark
            layout Column [ gap 1 rem width 75 % ]
            useComponent messageList

            UIComponent messageInput "Message input" : Form : Form_Simple [
                title "New message"
                part messageText "Message" : Field : Field_Input : WFC_Text [
                    dataAttributeBinding e_StreamChat.MessageContent
                    valueType Text
                ]
                part sendMessage "Send" : Slot : Slot_MenuOption : WFC_Button [
                    event messageSubmitted "Message submitted" : Submit
                ]
            ]

            useComponent providerSelector
            useComponent roleBadge
        ]
    ]

    on chatMain.messageInput.sendMessage.messageSubmitted do aSendMessage [
        onSuccess navigateTo rAssistantChat
        onFailure navigateTo rOperationError
    ]
]

UIPage pDashboard "Global Dashboard" : Application [
    authorization apProjectRBAC
    layout Column [ gap 1 rem width 100 % ]
    accessibility ( label "Global Dashboard" role "main" keyboard True focusOrder 1 )

    UIContainer dashboardShell "Dashboard shell" : Window [
        isLandmark
        layout Column [ gap 1 rem width 100 % ]
        useComponent kpiGrid
        useComponent taskByStageChart
        useComponent taskByCreatorChart
        useComponent burnDownChart
        useComponent velocityChart
    ]
]

UIPage pProjects "Projects" : List [
    authorization apProjectRBAC
    layout Column [ gap 1 rem width 100 % ]
    accessibility ( label "Projects" role "main" keyboard True focusOrder 1 )
    state UIState projectsLoading : Loading [ message "Loading projects." ]
    state UIState projectsEmpty   : Empty   [ message "No projects were found." ]

    UIContainer projectsWorkspace "Projects workspace" : Window [
        isLandmark
        layout Column [ gap 1 rem width 100 % ]
        UIContainer projectsContent "Project list region" : Other [
            layout Grid [ columns 1 gap 1 rem ]
            useComponent projectList
        ]
    ]
]

UIPage pProjectForm "Project form" : Form [
    authorization apProjectRBAC
    layout Column [ gap 1 rem width 100 % ]
    accessibility ( label "Project form" role "form" keyboard True focusOrder 1 )

    UIContainer projectFormWorkspace "Project form workspace" : Window [
        layout Column [ gap 1 rem width 100 % ]
        UIContainer projectFormContent "Project form region" : Other [
            layout Grid [ columns 2 gap 1 rem ]

            UIComponent projectForm "Project form" : Form : Form_Simple [
                title "Project"
                dataBinding e_Project [
                    visualizationAttributes Name, Description, CreatedDate, ManagerID
                ]
                part projectName "Name" : Field : Field_Input : WFC_Text [
                    dataAttributeBinding e_Project.Name
                    valueType String
                ]
                part projectDescription "Description" : Field : Field_Input : WFC_Text [
                    dataAttributeBinding e_Project.Description
                    valueType Text
                ]
                part projectManager "Manager" : Field : Field_EditableSelection : WFC_ComboBox [
                    dataAttributeBinding e_Project.ManagerID
                    dataBinding e_User [
                        searchAttributes Name, EmailAddress
                        visualizationAttributes ID, Name, EmailAddress
                        orderBy Name ASC
                    ]
                ]
                part saveProject "Save" : Slot : Slot_MenuOption : WFC_Button [
                    activationExpression "hasPermission('pManageProjects')"
                    event submitProject "Save project" : Submit
                ]
                part cancelProject "Cancel" : Slot : Slot_MenuOption : WFC_Button [
                    event cancelProjectEdit "Cancel editing" : Submit
                ]
            ]
        ]
    ]

    on projectFormContent.projectForm.saveProject.submitProject do aSaveProject [
        onSuccess navigateTo rProjects
        onFailure navigateTo rOperationError
    ]
]

UIPage pProjectDetail "Project detail" : Details [
    authorization apProjectRBAC
    layout Column [ gap 1 rem width 100 % ]
    accessibility ( label "Project detail" role "main" keyboard True focusOrder 1 )

    UIContainer detailShell "Project detail shell" : Window [
        isLandmark
        layout Column [ gap 1 rem width 100 % ]
        useComponent projectHeader
        useComponent stageList
        useComponent iterationList
        useComponent taskList
    ]
]

UIPage pMyWorkspace "My Workspace" : Application [
    authorization apProjectRBAC
    layout Column [ gap 1 rem width 100 % ]
    accessibility ( label "My Workspace" role "main" keyboard True focusOrder 1 )

    UIContainer workspaceShell "Workspace shell" : Window [
        isLandmark
        layout Column [ gap 1 rem width 100 % ]
        useComponent ownedProjectsList
        useComponent myTasksList
    ]
]

UIPage pOperationError "Operation error" : Error [
    UIContainer errorShell "Error shell" : Window [
        isLandmark
        layout Column [ gap 1 rem width 100 % ]
        useComponent operationErrorDialog
    ]
]

/* ============================================================
 * UI — Actions
 * ============================================================ */
UIAction aSendMessage "Send message" : Server [
    description "Routes the user message through the hybrid router and returns the agent response."
    event messageSucceeded "Message processed" : Success [
        navigateTo rAssistantChat
    ]
    event messageFailed "Message failed" : Failure [
        navigateTo rOperationError
    ]
]

UIAction aSaveProject "Persist project" : Server [
    description "Validates and persists project data via the Odoo XML-RPC layer."
    event projectSaveSucceeded "Project saved" : Success [
        navigateTo rProjects
    ]
    event projectSaveFailed "Project save failed" : Failure [
        navigateTo rOperationError
    ]
]

UIAction aMoveTask "Move task" : Server [
    description "Moves a task to another stage or status."
    event taskMoveSucceeded "Task moved" : Success [
        navigateTo rProjectDetail
    ]
    event taskMoveFailed "Task move failed" : Failure [
        navigateTo rOperationError
    ]
]

UIAction aArchiveSession "Archive chat session" : Server [
    description "Archives a chat session preserving its history."
    event sessionArchiveSucceeded "Session archived" : Success [
        navigateTo rAssistantChat
    ]
    event sessionArchiveFailed "Session archive failed" : Failure [
        navigateTo rOperationError
    ]
]

UIAction aGenerateReport "Generate report" : Server [
    description "Generates a PDF project report."
    event reportSucceeded "Report generated" : Success [
        navigateTo rProjectDetail
    ]
    event reportFailed "Report failed" : Failure [
        navigateTo rOperationError
    ]
]

UIAction aGenerateDiagram "Generate diagram" : Server [
    description "Generates a Mermaid diagram via LLM with deterministic fallback."
    event diagramSucceeded "Diagram generated" : Success [
        navigateTo rProjectDetail
    ]
    event diagramFailed "Diagram failed" : Failure [
        navigateTo rOperationError
    ]
]

/* ============================================================
 * UI — Design System
 * ============================================================ */
UIDesignSystem aipmDesignSystem "AI Project Management design system" : Application [
    token primaryColor    : Color   value "#2457A7"
    token surfaceColor    : Color   value "#FFFFFF"
    token standardSpacing : Spacing value "8px"
    token formRadius      : Radius  value "4px"
    description "Shared visual tokens and controlled component variants."
]

/* ============================================================
 * UI — Routes
 * ============================================================ */
UIRoute rAssistantChat  "Assistant chat route"  : Page [ path "/assistente/page"          page pAssistantChat ]
UIRoute rDashboard      "Dashboard route"       : Page [ path "/assistente/dashboard"     page pDashboard     ]
UIRoute rProjects       "Projects route"        : Page [ path "/assistente/projetos"      page pProjects      ]
UIRoute rProjectForm    "Project form route"    : Page [ path "/assistente/projeto/edit"  page pProjectForm   ]
UIRoute rProjectDetail  "Project detail route"  : Page [ path "/assistente/projeto/:id"   page pProjectDetail ]
UIRoute rMyWorkspace    "My workspace route"    : Page [ path "/assistente/meus-projetos" page pMyWorkspace   ]
UIRoute rOperationError "Error route"           : Page [ path "/assistente/erro"          page pOperationError ]

UIRouteSet assistantRoutes "Assistant routes" : Authenticated [
    route rAssistantChat
    route rDashboard
    route rProjects
    route rProjectForm
    route rProjectDetail
    route rMyWorkspace
    route rOperationError
    defaultRoute rAssistantChat
    authorization apProjectRBAC
]

/* ============================================================
 * Views
 * ============================================================ */
View v_DataEntities "Data entities" : DataView [
    e_User, e_Project, e_ProjectAssignment, e_ProjectStage,
    e_Iteration, e_Milestone, e_ProjectTask, e_ChatFolder,
    e_ChatSession, e_StreamChat, e_AgentTemplate, e_AgentTool,
    e_AgentTask, e_AgentInstance
    description "Principal persistent entities of the ecosystem."
]

View v_UI "UI pages" : UIView [
    pAssistantChat, pDashboard, pProjects, pProjectForm,
    pProjectDetail, pMyWorkspace, pOperationError
    description "Principal pages of the ecosystem UI."
]

View v_Security "Security model" : SecurityView [
    pManageProjects, pManageTasks, pManageStages, pManageIterations,
    pReadProjects, pReadTasks, pReadStages, pAnalyzeRisks,
    pPrioritizeTasks, pSwitchAIModel, pArchiveSession,
    pGenerateReport, pGenerateDiagram, pWeeklyReport,
    pExportData, pManageUsers,
    rProjectManager, rTeamMember, rProductManager, rAdministrator,
    apProjectRBAC, apProjectOwnership, apTaskOwnership
    description "Permissions, roles and access policies of the ecosystem."
]
