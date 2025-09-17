# Dynamic Planning Agent (FSM) - Visual Architecture

## 🏗️ System Overview

```mermaid
graph TB
    subgraph "External Interfaces"
        A[Android App] --> B[FastAPI Server]
        C[Web Client] --> B
        D[API Client] --> B
    end
    
    subgraph "FSM Agent Server (Port 8002)"
        B --> E[DynamicPlanningAgent]
        E --> F[LangGraph Workflow]
        
        subgraph "Session Management"
            G[Session Store]
            H[Conversation History]
            I[State Persistence]
        end
        
        E --> G
        E --> H
        E --> I
    end
    
    subgraph "LangGraph StateGraph Workflow"
        F --> J[State Machine Engine]
        J --> K[Conditional Routing]
        K --> L[Tool Executor]
    end
    
    subgraph "LangChain Tools"
        L --> M[ClassificationTool]
        L --> N[PrescriptionTool] 
        L --> O[VendorTool]
        L --> P[ContextExtractorTool]
    end
    
    subgraph "External Services"
        Q[Ollama LLM Server]
        R[CNN Model Files]
        S[ChromaDB RAG]
        T[Vendor Database]
    end
    
    J --> Q
    M --> R
    N --> S
    O --> T
    
    style F fill:#e1f5fe
    style J fill:#f3e5f5
    style L fill:#fff3e0
```

## 🔄 LangGraph StateGraph Flow

```mermaid
stateDiagram-v2
    [*] --> INITIAL
    
    INITIAL --> CLASSIFYING: Has Image + Context
    INITIAL --> FOLLOWUP: Request Image/Info
    INITIAL --> ERROR: Invalid Input
    
    CLASSIFYING --> PRESCRIBING: Classification Success
    CLASSIFYING --> CLASSIFYING: Retry (if failed)
    CLASSIFYING --> FOLLOWUP: Need More Info
    CLASSIFYING --> ERROR: Max Retries Exceeded
    
    PRESCRIBING --> VENDOR_QUERY: Prescription Generated
    PRESCRIBING --> PRESCRIBING: Retry (if failed)
    PRESCRIBING --> COMPLETED: User Wants No Vendors
    PRESCRIBING --> ERROR: Max Retries Exceeded
    
    VENDOR_QUERY --> SHOW_VENDORS: User Says Yes
    VENDOR_QUERY --> COMPLETED: User Says No
    VENDOR_QUERY --> FOLLOWUP: Unclear Response
    
    SHOW_VENDORS --> ORDER_BOOKING: Vendor Selected
    SHOW_VENDORS --> COMPLETED: No Vendors Selected
    SHOW_VENDORS --> FOLLOWUP: Need Clarification
    SHOW_VENDORS --> ERROR: Vendor Search Failed
    
    ORDER_BOOKING --> FOLLOWUP: Order Placed (await feedback)
    ORDER_BOOKING --> COMPLETED: Order Complete
    ORDER_BOOKING --> ERROR: Order Failed
    
    FOLLOWUP --> INITIAL: New Request
    FOLLOWUP --> CLASSIFYING: Reclassify
    FOLLOWUP --> PRESCRIBING: Regenerate Prescription
    FOLLOWUP --> SHOW_VENDORS: Show Vendors Again
    FOLLOWUP --> COMPLETED: User Done
    FOLLOWUP --> ERROR: Error in Processing
    
    ERROR --> [*]
    COMPLETED --> [*]
    
    note right of INITIAL: Entry point with\ncontext extraction
    note right of CLASSIFYING: CNN disease\nclassification
    note right of PRESCRIBING: RAG-based\nrecommendations
    note right of VENDOR_QUERY: Ask user about\nvendor preferences
    note right of SHOW_VENDORS: Display local\nvendors & pricing
    note right of ORDER_BOOKING: Process order\nwith selected vendor
    note right of FOLLOWUP: Handle additional\nquestions & navigation
    note right of COMPLETED: Terminal state with\ncontextual follow-ups
```

## 🧠 State Node Execution Flow

```mermaid
sequenceDiagram
    participant U as User
    participant S as FastAPI Server
    participant A as FSMAgent
    participant W as LangGraph Workflow
    participant T as Tools
    participant L as Ollama LLM
    
    U->>+S: POST /chat-stream
    S->>+A: process_message()
    A->>+W: ainvoke(state)
    
    Note over W: State: INITIAL
    W->>+T: ContextExtractorTool
    T-->>-W: Extracted context
    W->>+L: Determine next action
    L-->>-W: "classify" decision
    
    Note over W: Transition: INITIAL → CLASSIFYING
    W->>+T: ClassificationTool
    T-->>-W: Disease prediction
    W->>+L: Determine next action  
    L-->>-W: "prescribe" decision
    
    Note over W: Transition: CLASSIFYING → PRESCRIBING
    W->>+T: PrescriptionTool
    T-->>-W: Treatment recommendations
    W->>+L: Determine next action
    L-->>-W: "vendor_query" decision
    
    Note over W: Transition: PRESCRIBING → VENDOR_QUERY
    W-->>-A: Final state with responses
    A-->>-S: Streaming responses
    S-->>U: Stream chunks
    S-->>-U: [DONE]
```

## 🛠️ Tool Integration Architecture

```mermaid
graph TB
    subgraph "LangChain Tool Ecosystem"
        A[BaseTool Interface]
        
        subgraph "Tool Implementations"
            B[ClassificationTool]
            C[PrescriptionTool]
            D[VendorTool]
            E[ContextExtractorTool]
        end
        
        A --> B
        A --> C
        A --> D
        A --> E
    end
    
    subgraph "External Dependencies"
        F[CNN Classifier]
        G[RAG System]
        H[Vendor Database]
        I[NLP Patterns]
    end
    
    B --> F
    C --> G
    D --> H
    E --> I
    
    subgraph "LangGraph Integration"
        J[ToolExecutor]
        K[StateGraph Nodes]
    end
    
    B --> J
    C --> J
    D --> J
    E --> J
    J --> K
    
    subgraph "Async Execution"
        L[asyncio.to_thread]
        M[Concurrent Processing]
    end
    
    J --> L
    L --> M
    
    style A fill:#e8f5e8
    style J fill:#fff3e0
    style K fill:#e1f5fe
```

## 📊 State Schema & Data Flow

```mermaid
graph LR
    subgraph "WorkflowState (TypedDict)"
        A[Session Management]
        B[User Input]
        C[Context Data]
        D[Classification Results]
        E[Prescription Data] 
        F[Vendor Information]
        G[Conversation History]
        H[Flow Control]
        I[Error Handling]
        J[Metadata]
        K[Assistant Responses]
    end
    
    subgraph "State Updates"
        L[add_message_to_state]
        M[update_state_node]
        N[set_error]
        O[mark_complete]
    end
    
    A --> L
    B --> M
    C --> M
    D --> M
    E --> M
    F --> M
    G --> L
    H --> O
    I --> N
    J --> M
    K --> L
    
    subgraph "Persistence Layer"
        P[In-Memory Sessions]
        Q[Conversation History]
        R[State Snapshots]
    end
    
    L --> P
    M --> Q
    O --> R
    
    style A fill:#e8f5e8
    style L fill:#fff3e0
```

## 🌐 API Architecture & Endpoints

```mermaid
graph TB
    subgraph "Client Requests"
        A[Android App]
        B[Web Client]
        C[API Client]
    end
    
    subgraph "FastAPI Server (Port 8002)"
        D[CORS Middleware]
        E[Request Validation]
        F[Route Handlers]
        
        subgraph "Core Endpoints"
            G[POST /chat]
            H[POST /chat-stream]
            I[GET /health]
            J[GET /stats]
        end
        
        subgraph "Session Endpoints"
            K[GET /session/{id}]
            L[GET /session/{id}/history]
            M[GET /session/{id}/classification]
            N[GET /session/{id}/prescription]
            O[DELETE /session/{id}]
        end
        
        subgraph "Utility Endpoints"
            P[POST /cleanup]
        end
    end
    
    A --> D
    B --> D  
    C --> D
    D --> E
    E --> F
    
    F --> G
    F --> H
    F --> I
    F --> J
    F --> K
    F --> L
    F --> M
    F --> N
    F --> O
    F --> P
    
    subgraph "Response Types"
        Q[JSON Response]
        R[Streaming Response]
        S[Error Response]
    end
    
    G --> Q
    H --> R
    I --> Q
    J --> Q
    K --> Q
    L --> Q
    M --> Q
    N --> Q
    O --> Q
    P --> Q
    
    style D fill:#e1f5fe
    style F fill:#f3e5f5
    style R fill:#fff3e0
```

## 🔄 Streaming Response Architecture

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    participant A as FSMAgent  
    participant W as Workflow
    participant T as Tools
    participant L as LLM
    
    C->>+S: POST /chat-stream
    Note over S: Setup SSE headers
    
    S->>+A: stream_message()
    A->>+W: astream(state)
    
    loop For each state execution
        W->>+T: Execute tool
        T->>+L: LLM call (if needed)
        L-->>-T: LLM response
        T-->>-W: Tool result
        
        W-->>A: Stream chunk (state_update)
        A-->>S: Yield state chunk
        S-->>C: data: {state_data}
        
        W-->>A: Stream chunk (message)
        A-->>S: Yield message chunk  
        S-->>C: data: {content}
        
        Note over W: State transition
        W->>W: Conditional routing
    end
    
    W-->>-A: Final state
    A-->>S: Yield completion
    S-->>C: event: done\ndata: [DONE]
    S-->>-C: Close stream
```

## 🧩 Conditional Routing Logic

```mermaid
graph TB
    subgraph "Routing Decision Tree"
        A[Current State + User Input]
        A --> B[LLM Analysis]
        B --> C[Intent Classification]
        
        subgraph "Route From INITIAL"
            C --> D{Has Image?}
            D -->|Yes| E[→ CLASSIFYING]
            D -->|No| F[→ FOLLOWUP]
        end
        
        subgraph "Route From CLASSIFYING" 
            C --> G{Success?}
            G -->|Yes| H[→ PRESCRIBING]
            G -->|Retry| I[→ CLASSIFYING]
            G -->|Failed| J[→ ERROR]
        end
        
        subgraph "Route From PRESCRIBING"
            C --> K{Generated?}
            K -->|Yes| L[→ VENDOR_QUERY]
            K -->|Retry| M[→ PRESCRIBING] 
            K -->|Failed| N[→ ERROR]
        end
        
        subgraph "Route From VENDOR_QUERY"
            C --> O{User Response}
            O -->|Yes| P[→ SHOW_VENDORS]
            O -->|No| Q[→ COMPLETED]
            O -->|Unclear| R[→ FOLLOWUP]
        end
        
        subgraph "Route From FOLLOWUP"
            C --> S{Intent Analysis}
            S -->|New Request| T[→ INITIAL]
            S -->|Classify| U[→ CLASSIFYING]
            S -->|Prescribe| V[→ PRESCRIBING]
            S -->|Vendors| W[→ SHOW_VENDORS]
            S -->|Done| X[→ COMPLETED]
        end
    end
    
    style B fill:#e1f5fe
    style C fill:#f3e5f5
    style A fill:#e8f5e8
```

## 🔧 Tool Execution Pipeline

```mermaid
graph LR
    subgraph "Tool Execution Flow"
        A[Tool Input Validation] --> B[Async Wrapper]
        B --> C[Core Logic Execution]
        C --> D[Result Processing]
        D --> E[Error Handling]
        E --> F[Tool Output]
    end
    
    subgraph "ClassificationTool Pipeline"
        G[Image B64 Decode] --> H[CNN Model Load]
        H --> I[Prediction] --> J[Attention Visualization]
        J --> K[Result Formatting]
    end
    
    subgraph "PrescriptionTool Pipeline"
        L[RAG System Init] --> M[Query Building]
        M --> N[Vector Search] --> O[LLM Generation]
        O --> P[Response Parsing]
    end
    
    subgraph "VendorTool Pipeline"
        Q[Location Filtering] --> R[Product Matching]
        R --> S[Price Calculation] --> T[Vendor Ranking]
        T --> U[Response Formatting]
    end
    
    subgraph "ContextExtractorTool Pipeline"
        V[Text Normalization] --> W[Pattern Matching]
        W --> X[NLP Processing] --> Y[Context Extraction]
        Y --> Z[Validation]
    end
    
    C --> G
    C --> L
    C --> Q
    C --> V
    
    K --> F
    P --> F
    U --> F
    Z --> F
    
    style A fill:#e8f5e8
    style C fill:#fff3e0
    style F fill:#e1f5fe
```

## 📱 Session Management Architecture

```mermaid
graph TB
    subgraph "Session Lifecycle"
        A[Session Creation] --> B[State Initialization]
        B --> C[Conversation Processing]
        C --> D[State Updates]
        D --> E[History Tracking]
        E --> F[Session Cleanup]
        F --> G[Session Termination]
    end
    
    subgraph "Session Storage"
        H[In-Memory Store]
        I[Session Metadata]
        J[Conversation History]
        K[State Snapshots]
    end
    
    A --> H
    B --> I
    C --> J
    D --> K
    
    subgraph "Session Operations"
        L[Create Session]
        M[Get Session Info]
        N[Update Session]
        O[End Session]
        P[Cleanup Inactive]
    end
    
    L --> A
    M --> I
    N --> D
    O --> G
    P --> F
    
    subgraph "Session Data Model"
        Q[session_id: str]
        R[created_at: datetime]
        S[last_activity: datetime]
        T[message_count: int]
        U[state: WorkflowState]
        V[is_complete: bool]
    end
    
    H --> Q
    H --> R
    H --> S
    H --> T
    H --> U
    H --> V
    
    style A fill:#e8f5e8
    style H fill:#f3e5f5
    style L fill:#fff3e0
```

## 🚀 Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        A[Local Development]
        B[Auto-reload Server]
        C[Debug Logging]
        D[Test Suite]
    end
    
    subgraph "Production Environment"
        E[Multi-worker Server]
        F[Load Balancer]
        G[Session Persistence]
        H[Monitoring & Metrics]
    end
    
    subgraph "External Dependencies"
        I[Ollama Server]
        J[CNN Model Files]
        K[ChromaDB Data]
        L[Environment Variables]
    end
    
    subgraph "Scaling Options"
        M[Horizontal Scaling]
        N[Session Store (Redis)]
        O[Model Caching]
        P[Rate Limiting]
    end
    
    A --> E
    B --> F
    C --> H
    D --> G
    
    E --> I
    E --> J
    E --> K
    E --> L
    
    F --> M
    G --> N
    H --> O
    I --> P
    
    style A fill:#e8f5e8
    style E fill:#e1f5fe
    style I fill:#fff3e0
```

## 🔄 Error Handling & Recovery

```mermaid
graph TB
    subgraph "Error Types"
        A[Tool Execution Errors]
        B[LLM Connection Errors]  
        C[State Transition Errors]
        D[Session Management Errors]
        E[Validation Errors]
    end
    
    subgraph "Error Handling Strategies"
        F[Retry with Backoff]
        G[Fallback Responses]
        H[Error State Transition]
        I[Session Recovery]
        J[Graceful Degradation]
    end
    
    A --> F
    B --> G
    C --> H
    D --> I
    E --> J
    
    subgraph "Recovery Mechanisms"
        K[Automatic Retry (3x)]
        L[Alternative Tool Path]
        M[Error State Node]
        N[Session Cleanup]
        O[User Notification]
    end
    
    F --> K
    G --> L
    H --> M
    I --> N
    J --> O
    
    subgraph "Monitoring & Logging"
        P[Error Tracking]
        Q[Performance Metrics]
        R[Health Checks]
        S[Alert System]
    end
    
    K --> P
    L --> Q
    M --> R
    N --> S
    
    style A fill:#ffebee
    style F fill:#f3e5f5
    style K fill:#e8f5e8
```

## 🎯 Performance Optimization

```mermaid
graph LR
    subgraph "Performance Layers"
        A[Request Level]
        B[Session Level]
        C[Tool Level]
        D[LLM Level]
        E[Infrastructure Level]
    end
    
    subgraph "Optimization Techniques"
        F[Async Processing]
        G[Connection Pooling]
        H[Result Caching]
        I[Model Optimization]
        J[Resource Management]
    end
    
    A --> F
    B --> G
    C --> H
    D --> I
    E --> J
    
    subgraph "Caching Strategy"
        K[Tool Result Cache]
        L[LLM Response Cache]
        M[Session State Cache]
        N[Static Data Cache]
    end
    
    H --> K
    I --> L
    G --> M
    J --> N
    
    subgraph "Resource Management"
        O[Memory Management]
        P[Connection Limits]
        Q[Cleanup Schedules]
        R[Load Balancing]
    end
    
    F --> O
    G --> P
    H --> Q
    I --> R
    
    style F fill:#e8f5e8
    style H fill:#fff3e0
    style K fill:#e1f5fe
```

## 🔍 Monitoring & Observability

```mermaid
graph TB
    subgraph "Metrics Collection"
        A[Request Metrics]
        B[Session Metrics]
        C[Tool Metrics]
        D[LLM Metrics]
        E[System Metrics]
    end
    
    subgraph "Logging Layers"
        F[Application Logs]
        G[Access Logs]
        H[Error Logs]
        I[Debug Logs]
    end
    
    A --> F
    B --> G
    C --> H
    D --> I
    E --> F
    
    subgraph "Health Monitoring"
        J[Health Endpoint]
        K[Dependency Checks]
        L[Performance Thresholds]
        M[Alert Triggers]
    end
    
    F --> J
    G --> K
    H --> L
    I --> M
    
    subgraph "Analytics Dashboard"
        N[Usage Statistics]
        O[Performance Trends]
        P[Error Analysis]
        Q[User Behavior]
    end
    
    J --> N
    K --> O
    L --> P
    M --> Q
    
    style A fill:#e8f5e8
    style F fill:#fff3e0
    style J fill:#e1f5fe
```

## 🧪 Testing Strategy

```mermaid
graph LR
    subgraph "Test Levels"
        A[Unit Tests]
        B[Integration Tests]
        C[System Tests]
        D[Performance Tests]
    end
    
    subgraph "Test Categories"
        E[Tool Testing]
        F[Workflow Testing]
        G[API Testing]
        H[Session Testing]
    end
    
    A --> E
    B --> F
    C --> G
    D --> H
    
    subgraph "Test Scenarios"
        I[Happy Path Flow]
        J[Error Conditions]
        K[Edge Cases]
        L[Load Testing]
    end
    
    E --> I
    F --> J
    G --> K
    H --> L
    
    subgraph "Test Tools"
        M[pytest & asyncio]
        N[Mock Services]
        O[Test Data Sets]
        P[Performance Profiling]
    end
    
    I --> M
    J --> N
    K --> O
    L --> P
    
    style A fill:#e8f5e8
    style E fill:#fff3e0
    style I fill:#e1f5fe
```

## 📈 Scalability Considerations

```mermaid
graph TB
    subgraph "Scaling Dimensions"
        A[Concurrent Users]
        B[Session Volume]
        C[Tool Execution]
        D[LLM Requests]
        E[Data Storage]
    end
    
    subgraph "Scaling Solutions"
        F[Horizontal Scaling]
        G[Load Distribution]
        H[Async Processing]
        I[Connection Pooling]
        J[Data Partitioning]
    end
    
    A --> F
    B --> G
    C --> H
    D --> I
    E --> J
    
    subgraph "Infrastructure Options"
        K[Multi-instance Deployment]
        L[Container Orchestration]
        M[Distributed Sessions]
        N[External Caching]
        O[Database Scaling]
    end
    
    F --> K
    G --> L
    H --> M
    I --> N
    J --> O
    
    subgraph "Performance Targets"
        P[Response Time < 2s]
        Q[Concurrent Users > 100]
        R[Uptime > 99.9%]
        S[Memory < 2GB per instance]
    end
    
    K --> P
    L --> Q
    M --> R
    N --> S
    
    style A fill:#e8f5e8
    style F fill:#fff3e0
    style K fill:#e1f5fe
```

---

## 🎯 Key Architectural Benefits

### **1. LangGraph Integration**
- **Professional FSM Framework**: Built on LangGraph's proven state management
- **Dynamic Routing**: LLM-powered conditional transitions
- **Tool Integration**: Native LangChain compatibility
- **Streaming Support**: Real-time response delivery

### **2. Modular Design**
- **Pluggable Tools**: Easy to add/modify tools
- **State Isolation**: Clear separation of concerns
- **Error Boundaries**: Robust error handling
- **Session Management**: Scalable conversation tracking

### **3. Production Ready**
- **Async Architecture**: Non-blocking operations
- **Health Monitoring**: Comprehensive observability
- **Graceful Degradation**: Fallback mechanisms
- **Performance Optimization**: Caching and resource management

### **4. Extensible Foundation**
- **New State Addition**: Simple workflow extension
- **Custom Tools**: Standard LangChain interface
- **External Integrations**: Flexible API design
- **Multi-modal Support**: Text, images, and more

This architecture provides a robust, scalable, and maintainable foundation for the plant disease diagnosis and prescription system! 🌱🤖

