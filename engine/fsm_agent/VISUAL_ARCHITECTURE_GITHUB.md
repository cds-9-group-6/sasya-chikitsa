# Dynamic Planning Agent (FSM) - Visual Architecture (GitHub Edition)

## 🏗️ System Overview

```
┌─────────────────────┐    ┌─────────────────────────────────────────┐
│   External          │    │            FSM Agent Server             │
│   Interfaces        │    │             (Port 8002)                 │
│                     │    │                                         │
│  ┌─Android App───┐  │    │  ┌─DynamicPlanningAgent─────────────┐  │
│  │               │  │────┼──│                                   │  │
│  └───────────────┘  │    │  │  ┌─LangGraph Workflow──────────┐ │  │
│                     │    │  │  │                              │ │  │
│  ┌─Web Client────┐  │    │  │  │  ┌─State Machine Engine─┐   │ │  │
│  │               │  │────┼──│  │  │                       │   │ │  │
│  └───────────────┘  │    │  │  │  │  ┌─Conditional───┐   │   │ │  │
│                     │    │  │  │  │  │   Routing     │   │   │ │  │
│  ┌─API Client────┐  │    │  │  │  │  └───────────────┘   │   │ │  │
│  │               │  │────┼──│  │  │                       │   │ │  │
│  └───────────────┘  │    │  │  └──┤  ┌─Tool Executor──┐   │   │ │  │
│                     │    │  │     │  │                 │   │   │ │  │
└─────────────────────┘    │  │     │  └─────────────────┘   │   │ │  │
                           │  │     └─────────────────────────┘   │ │  │
┌─────────────────────┐    │  └─────────────────────────────────────┘ │  │
│  Session Management │    │                                          │  │
│                     │    │  ┌─LangChain Tools─────────────────────┐ │  │
│ ┌─Session Store──┐  │    │  │                                     │ │  │
│ │                │  │────┼──┤ ┌─ClassificationTool────────────┐   │ │  │
│ └────────────────┘  │    │  │ │                               │   │ │  │
│                     │    │  │ └───────────────────────────────┘   │ │  │
│ ┌─Conversation───┐  │    │  │                                     │ │  │
│ │   History      │  │────┼──┤ ┌─PrescriptionTool──────────────┐   │ │  │
│ └────────────────┘  │    │  │ │                               │   │ │  │
│                     │    │  │ └───────────────────────────────┘   │ │  │
│ ┌─State───────────┐ │    │  │                                     │ │  │
│ │  Persistence    │ │────┼──┤ ┌─VendorTool────────────────────┐   │ │  │
│ └─────────────────┘ │    │  │ │                               │   │ │  │
└─────────────────────┘    │  │ └───────────────────────────────┘   │ │  │
                           │  │                                     │ │  │
┌─────────────────────┐    │  │ ┌─ContextExtractorTool─────────┐   │ │  │
│  External Services  │    │  │ │                               │   │ │  │
│                     │    │  │ └───────────────────────────────┘   │ │  │
│ ┌─Ollama LLM─────┐  │────┼──┤                                     │ │  │
│ │   Server       │  │    │  └─────────────────────────────────────┘ │  │
│ └────────────────┘  │    │                                          │  │
│                     │    └──────────────────────────────────────────┘  │
│ ┌─CNN Model──────┐  │                                                   │
│ │   Files        │  │───────────────────────────────────────────────────┘
│ └────────────────┘  │
│                     │
│ ┌─ChromaDB RAG───┐  │
│ │               │  │
│ └───────────────┘  │
│                     │
│ ┌─Vendor─────────┐  │
│ │   Database     │  │
│ └────────────────┘  │
└─────────────────────┘
```

## 🔄 LangGraph StateGraph Flow

### State Transition Diagram

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   INITIAL   │
                    │ Context     │
                    │ Extraction  │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
    ┌───────▼────────┐ ┌───▼──────┐ ┌────▼─────┐
    │  CLASSIFYING   │ │ FOLLOWUP │ │  ERROR   │
    │   CNN Model    │ │ Request  │ │          │
    │   Analysis     │ │  Image   │ │          │
    └───────┬────────┘ └──────────┘ └────┬─────┘
            │                           │
    ┌───────▼────────┐                  │
    │ PRESCRIBING    │                  │
    │ RAG-based      │                  │
    │ Treatments     │                  │
    └───────┬────────┘                  │
            │                           │
    ┌───────▼────────┐                  │
    │ VENDOR_QUERY   │                  │
    │ Ask User       │                  │
    │ Preferences    │                  │
    └───────┬────────┘                  │
            │                           │
    ┌───────▼────────┐                  │
    │ SHOW_VENDORS   │                  │
    │ Display Options│                  │
    │ & Pricing      │                  │
    └───────┬────────┘                  │
            │                           │
    ┌───────▼────────┐                  │
    │ ORDER_BOOKING  │                  │
    │ Process Order  │                  │
    │ with Vendor    │                  │
    └───────┬────────┘                  │
            │                           │
    ┌───────▼────────┐                  │
    │   COMPLETED    │◄─────────────────┘
    │ (Follow-ups)   │
    └────────────────┘
            │
            ▼
        ┌───────┐
        │  END  │
        └───────┘
```

### State Transition Table

| From State | To State | Trigger Condition | LLM Decision |
|------------|----------|-------------------|--------------|
| INITIAL | CLASSIFYING | Has Image + Context | "classify" |
| INITIAL | FOLLOWUP | Request Image/Info | "request_image" |
| INITIAL | ERROR | Invalid Input | "error" |
| CLASSIFYING | PRESCRIBING | Classification Success | "prescribe" |
| CLASSIFYING | CLASSIFYING | Retry (if failed) | "retry" |
| CLASSIFYING | FOLLOWUP | Need More Info | "followup" |
| CLASSIFYING | ERROR | Max Retries Exceeded | "error" |
| PRESCRIBING | VENDOR_QUERY | Prescription Generated | "vendor_query" |
| PRESCRIBING | PRESCRIBING | Retry (if failed) | "retry" |
| PRESCRIBING | COMPLETED | User Wants No Vendors | "complete" |
| PRESCRIBING | ERROR | Max Retries Exceeded | "error" |
| VENDOR_QUERY | SHOW_VENDORS | User Says Yes | "show_vendors" |
| VENDOR_QUERY | COMPLETED | User Says No | "completed" |
| VENDOR_QUERY | FOLLOWUP | Unclear Response | "followup" |
| SHOW_VENDORS | ORDER_BOOKING | Vendor Selected | "order" |
| SHOW_VENDORS | COMPLETED | No Vendors Selected | "completed" |
| SHOW_VENDORS | FOLLOWUP | Need Clarification | "followup" |
| ORDER_BOOKING | FOLLOWUP | Order Placed | "followup" |
| ORDER_BOOKING | COMPLETED | Order Complete | "completed" |
| ORDER_BOOKING | ERROR | Order Failed | "error" |
| FOLLOWUP | INITIAL | New Request | "restart" |
| FOLLOWUP | CLASSIFYING | Reclassify | "classify" |
| FOLLOWUP | PRESCRIBING | Regenerate Prescription | "prescribe" |
| FOLLOWUP | SHOW_VENDORS | Show Vendors Again | "show_vendors" |
| FOLLOWUP | COMPLETED | User Done | "complete" |

## 🧠 State Node Execution Flow

### Sequence Flow

```
User          Server        FSMAgent      Workflow      Tools         LLM
  │              │              │            │            │            │
  ├─POST chat────▶│              │            │            │            │
  │              ├─process_msg───▶│            │            │            │
  │              │              ├─ainvoke────▶│            │            │
  │              │              │            │            │            │
  │              │              │     ┌──────┴──── INITIAL STATE ────┐  │
  │              │              │     │                               │  │
  │              │              │     ├─ContextExtractor─────────────▶│  │
  │              │              │     │◄─────────────── context ──────┤  │
  │              │              │     │                               │  │
  │              │              │     ├─LLM determine action─────────▶│  │
  │              │              │     │◄────────── "classify" ────────┤  │
  │              │              │     │                               │  │
  │              │              │     └─── TRANSITION: INITIAL → CLASSIFYING
  │              │              │     │                               │  │
  │              │              │     ┌─────── CLASSIFYING STATE ────┐  │
  │              │              │     │                               │  │
  │              │              │     ├─ClassificationTool───────────▶│  │
  │              │              │     │◄─────── prediction ──────────┤  │
  │              │              │     │                               │  │
  │              │              │     ├─LLM determine action─────────▶│  │
  │              │              │     │◄────────── "prescribe" ──────┤  │
  │              │              │     │                               │  │
  │              │              │     └─── TRANSITION: CLASSIFYING → PRESCRIBING
  │              │              │     │                               │  │
  │              │              │     ┌─────── PRESCRIBING STATE ────┐  │
  │              │              │     │                               │  │
  │              │              │     ├─PrescriptionTool─────────────▶│  │
  │              │              │     │◄─────── treatments ──────────┤  │
  │              │              │     │                               │  │
  │              │              │     └──────────────────────────────┘  │
  │              │              │            │            │            │
  │              │              │◄───────────┤            │            │
  │              │◄─────────────┤            │            │            │
  │◄─stream─────┤              │            │            │            │
  │   chunks     │              │            │            │            │
```

## 🛠️ Tool Integration Architecture

### Tool Hierarchy

```
LangChain BaseTool Interface
├── Classification Tool
│   ├── CNN Classifier Integration
│   ├── Attention Visualization
│   ├── Base64 Image Processing
│   └── Plant Context Integration
│
├── Prescription Tool  
│   ├── RAG System Query
│   ├── Treatment Parsing
│   ├── Preventive Measures
│   └── Fallback Recommendations
│
├── Vendor Tool
│   ├── Location Filtering
│   ├── Product Matching
│   ├── Price Calculation
│   └── Delivery Estimation
│
└── Context Extractor Tool
    ├── Location Extraction
    ├── Plant Type Detection
    ├── Season Recognition
    ├── Growth Stage Analysis
    └── Symptom Analysis
```

### Tool Execution Pipeline

```
┌─────────────────┐
│ Tool Input      │
│ Validation      │
└─────┬───────────┘
      │
┌─────▼───────────┐
│ Async Wrapper   │
│ (asyncio)       │
└─────┬───────────┘
      │
┌─────▼───────────┐    ┌────────────────────┐
│ Core Logic      │    │ External           │
│ Execution       │◄───┤ Dependencies       │
└─────┬───────────┘    │ • CNN Model        │
      │                │ • RAG System       │
┌─────▼───────────┐    │ • Vendor Database  │
│ Result          │    │ • NLP Patterns     │
│ Processing      │    └────────────────────┘
└─────┬───────────┘
      │
┌─────▼───────────┐
│ Error           │
│ Handling        │
└─────┬───────────┘
      │
┌─────▼───────────┐
│ Tool Output     │
│ (Formatted)     │
└─────────────────┘
```

## 📊 State Schema & Data Flow

### WorkflowState Structure

| Category | Fields | Type | Description |
|----------|--------|------|-------------|
| **Session Management** | `session_id` | `str` | Unique session identifier |
|  | `current_node` | `str` | Current state name |
|  | `previous_node` | `Optional[str]` | Previous state |
| **User Input** | `user_message` | `str` | User's input message |
|  | `user_image` | `Optional[str]` | Base64 encoded image |
| **Context Data** | `user_context` | `Dict[str, Any]` | Extracted context |
|  | `location` | `Optional[str]` | User location |
|  | `season` | `Optional[str]` | Current season |
|  | `plant_type` | `Optional[str]` | Plant type |
|  | `growth_stage` | `Optional[str]` | Growth stage |
| **Classification** | `classification_results` | `Dict[str, Any]` | CNN results |
|  | `disease_name` | `Optional[str]` | Detected disease |
|  | `confidence` | `Optional[float]` | Confidence score |
|  | `attention_overlay` | `Optional[str]` | Attention visualization |
| **Prescription** | `prescription_data` | `Dict[str, Any]` | Treatment data |
|  | `treatment_recommendations` | `List[Dict]` | Treatment list |
|  | `preventive_measures` | `List[str]` | Prevention steps |
| **Vendor Information** | `vendor_options` | `List[Dict]` | Available vendors |
|  | `selected_vendor` | `Optional[Dict]` | Chosen vendor |
|  | `vendor_query_response` | `Optional[str]` | User response |
| **Order Information** | `order_details` | `Dict[str, Any]` | Order data |
|  | `order_status` | `Optional[str]` | Order status |
| **Conversation** | `messages` | `List[Dict]` | Chat history |
| **Flow Control** | `next_action` | `Optional[str]` | Next action |
|  | `requires_user_input` | `bool` | Waiting for input |
|  | `is_complete` | `bool` | Workflow complete |
| **Error Handling** | `error_message` | `Optional[str]` | Error details |
|  | `retry_count` | `int` | Retry attempts |
|  | `max_retries` | `int` | Max retry limit |
|| **Assistant Responses** | `assistant_response` | `Optional[str]` | Streaming responses with follow-ups |

### State Update Flow

```
┌─────────────────────┐
│ User Input          │
│ ┌─ user_message     │
│ ├─ user_image       │
│ └─ context          │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ State Updates       │
│ ┌─ add_message()    │
│ ├─ update_node()    │
│ ├─ set_error()      │
│ └─ mark_complete()  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Persistence         │
│ ┌─ In-Memory        │
│ ├─ Session Store    │
│ ├─ Conversation     │
│ └─ State Snapshots  │
└─────────────────────┘
```

## 🌐 API Architecture & Endpoints

### Endpoint Hierarchy

```
FastAPI Server (Port 8002)
│
├── Core Endpoints
│   ├── POST /sasya-chikitsa/chat
│   ├── POST /sasya-chikitsa/chat-stream
│   ├── GET  /health
│   └── GET  /sasya-chikitsa/stats
│
├── Session Management
│   ├── GET    /sasya-chikitsa/session/{id}
│   ├── GET    /sasya-chikitsa/session/{id}/history
│   ├── GET    /sasya-chikitsa/session/{id}/classification
│   ├── GET    /sasya-chikitsa/session/{id}/prescription
│   └── DELETE /sasya-chikitsa/session/{id}
│
└── Utilities
    └── POST /sasya-chikitsa/cleanup
```

### Request/Response Flow

```
Client Request
      ↓
┌─────────────────┐
│ CORS Middleware │
└─────────┬───────┘
          ↓
┌─────────────────┐
│ Request         │
│ Validation      │
└─────────┬───────┘
          ↓
┌─────────────────┐
│ Route           │
│ Handlers        │
└─────────┬───────┘
          ↓
┌─────────────────┐
│ FSM Agent       │
│ Processing      │
└─────────┬───────┘
          ↓
┌─────────────────┐
│ Response        │
│ Formatting      │
└─────────┬───────┘
          ↓
    Client Response
```

### Response Types

| Type | Format | Use Case |
|------|--------|----------|
| **JSON Response** | `application/json` | Standard API responses |
| **Streaming Response** | `text/plain` (SSE) | Real-time updates |
| **Error Response** | `application/json` | Error conditions |

## 🔄 Streaming Response Architecture

### Server-Sent Events (SSE) Flow

```
Client                    Server                    FSM Agent
  │                         │                         │
  ├─ POST chat-stream ─────▶│                         │
  │                         ├─ Setup SSE headers     │
  │                         │                         │
  │                         ├─ stream_message() ────▶│
  │                         │                         │
  │ ◄─ event: message ─────┤◄─ yield message chunk ─┤
  │    data: "content"      │                         │
  │                         │                         │
  │ ◄─ event: state_update ┤◄─ yield state update ──┤
  │    data: {state_data}   │                         │
  │                         │                         │
  │ ◄─ event: done ────────┤◄─ yield completion ────┤
  │    data: [DONE]         │                         │
  │                         │                         │
  │ ◄─ Connection closed ──┤                         │
```

### Stream Chunk Types

| Event Type | Data Format | Purpose |
|------------|-------------|---------|
| `message` | Plain text | Agent response content |
| `state_update` | JSON object | State transition info |
| `error` | Error string | Error notifications |
| `done` | "[DONE]" | Stream completion |

## 🧩 Conditional Routing Logic

### Routing Decision Matrix

```
Current State + User Input
           ↓
    ┌─────────────┐
    │ LLM Analysis│
    └─────┬───────┘
          ↓
    ┌─────────────┐
    │ Intent      │
    │ Classification │
    └─────┬───────┘
          ↓
┌─────────────────────────────┐
│        Route Decision       │
├─────────────────────────────┤
│ INITIAL                     │
│ ├─ Has Image? → CLASSIFYING │
│ └─ No Image? → FOLLOWUP     │
├─────────────────────────────┤
│ CLASSIFYING                 │
│ ├─ Success? → PRESCRIBING   │
│ ├─ Retry? → CLASSIFYING     │
│ └─ Failed? → ERROR          │
├─────────────────────────────┤
│ PRESCRIBING                 │
│ ├─ Generated? → VENDOR_QUERY│
│ ├─ Retry? → PRESCRIBING     │
│ └─ Failed? → ERROR          │
├─────────────────────────────┤
│ VENDOR_QUERY                │
│ ├─ "Yes" → SHOW_VENDORS     │
│ ├─ "No" → COMPLETED         │
│ └─ Unclear → FOLLOWUP       │
├─────────────────────────────┤
│ FOLLOWUP                    │
│ ├─ New Request → INITIAL    │
│ ├─ Classify → CLASSIFYING   │
│ ├─ Prescribe → PRESCRIBING  │
│ ├─ Vendors → SHOW_VENDORS   │
│ └─ Done → COMPLETED         │
└─────────────────────────────┘
```

### Intent Classification Table

| User Input Pattern | Detected Intent | Next Action |
|-------------------|-----------------|-------------|
| "new", "another", "different" | New Request | → INITIAL |
| "classify", "diagnose", "analyze" | Classification | → CLASSIFYING |
| "prescription", "treatment", "recommend" | Treatment | → PRESCRIBING |
| "vendor", "buy", "purchase", "order" | Vendor Search | → SHOW_VENDORS |
| "done", "finish", "complete", "bye" | Completion | → COMPLETED |
| Image uploaded | Visual Analysis | → CLASSIFYING |
| Error conditions | Error Recovery | → ERROR |
| Unclear intent | Clarification | → FOLLOWUP |

## 📱 Session Management Architecture

### Session Lifecycle

```
Session Creation
      ↓
┌─────────────────┐
│ State           │
│ Initialization  │
└─────┬───────────┘
      ↓
┌─────────────────┐
│ Conversation    │
│ Processing      │
└─────┬───────────┘
      ↓
┌─────────────────┐
│ State Updates   │
└─────┬───────────┘
      ↓
┌─────────────────┐
│ History         │
│ Tracking        │
└─────┬───────────┘
      ↓
┌─────────────────┐
│ Session         │
│ Cleanup         │
└─────┬───────────┘
      ↓
Session Termination
```

### Session Data Model

```
Session {
  session_id: string
  created_at: datetime
  last_activity: datetime
  message_count: integer
  state: WorkflowState {
    current_node: string
    user_context: object
    classification_results: object
    prescription_data: object
    vendor_options: array
    messages: array
    is_complete: boolean
  }
}
```

### Session Operations

| Operation | Endpoint | Description |
|-----------|----------|-------------|
| **Create** | `POST /sasya-chikitsa/chat` | Start new session |
| **Get Info** | `GET /sasya-chikitsa/session/{id}` | Session metadata |
| **Update** | `POST /sasya-chikitsa/chat` | Continue conversation |
| **History** | `GET /sasya-chikitsa/session/{id}/history` | Message history |
| **Results** | `GET /sasya-chikitsa/session/{id}/classification` | Get results |
| **End** | `DELETE /sasya-chikitsa/session/{id}` | Terminate session |
| **Cleanup** | `POST /sasya-chikitsa/cleanup` | Remove inactive |

## 🚀 Deployment Architecture

### Environment Comparison

| Aspect | Development | Production |
|--------|-------------|------------|
| **Server Mode** | Single worker, auto-reload | Multi-worker, stable |
| **Logging** | Debug level, console | Info level, files |
| **Session Storage** | In-memory | External store (Redis) |
| **Load Balancing** | None | Nginx/HAProxy |
| **Monitoring** | Basic health check | Full metrics suite |
| **Dependencies** | Local Ollama | Distributed LLM |

### Scaling Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│                   (Nginx/HAProxy)                       │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
┌─────────▼──┐ ┌──────▼──┐ ┌──────▼──┐
│ FSM Agent  │ │FSM Agent│ │FSM Agent│
│ Instance 1 │ │Instance2│ │Instance3│
└─────────┬──┘ └────┬────┘ └────┬────┘
          │         │           │
          └─────────┼───────────┘
                    │
┌─────────────────────┴───────────────────────┐
│            Shared Services                  │
├─────────────────────────────────────────────┤
│ ┌─Session Store─┐  ┌─Model Cache─┐          │
│ │   (Redis)     │  │  (Local)    │          │
│ └───────────────┘  └─────────────┘          │
│                                             │
│ ┌─External LLM──┐  ┌─Vector DB───┐          │
│ │   (Ollama)    │  │ (ChromaDB)  │          │
│ └───────────────┘  └─────────────┘          │
└─────────────────────────────────────────────┘
```

## 🔍 Monitoring & Observability

### Metrics Collection

```
Application Layer
├── Request Metrics
│   ├── Response Time
│   ├── Success Rate
│   ├── Error Rate
│   └── Throughput
│
├── Session Metrics  
│   ├── Active Sessions
│   ├── Session Duration
│   ├── Messages per Session
│   └── Completion Rate
│
├── Tool Metrics
│   ├── Classification Accuracy
│   ├── Prescription Quality
│   ├── Vendor Match Rate
│   └── Context Extraction Rate
│
└── System Metrics
    ├── Memory Usage
    ├── CPU Utilization
    ├── Network I/O
    └── Disk Usage
```

### Health Monitoring

| Check | Endpoint | Criteria |
|-------|----------|----------|
| **Basic Health** | `/health` | HTTP 200, response < 5s |
| **Dependency Health** | `/health` | Ollama connectivity |
| **Performance** | `/sasya-chikitsa/stats` | Active sessions < 1000 |
| **Error Rate** | Logs | Error rate < 5% |

### Logging Architecture

```
┌─────────────────┐
│ Application     │
│ Logs            │
├─────────────────┤
│ • State Trans.  │
│ • Tool Exec.    │
│ • User Actions  │
│ • Errors        │
└─────┬───────────┘
      │
┌─────▼───────────┐
│ Structured      │
│ Logging         │
├─────────────────┤
│ • JSON Format   │
│ • Timestamps    │
│ • Session IDs   │
│ • Correlation   │
└─────┬───────────┘
      │
┌─────▼───────────┐
│ Log             │
│ Aggregation     │
├─────────────────┤
│ • ELK Stack     │
│ • Grafana       │
│ • Prometheus    │
└─────────────────┘
```

## 🧪 Testing Strategy

### Test Pyramid

```
                  ┌─────────────────┐
                  │  System Tests   │
                  │ ┌─────────────┐ │
                  │ │ Performance │ │
                  │ │ End-to-End  │ │
                  │ │ Integration │ │
                  │ └─────────────┘ │
                  └─────────────────┘
                ┌─────────────────────┐
                │  Integration Tests  │
                │ ┌─────────────────┐ │
                │ │ API Endpoints   │ │
                │ │ Workflow Tests  │ │
                │ │ Tool Integration│ │
                │ └─────────────────┘ │
                └─────────────────────┘
            ┌─────────────────────────────┐
            │        Unit Tests           │
            │ ┌─────────────────────────┐ │
            │ │ Tool Functions          │ │
            │ │ State Logic             │ │
            │ │ Context Extraction      │ │
            │ │ Utility Functions       │ │
            │ └─────────────────────────┘ │
            └─────────────────────────────┘
```

### Test Categories

| Category | Scripts | Coverage |
|----------|---------|----------|
| **Classification** | `test_fsm_classification.sh` | CNN, attention, image processing |
| **Context Extraction** | `test_context_extraction.sh` | NLP, location, plant detection |
| **Vendor Integration** | `test_vendor_integration.sh` | Search, pricing, ordering |
| **Streaming Workflow** | `test_streaming_workflow.sh` | End-to-end flow |
| **Performance** | `test_performance_load.sh` | Load, concurrency, timing |
| **Error Handling** | `test_error_handling.sh` | Edge cases, recovery |

### Test Execution Flow

```
Pre-flight Check
      ↓
┌─────────────────┐
│ Server Health   │
│ Dependency      │
│ Availability    │
└─────┬───────────┘
      ↓
┌─────────────────┐
│ Individual      │
│ Test Execution  │
└─────┬───────────┘
      ↓
┌─────────────────┐
│ Result          │
│ Collection      │
└─────┬───────────┘
      ↓
┌─────────────────┐
│ Report          │
│ Generation      │
└─────┬───────────┘
      ↓
┌─────────────────┐
│ Cleanup &       │
│ Summary         │
└─────────────────┘
```

## 📈 Performance Optimization

### Optimization Layers

```
┌─────────────────────────────────────┐
│            Request Level            │
├─────────────────────────────────────┤
│ • Async Processing                  │
│ • Non-blocking I/O                  │
│ • Parallel Tool Execution           │
└─────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────┐
│           Session Level             │
├─────────────────────────────────────┤
│ • Connection Pooling                │
│ • Session Reuse                     │
│ • State Persistence                 │
└─────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────┐
│            Tool Level               │
├─────────────────────────────────────┤
│ • Result Caching                    │
│ • Model Optimization                │
│ • Batch Processing                  │
└─────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────┐
│         Infrastructure Level        │
├─────────────────────────────────────┤
│ • Load Balancing                    │
│ • Resource Management               │
│ • Distributed Processing            │
└─────────────────────────────────────┘
```

### Caching Strategy

| Layer | Cache Type | TTL | Purpose |
|-------|------------|-----|---------|
| **Tool Results** | In-memory | 5 min | Avoid duplicate processing |
| **LLM Responses** | Redis | 1 hour | Common query responses |
| **Session Data** | In-memory | 24 hours | Active session state |
| **Static Data** | Local | Permanent | Model files, configs |

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Response Time** | < 2s | 95th percentile |
| **Concurrent Users** | > 100 | Simultaneous sessions |
| **Throughput** | > 50 req/s | Sustained load |
| **Memory Usage** | < 2GB | Per instance |
| **CPU Usage** | < 80% | Average load |
| **Uptime** | > 99.9% | Monthly availability |

## 🛡️ Error Handling & Recovery

### Error Classification

```
┌─────────────────────┐
│   Input Errors      │
├─────────────────────┤
│ • Empty messages    │
│ • Invalid JSON      │
│ • Malformed images  │
│ • Missing fields    │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Processing Errors  │
├─────────────────────┤
│ • Tool failures     │
│ • LLM timeouts      │
│ • Model errors      │
│ • State conflicts   │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  System Errors      │
├─────────────────────┤
│ • Resource limits   │
│ • Network issues    │
│ • Service outages   │
│ • Database errors   │
└─────────────────────┘
```

### Recovery Mechanisms

| Error Type | Strategy | Implementation |
|------------|----------|----------------|
| **Tool Execution** | Retry with Backoff | 3 attempts, exponential delay |
| **LLM Connection** | Fallback Responses | Pre-generated responses |
| **State Transition** | Error State Node | Dedicated error handling |
| **Session Management** | Session Recovery | State reconstruction |
| **Resource Exhaustion** | Graceful Degradation | Load shedding |

### Error Recovery Flow

```
Error Detected
      ↓
┌─────────────────┐
│ Error           │
│ Classification  │
└─────┬───────────┘
      │
┌─────▼───────────┐
│ Recovery        │
│ Strategy        │
│ Selection       │
└─────┬───────────┘
      │
┌─────▼───────────┐
│ Recovery        │
│ Action          │
│ Execution       │
└─────┬───────────┘
      │
┌─────▼───────────┐
│ Success?        │
│ ┌─ Yes → Resume │
│ └─ No → Escalate│
└─────────────────┘
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
- **Error Boundaries**: Robust error handling at each layer
- **Session Management**: Scalable conversation tracking

### **3. Production Ready**
- **Async Architecture**: Non-blocking operations throughout
- **Health Monitoring**: Comprehensive observability
- **Graceful Degradation**: Multiple fallback mechanisms
- **Performance Optimization**: Multi-layer caching and resource management

### **4. Extensible Foundation**
- **New State Addition**: Simple workflow extension via LangGraph
- **Custom Tools**: Standard LangChain interface for easy integration
- **External Integrations**: Flexible API design for third-party services
- **Multi-modal Support**: Text, images, and future modalities

This architecture provides a **robust, scalable, and maintainable foundation** for the plant disease diagnosis and prescription system using modern AI/ML patterns and production-ready infrastructure! 🌱🤖

