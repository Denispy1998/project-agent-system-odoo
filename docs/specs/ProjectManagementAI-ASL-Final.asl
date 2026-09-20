// Package and System
Package AIProjectManagementEcosystem

System AIProjectManagementSystem "AI Project Management Ecosystem" : WebApplication [
    description "AI-powered project management platform"
]

// Data Entities
Entity Project {
    id: Integer [primaryKey, autoIncrement]
    name: String(100) [required]
    description: String(500)
}

Entity Task {
    id: Integer [primaryKey, autoIncrement]
    projectId: Integer [required, references Project]
    name: String(200) [required]
    stage: String(50)
    status: TaskStatus [required]
}

Entity Stage {
    id: Integer [primaryKey, autoIncrement]
    projectId: Integer [required, references Project]
    name: String(50) [required]
    sequence: Integer [required]
}

Entity User {
    id: Integer [primaryKey, autoIncrement]
    username: String(50) [required, unique]
    email: String(100) [required, unique]
    role: UserRole [required]
}

Entity AISession {
    id: Integer [primaryKey, autoIncrement]
    userId: Integer [required, references User]
    modelProvider: AIModelProvider [required]
    sessionName: String(100) [required]
}

Entity Agent {
    id: Integer [primaryKey, autoIncrement]
    name: String(50) [required]
    type: String(50) [required]
}

// Data Enumerations
Enum AIModelProvider {
    Groq, OpenAI, Anthropic
}

Enum UserRole {
    ProjectManager, TeamMember, ProductManager, Administrator
}

Enum TaskStatus {
    NoStage, InProgress, Completed, OnHold
}

// Actors
Actor ProjectManager {
    description "Manages projects and tasks"
}

Actor TeamMember {
    description "Contributes to tasks"
}

Actor ProductManager {
    description "Manages product backlog"
}

Actor Administrator {
    description "Manages system configuration"
}

// User Interface
UIContainer Dashboard {
    component ProjectOverview {
        part ProjectList: Table [
            columns: ["name", "taskCount", "status"]
        ]
        part TaskChart: BarChart [
            xAxis: "Task Status",
            yAxis: "Count"
        ]
    }
    component AIChat {
        part ChatWindow: ChatBox [
            modelProvider: AIModelProvider
        ]
    }
}

UIContainer ProjectManagement {
    component TaskBoard {
        part StageColumns: KanbanBoard [
            stages: ["NoStage", "InProgress", "Completed", "OnHold"]
        ]
        part TaskCards: CardList [
            fields: ["name", "status", "assignee"]
        ]
    }
    component ProjectSettings {
        part DetailsForm: Form [
            fields: ["name", "description", "startDate", "endDate"]
        ]
    }
}

UIContainer Settings {
    component UserProfile {
        part ProfileForm: Form [
            fields: ["username", "email", "role"]
        ]
    }
    component AIConfiguration {
        part ModelSelector: Dropdown [
            options: AIModelProvider
        ]
    }
}
