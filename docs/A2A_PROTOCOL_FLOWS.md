# A2A Protocol Implementation and Request Flows

## 📋 Table of Contents

1. [A2A Protocol Overview](#a2a-protocol-overview)
2. [Agent Registration and Discovery](#agent-registration-and-discovery)
3. [Message Format and Communication](#message-format-and-communication)
4. [Request Flow Patterns](#request-flow-patterns)
5. [Agent Capability Declarations](#agent-capability-declarations)
6. [Error Handling in A2A Communication](#error-handling-in-a2a-communication)
7. [Performance and Monitoring](#performance-and-monitoring)

---

## 🌐 A2A Protocol Overview

The Sasya Chikitsa multi-agent system implements the Agent-to-Agent (A2A) protocol using the [python-a2a](https://python-a2a.readthedocs.io/) library, which provides a production-ready implementation of Google's Agent-to-Agent communication standard.

### Key Components

```mermaid
graph TB
    subgraph "A2A Protocol Stack"
        Application[🎯 Application Layer<br/>Agent Business Logic]
        A2ALib[📚 Python-A2A Library<br/>Protocol Implementation] 
        Transport[🌐 Transport Layer<br/>HTTP/WebSocket]
        Network[🔗 Network Layer<br/>TCP/IP]
    end
    
    subgraph "A2A Components"
        Server[🖥️ A2A Server<br/>Message Handler]
        Client[📤 A2A Client<br/>Request Sender]
        Registry[📋 Agent Registry<br/>Service Discovery]
        Card[🎫 Agent Card<br/>Capability Declaration]
    end
    
    subgraph "Message Flow"
        Message[📨 A2A Message<br/>Standardized Format]
        Content[📄 Content<br/>Text/Binary/Multimodal]
        Metadata[🏷️ Metadata<br/>Context Information]
        Response[📬 Response<br/>Result Data]
    end
    
    Application --> A2ALib
    A2ALib --> Transport
    Transport --> Network
    
    Server --> Registry
    Client --> Message
    Message --> Content
    Content --> Response
    
    Registry --> Card
    Card --> Metadata
```

### Protocol Benefits

- **Standardization**: Follows Google's A2A specification
- **Interoperability**: Compatible with other A2A-compliant systems
- **Scalability**: Built for distributed agent architectures
- **Reliability**: Built-in error handling and retry mechanisms
- **Discovery**: Automatic agent registration and capability discovery
- **Security**: Authentication and authorization support
- **Monitoring**: Built-in metrics and health checking

---

## 🔍 Agent Registration and Discovery

### Agent Registration Process

```mermaid
sequenceDiagram
    participant A as Agent Instance
    participant AS as A2A Server
    participant AR as Agent Registry
    participant AC as Agent Card
    
    Note over A,AC: Agent Startup and Registration
    
    A->>+AS: Initialize A2A Server
    AS->>+AC: Create Agent Card
    Note right of AC: Agent metadata:<br/>- name<br/>- description<br/>- capabilities<br/>- endpoints<br/>- version
    AC-->>-AS: Agent Card Created
    
    AS->>+AR: Register Agent
    Note right of AS: Register with:<br/>- Agent card<br/>- Service endpoints<br/>- Health check URL<br/>- Capability list
    AR-->>-AS: Registration Successful
    
    AS-->>-A: A2A Server Ready
    
    Note over A,AC: Agent is now discoverable<br/>by other agents in the system
    
    loop Health Check Updates
        AR->>+AS: Health Check Ping
        AS->>+A: Check Agent Status  
        A-->>-AS: Status: Healthy
        AS-->>-AR: Agent Status Update
    end
    
    Note over A,AC: Continuous health monitoring<br/>ensures service reliability
```

### Agent Discovery Flow

```mermaid
sequenceDiagram
    participant O as Orchestration Agent
    participant AR as Agent Registry
    participant DA as Diagnostics Agent
    participant PA as Prescription Agent
    participant CA as Crop Care Agent
    participant VA as Vendor Agent
    
    Note over O,VA: Multi-Agent Discovery Process
    
    O->>+AR: Discover Available Agents
    Note right of O: Query: "agents with plant_diagnosis capability"
    
    AR->>AR: Search Registered Agents
    Note right of AR: Filter by:<br/>- Capability match<br/>- Health status<br/>- Load balancing<br/>- Geographic proximity
    
    AR-->>-O: Agent Discovery Results
    Note right of AR: {<br/>  "diagnostics_agent": {<br/>    "agent_id": "diag_001",<br/>    "capabilities": ["diagnose_plant", "classify_image"],<br/>    "endpoint": "http://localhost:8080/diagnostics",<br/>    "health": "healthy",<br/>    "load": "low"<br/>  },<br/>  "prescription_agent": {...},<br/>  "crop_care_agent": {...},<br/>  "vendor_agent": {...}<br/>}
    
    O->>O: Cache Agent Information
    Note right of O: Cache TTL: 5 minutes<br/>Reduces registry queries<br/>Improves performance
    
    O->>O: Create Execution Plan
    Note right of O: Select optimal agents<br/>based on capabilities,<br/>load, and requirements
    
    Note over O,VA: Discovery enables dynamic<br/>agent selection and load balancing
```

### Agent Card Declaration

```python
# Example Agent Card for Diagnostics Agent
agent_card = AgentCard(
    name="Multimodal Diagnostics Agent",
    description="Advanced plant disease diagnosis using CNN and multimodal analysis",
    url="http://localhost:8080/agents/diagnostics",
    version="2.1.0",
    provider="sasya-chikitsa",
    documentation_url="https://sasya-chikitsa.com/docs/diagnostics-agent",
    authentication=None,
    capabilities={
        "primary_functions": [
            "diagnose_plant",
            "classify_image", 
            "analyze_text_symptoms",
            "process_video",
            "synthesize_multimodal_results"
        ],
        "supported_media_types": ["image/jpeg", "image/png", "video/mp4", "text/plain"],
        "supported_plant_types": ["tomato", "potato", "pepper", "eggplant", "cucumber"],
        "supported_diseases": [
            "early_blight", "late_blight", "bacterial_spot", 
            "mosaic_virus", "leaf_curl", "powdery_mildew"
        ],
        "response_time": "2-5 seconds",
        "confidence_threshold": 0.7,
        "attention_visualization": True,
        "batch_processing": False,
        "max_concurrent_requests": 10
    },
    metadata={
        "model_version": "cnn_attention_v2.1", 
        "training_data": "plant_disease_dataset_2024",
        "accuracy": 0.92,
        "supported_languages": ["en", "hi", "mr"],
        "deployment_region": "asia-south1",
        "resource_requirements": {
            "cpu": "2 cores",
            "memory": "4GB", 
            "gpu": "optional"
        }
    }
)
```

---

## 📨 Message Format and Communication

### A2A Message Structure

```python
# A2A Message Components
class A2AMessage:
    """Standard A2A message format"""
    
    # Message Content
    content: Union[TextContent, BinaryContent, MultimodalContent]
    
    # Message Metadata  
    role: MessageRole  # AGENT, USER, SYSTEM
    conversation_id: str  # Session identifier
    message_id: str  # Unique message ID
    
    # A2A Protocol Fields
    source_agent: str  # Sending agent ID
    target_agent: str  # Receiving agent ID
    operation: str  # Requested operation
    priority: int  # Message priority (1-10)
    
    # Context and State
    context: Dict[str, Any]  # Request context
    state: Dict[str, Any]  # Conversation state
    metadata: Dict[str, Any]  # Additional metadata
    
    # Timestamps
    created_at: datetime
    expires_at: Optional[datetime]
    
    # Error Handling
    retry_count: int = 0
    max_retries: int = 3
```

### Message Flow Example

```mermaid
sequenceDiagram
    participant O as Orchestration Agent
    participant AC as A2A Client (Orchestrator)
    participant AS as A2A Server (Diagnostics)
    participant D as Diagnostics Agent
    
    Note over O,D: A2A Message Communication Flow
    
    O->>O: 📝 Create Agent Request
    Note right of O: Operation: diagnose_plant<br/>Context: user query + image<br/>Priority: high
    
    O->>+AC: 📤 Send A2A Message
    Note right of O: Message content:<br/>- TextContent: task parameters<br/>- BinaryContent: image data<br/>- Metadata: session context
    
    AC->>AC: 🔧 Format A2A Message
    Note right of AC: Standard A2A format:<br/>- Message headers<br/>- Content encoding<br/>- Authentication tokens<br/>- Routing information
    
    AC->>+AS: 🌐 HTTP POST to Agent Endpoint
    Note right of AC: POST /agents/diagnostics/a2a<br/>Content-Type: application/json<br/>Authorization: Bearer token
    
    AS->>AS: ✅ Validate Message Format
    Note right of AS: Validate:<br/>- A2A protocol compliance<br/>- Authentication<br/>- Content integrity<br/>- Rate limiting
    
    AS->>+D: 📋 Route to Agent Handler
    Note right of AS: Extract:<br/>- Operation: diagnose_plant<br/>- Parameters: task data<br/>- Context: session info
    
    D->>D: 🔄 Process Request
    Note right of D: Execute:<br/>- Image classification<br/>- Attention generation<br/>- Result synthesis
    
    D-->>-AS: 📊 Agent Response
    Note right of D: Response includes:<br/>- Processing results<br/>- Confidence scores<br/>- Error status<br/>- Execution metadata
    
    AS->>AS: 🔧 Format A2A Response
    Note right of AS: Standard response:<br/>- Result payload<br/>- Status codes<br/>- Timing information<br/>- Error details (if any)
    
    AS-->>-AC: 🌐 HTTP Response
    Note right of AS: 200 OK<br/>Content-Type: application/json<br/>Response body: A2A message
    
    AC->>AC: ✅ Validate Response
    Note right of AC: Check:<br/>- Response format<br/>- Content integrity<br/>- Error conditions
    
    AC-->>-O: 📬 Parsed Response
    Note right of AC: Extract:<br/>- Agent results<br/>- Execution status<br/>- Performance metrics
    
    Note over O,D: Complete A2A message round-trip<br/>with validation and error handling
```

### Content Types and Encoding

```python
# A2A Content Types
from python_a2a.models.content import TextContent, BinaryContent, MultimodalContent

# Text Content (JSON parameters)
text_content = TextContent(
    text=json.dumps({
        "operation": "diagnose_plant",
        "user_query": "What disease is this?",
        "context": {
            "location": "Maharashtra, India",
            "season": "monsoon",
            "plant_type": "tomato"
        }
    })
)

# Binary Content (Image data)
binary_content = BinaryContent(
    data=base64.b64decode(image_base64),
    mime_type="image/jpeg",
    filename="plant_image.jpg"
)

# Multimodal Content (Combined data)
multimodal_content = MultimodalContent(
    parts=[
        {"type": "text", "content": task_parameters},
        {"type": "image", "content": image_data, "mime_type": "image/jpeg"},
        {"type": "metadata", "content": context_data}
    ]
)

# A2A Message Construction
message = Message(
    content=multimodal_content,
    role=MessageRole.AGENT,
    conversation_id=session_id,
    metadata={
        "source_agent": "orchestrator",
        "target_agent": "diagnostics",
        "operation": "diagnose_plant",
        "priority": 8,
        "timeout": 60,
        "retry_policy": "exponential_backoff"
    }
)
```

---

## 🔄 Request Flow Patterns

### Pattern 1: Simple Agent-to-Agent Request

```mermaid
sequenceDiagram
    participant O as Orchestration Agent
    participant C as Crop Care Agent
    
    Note over O,C: Simple A2A Request Pattern
    
    O->>O: 📋 Analyze User Intent
    Note right of O: Intent: GENERAL_CROP_CARE<br/>Agent Required: crop_care<br/>Operation: provide_care_advice
    
    O->>+C: 📨 A2A Message (provide_care_advice)
    Note right of O: {<br/>  "operation": "provide_care_advice",<br/>  "query": "How to grow tomatoes?",<br/>  "context": {<br/>    "location": "India",<br/>    "season": "winter",<br/>    "experience": "beginner"<br/>  }<br/>}
    
    C->>C: 🤖 Process Agricultural Query
    Note right of C: - Classify query type<br/>- Generate recommendations<br/>- Add seasonal considerations<br/>- Format response
    
    C-->>-O: 📬 A2A Response
    Note right of C: {<br/>  "success": true,<br/>  "response": "Winter tomato cultivation guide...",<br/>  "recommendations": [...],<br/>  "seasonal_tips": [...],<br/>  "confidence": 0.92<br/>}
    
    O->>O: 📝 Process Agent Response  
    Note right of O: - Extract recommendations<br/>- Format for user<br/>- Add contextual notes
    
    Note over O,C: Single agent execution<br/>Latency: ~1-2 seconds
```

### Pattern 2: Sequential Multi-Agent Workflow

```mermaid
sequenceDiagram
    participant O as Orchestration Agent
    participant D as Diagnostics Agent  
    participant P as Prescription Agent
    
    Note over O,P: Sequential Multi-Agent Pattern
    
    O->>O: 📋 Analyze Complex Intent
    Note right of O: Intent: DISEASE_DIAGNOSIS + TREATMENT<br/>Agents: [diagnostics, prescription]<br/>Execution: sequential
    
    rect rgb(255, 248, 248)
        Note over O,D: Phase 1: Diagnosis
        O->>+D: 📨 A2A Message (diagnose_plant)
        Note right of O: Include:<br/>- Plant image<br/>- User description<br/>- Environmental context
        
        D->>D: 🧠 CNN Classification + Analysis
        D-->>-O: 📬 Diagnostic Results
        Note right of D: {<br/>  "disease": "Early Blight",<br/>  "confidence": 0.87,<br/>  "severity": "moderate",<br/>  "affected_area": "25%"<br/>}
    end
    
    rect rgb(248, 255, 248)  
        Note over O,P: Phase 2: Treatment Planning
        O->>+P: 📨 A2A Message (generate_prescription)
        Note right of O: Include diagnostic context:<br/>{<br/>  "diagnosis_results": {<br/>    "disease": "Early Blight",<br/>    "severity": "moderate",<br/>    "plant_type": "tomato"<br/>  },<br/>  "environmental_context": {...}<br/>}
        
        P->>P: 📚 RAG Query + Treatment Generation
        Note right of P: - Query knowledge base<br/>- Generate treatment plan<br/>- Calculate dosages<br/>- Create schedule
        
        P-->>-O: 📬 Treatment Plan
        Note right of P: {<br/>  "treatment": "Copper oxychloride spray",<br/>  "schedule": "Every 7 days for 3 weeks",<br/>  "dosage": "2ml per liter",<br/>  "monitoring": [...]<br/>}
    end
    
    O->>O: 🔧 Synthesize Final Response
    Note right of O: Combine:<br/>- Diagnostic findings<br/>- Treatment recommendations<br/>- Implementation guidance
    
    Note over O,P: Sequential execution with context passing<br/>Total latency: ~4-6 seconds
```

### Pattern 3: Parallel Multi-Agent Execution

```mermaid
sequenceDiagram
    participant O as Orchestration Agent
    participant D as Diagnostics Agent
    participant C as Crop Care Agent
    participant V as Vendor Agent
    
    Note over O,V: Parallel Multi-Agent Pattern
    
    O->>O: 📋 Analyze Complex Intent
    Note right of O: Intent: COMPREHENSIVE_PLANT_CARE<br/>Agents: [diagnostics, crop_care, vendor]<br/>Execution: parallel (where possible)
    
    rect rgb(240, 248, 255)
        Note over O,V: Parallel Execution Phase
        
        par Diagnostics Track
            O->>+D: 📨 A2A Message (diagnose_plant)
            Note right of O: Primary track:<br/>Disease identification
            D->>D: 🧠 CNN Processing
            D-->>-O: 📬 Diagnostic Results
        and Crop Care Track
            O->>+C: 📨 A2A Message (general_care_advice)
            Note right of O: Parallel track:<br/>General plant care
            C->>C: 🤖 Agricultural Guidance
            C-->>-O: 📬 Care Recommendations
        and Vendor Search Track
            O->>+V: 📨 A2A Message (search_products)
            Note right of O: Parallel track:<br/>Product availability
            V->>V: 🛒 Product Search
            V-->>-O: 📬 Product Options
        end
    end
    
    O->>O: 🔧 Synthesize Combined Response
    Note right of O: Merge all agent responses:<br/>- Diagnostic findings<br/>- Care recommendations<br/>- Product suggestions<br/>- Integrated action plan
    
    Note over O,V: Parallel execution reduces latency<br/>Total time: ~3-4 seconds (vs 8-10 sequential)
```

### Pattern 4: Conditional Agent Routing

```mermaid
sequenceDiagram
    participant O as Orchestration Agent
    participant D as Diagnostics Agent
    participant P as Prescription Agent
    participant C as Crop Care Agent
    
    Note over O,C: Conditional Routing Pattern
    
    O->>O: 📋 Initial Intent Analysis
    Note right of O: User query analysis:<br/>Ambiguous intent detected<br/>Multiple possibilities
    
    O->>+D: 📨 A2A Message (diagnose_plant)
    Note right of O: First, check if disease present
    
    D->>D: 🧠 Disease Detection
    D-->>-O: 📬 Diagnostic Results
    Note right of D: Result: No disease detected<br/>Plant appears healthy<br/>Confidence: 0.91
    
    alt Disease Detected
        Note over O,P: If disease found → Treatment path
        O->>P: A2A Message (generate_prescription)
        P-->>O: Treatment recommendations
    else No Disease (Healthy Plant)
        Note over O,C: If healthy → General care path
        O->>+C: 📨 A2A Message (provide_care_advice)
        Note right of O: Focus on:<br/>- Preventive care<br/>- Nutrition optimization<br/>- Growth enhancement
        
        C->>C: 🌱 Healthy Plant Care Guidance
        Note right of C: Generate:<br/>- Fertilization schedule<br/>- Pruning recommendations<br/>- Pest prevention<br/>- Yield optimization
        
        C-->>-O: 📬 Care Enhancement Plan
    else Inconclusive Results
        Note over O,C: If uncertain → Multiple agent consultation
        par Prescription Consultation
            O->>P: A2A Message (assess_plant_health)
            P-->>O: Health assessment
        and Care Consultation  
            O->>C: A2A Message (comprehensive_evaluation)
            C-->>O: Detailed evaluation
        end
    end
    
    O->>O: 🔧 Process Conditional Results
    Note right of O: Route based on:<br/>- Diagnostic confidence<br/>- User needs<br/>- Agent recommendations
    
    Note over O,C: Dynamic routing based on<br/>intermediate results and conditions
```

---

## 🎯 Agent Capability Declarations

### Capability Registration System

```python
class AgentCapabilityManager:
    """Manage and declare agent capabilities for A2A discovery"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.capabilities = self._initialize_capabilities()
        
    def _initialize_capabilities(self) -> Dict[str, Any]:
        """Initialize agent-specific capabilities"""
        
        if self.agent_type == AgentType.DIAGNOSTICS:
            return {
                "primary_operations": [
                    {
                        "name": "diagnose_plant",
                        "description": "Comprehensive plant disease diagnosis",
                        "input_types": ["image", "text", "video"],
                        "output_format": "structured_diagnosis",
                        "average_latency": "3-5 seconds",
                        "confidence_threshold": 0.7,
                        "supported_formats": ["jpeg", "png", "mp4"]
                    },
                    {
                        "name": "classify_image", 
                        "description": "Image-only disease classification",
                        "input_types": ["image"],
                        "output_format": "classification_result",
                        "average_latency": "2-3 seconds",
                        "batch_support": True,
                        "max_batch_size": 5
                    }
                ],
                "specialized_features": {
                    "attention_visualization": {
                        "enabled": True,
                        "color_schemes": ["blue_yellow", "red_yellow", "grayscale"],
                        "overlay_formats": ["base64_png", "coordinates"],
                        "clickable_regions": True
                    },
                    "multimodal_fusion": {
                        "image_text_combination": True,
                        "video_frame_analysis": True,
                        "temporal_analysis": False
                    }
                },
                "supported_plant_types": [
                    "tomato", "potato", "pepper", "eggplant", "cucumber",
                    "cabbage", "cauliflower", "lettuce", "spinach"
                ],
                "disease_categories": [
                    "fungal", "bacterial", "viral", "nutritional", "pest_damage"
                ],
                "performance_metrics": {
                    "accuracy": 0.92,
                    "precision": 0.89,
                    "recall": 0.94,
                    "f1_score": 0.91
                }
            }
            
        elif self.agent_type == AgentType.PRESCRIPTION:
            return {
                "primary_operations": [
                    {
                        "name": "generate_prescription",
                        "description": "Create tailored treatment plans",
                        "input_requirements": ["disease_diagnosis", "plant_context"],
                        "output_format": "structured_prescription",
                        "customization_level": "high",
                        "average_latency": "1-3 seconds"
                    },
                    {
                        "name": "query_rag_knowledge",
                        "description": "Query treatment knowledge base",
                        "knowledge_domains": ["treatments", "products", "schedules"],
                        "search_methods": ["semantic", "keyword", "similarity"],
                        "response_format": "ranked_results"
                    }
                ],
                "knowledge_base": {
                    "treatment_database": {
                        "size": "50,000+ treatments",
                        "coverage": "comprehensive",
                        "update_frequency": "monthly",
                        "languages": ["english", "hindi"]
                    },
                    "product_database": {
                        "organic_treatments": 1200,
                        "chemical_treatments": 800,
                        "biological_controls": 400,
                        "local_availability": True
                    }
                },
                "customization_factors": [
                    "disease_severity",
                    "plant_growth_stage", 
                    "environmental_conditions",
                    "farmer_preferences",
                    "budget_constraints",
                    "organic_vs_chemical"
                ]
            }
            
        # Similar capability definitions for other agents...
        
    def get_capability_declaration(self) -> Dict[str, Any]:
        """Get formatted capability declaration for A2A registration"""
        return {
            "agent_type": self.agent_type.value,
            "capabilities": self.capabilities,
            "service_level": {
                "availability": "99.5%",
                "max_concurrent_requests": 10,
                "rate_limiting": "100 requests/minute",
                "timeout_policy": "60 seconds"
            },
            "integration": {
                "a2a_protocol_version": "1.0",
                "message_formats": ["json", "binary", "multimodal"],
                "authentication_methods": ["bearer_token", "api_key"],
                "health_check_endpoint": "/health"
            }
        }
```

### Dynamic Capability Updates

```mermaid
sequenceDiagram
    participant A as Agent
    participant CM as Capability Manager  
    participant AR as Agent Registry
    participant O as Orchestration Agent
    
    Note over A,O: Dynamic Capability Management
    
    A->>A: 🔄 Model Update/Enhancement
    Note right of A: - New CNN model deployed<br/>- Additional plant types supported<br/>- Improved accuracy metrics
    
    A->>+CM: 📋 Update Capability Declaration
    Note right of A: New capabilities:<br/>- Support for 5 new plant types<br/>- Improved accuracy: 0.94<br/>- Reduced latency: 2-4 seconds
    
    CM->>CM: ✅ Validate Capability Changes
    Note right of CM: Check:<br/>- Capability format<br/>- Performance claims<br/>- Backward compatibility
    
    CM->>+AR: 📤 Register Updated Capabilities
    Note right of CM: Update agent registry with:<br/>- New capability list<br/>- Updated performance metrics<br/>- Version information
    
    AR->>AR: 🔄 Update Agent Records
    Note right of AR: - Merge capability changes<br/>- Version capability definitions<br/>- Notify dependent services
    
    AR-->>-CM: ✅ Capability Update Confirmed
    CM-->>-A: 📋 Update Successful
    
    rect rgb(240, 255, 240)
        Note over AR,O: Capability Change Propagation
        AR->>+O: 📢 Capability Change Notification
        Note right of AR: Notify orchestrators:<br/>- Agent capability changes<br/>- Performance improvements<br/>- New operation availability
        
        O->>O: 🔄 Update Agent Cache
        Note right of O: Refresh cached information:<br/>- Available operations<br/>- Expected latencies<br/>- Routing preferences
        
        O-->>-AR: ✅ Notification Acknowledged
    end
    
    Note over A,O: Dynamic capability updates enable<br/>continuous system improvement
```

---

## ⚠️ Error Handling in A2A Communication

### A2A Error Categories

```mermaid
graph TB
    subgraph "A2A Error Types"
        CommErr[🌐 Communication Errors<br/>Network failures, timeouts]
        ProtErr[📋 Protocol Errors<br/>Invalid message format]
        AuthErr[🔐 Authentication Errors<br/>Invalid credentials]
        CapErr[🎯 Capability Errors<br/>Unsupported operations]
        ProcErr[⚙️ Processing Errors<br/>Agent-specific failures]
    end
    
    subgraph "Error Handling Strategies"
        Retry[🔄 Retry Logic<br/>Exponential backoff]
        Fallback[🛡️ Fallback Services<br/>Alternative agents]
        Circuit[⚡ Circuit Breakers<br/>Service protection]
        Cache[💾 Response Caching<br/>Recent results]
    end
    
    CommErr --> Retry
    ProtErr --> Fallback
    AuthErr --> Circuit
    CapErr --> Cache
    ProcErr --> Retry
```

### Error Recovery Flow

```mermaid
sequenceDiagram
    participant O as Orchestration Agent
    participant AC as A2A Client
    participant AS as A2A Server (Primary)
    participant ASB as A2A Server (Backup)
    participant CB as Circuit Breaker
    participant D as Diagnostics Agent
    
    Note over O,D: A2A Error Recovery Pattern
    
    O->>+AC: 📤 Send A2A Message
    AC->>+CB: 🔍 Check Circuit Status
    CB-->>-AC: ✅ Circuit CLOSED - Proceed
    
    AC->>+AS: 🌐 HTTP Request to Primary Agent
    AS->>AS: ❌ Internal Server Error
    AS-->>-AC: 🚨 500 Internal Server Error
    
    AC->>+CB: 📊 Report Failure
    CB->>CB: 📈 Increment Failure Count (3/5)
    CB-->>-AC: ⚠️ Failure Recorded - Continue
    
    rect rgb(255, 245, 245)
        Note over AC,AS: Retry Attempt 1
        AC->>AC: ⏳ Wait (Exponential Backoff: 1s)
        AC->>+AS: 🔄 Retry HTTP Request
        AS-->>-AC: 🚨 504 Gateway Timeout
        
        AC->>+CB: 📊 Report Failure
        CB->>CB: 📈 Increment Failure Count (4/5)
        CB-->>-AC: ⚠️ One failure away from OPEN
    end
    
    rect rgb(255, 245, 245)
        Note over AC,AS: Retry Attempt 2  
        AC->>AC: ⏳ Wait (Exponential Backoff: 2s)
        AC->>+AS: 🔄 Retry HTTP Request
        AS-->>-AC: 🚨 Connection Refused
        
        AC->>+CB: 📊 Report Failure
        CB->>CB: 🚨 Circuit OPEN (5/5 failures)
        CB-->>-AC: ⛔ Circuit OPEN - Service Unavailable
    end
    
    rect rgb(245, 255, 245)
        Note over AC,ASB: Fallback to Backup Service
        AC->>AC: 🔄 Switch to Backup Agent
        Note right of AC: Fallback strategy:<br/>- Use backup diagnostics agent<br/>- Reduced functionality<br/>- Lower confidence threshold
        
        AC->>+ASB: 🌐 HTTP Request to Backup Agent
        ASB->>+D: 📋 Process Request (Backup)
        D->>D: 🧠 Basic Image Analysis
        Note right of D: Fallback processing:<br/>- Simpler model<br/>- Faster inference<br/>- Lower accuracy
        
        D-->>-ASB: 📊 Backup Results
        ASB-->>-AC: ✅ 200 OK - Backup Response
        
        AC->>AC: 🏷️ Mark as Fallback Response
        Note right of AC: Add metadata:<br/>- service_mode: "fallback"<br/>- confidence_adjusted: true<br/>- primary_service_unavailable: true
    end
    
    AC-->>-O: 📬 Fallback Response with Metadata
    Note right of AC: {<br/>  "success": true,<br/>  "result": backup_diagnosis,<br/>  "service_mode": "fallback",<br/>  "confidence": 0.75,<br/>  "limitations": "Reduced accuracy due to backup service"<br/>}
    
    O->>O: 📝 Process Fallback Response
    Note right of O: Handle graceful degradation:<br/>- Inform user of service limitations<br/>- Adjust confidence thresholds<br/>- Provide appropriate disclaimers
    
    Note over O,D: Graceful degradation ensures<br/>service continuity during failures
```

### Error Response Formats

```python
# A2A Error Response Format
class A2AErrorResponse(BaseModel):
    """Standardized A2A error response"""
    
    error: bool = True
    error_code: str  # Standard error codes
    error_message: str  # Human-readable message
    error_details: Dict[str, Any]  # Detailed error information
    
    # A2A Protocol Fields
    message_id: str  # Reference to original message
    conversation_id: str  # Session identifier
    agent_id: str  # Error-producing agent
    
    # Recovery Information
    retry_after: Optional[int] = None  # Seconds before retry
    alternative_agents: List[str] = []  # Fallback options
    fallback_available: bool = False
    
    # Debugging Information
    stack_trace: Optional[str] = None
    request_context: Dict[str, Any] = {}
    performance_metrics: Dict[str, float] = {}
    
    # Timestamps
    error_timestamp: datetime = Field(default_factory=datetime.now)
    request_timestamp: Optional[datetime] = None
    
# Example Error Responses
image_processing_error = A2AErrorResponse(
    error_code="IMAGE_PROCESSING_FAILED",
    error_message="Cannot process RGBA image format",
    error_details={
        "supported_formats": ["RGB", "L", "P"],
        "received_format": "RGBA",
        "conversion_available": True
    },
    retry_after=5,
    fallback_available=True,
    alternative_agents=["backup_diagnostics_agent"]
)

timeout_error = A2AErrorResponse(
    error_code="AGENT_TIMEOUT", 
    error_message="Agent processing exceeded timeout limit",
    error_details={
        "timeout_limit": 60,
        "processing_time": 62.5,
        "operation": "diagnose_plant",
        "partial_results_available": False
    },
    retry_after=30,
    fallback_available=True
)

capability_error = A2AErrorResponse(
    error_code="UNSUPPORTED_OPERATION",
    error_message="Agent does not support requested operation", 
    error_details={
        "requested_operation": "analyze_soil_composition",
        "supported_operations": ["diagnose_plant", "classify_image"],
        "suggested_agent": "soil_analysis_agent"
    },
    alternative_agents=["soil_analysis_agent", "environmental_agent"]
)
```

---

## 📊 Performance and Monitoring

### A2A Performance Metrics

```mermaid
graph TB
    subgraph "Communication Metrics"
        Latency[⏱️ Message Latency<br/>Request-Response Time]
        Throughput[📊 Message Throughput<br/>Messages/Second]
        ErrorRate[🚨 Error Rate<br/>Failed Messages %]
    end
    
    subgraph "Agent Metrics"
        Availability[✅ Agent Availability<br/>Uptime %]
        Capacity[🔋 Processing Capacity<br/>Concurrent Requests]
        Response[⚡ Response Time<br/>Agent Processing Time]
    end
    
    subgraph "System Metrics"
        Discovery[🔍 Discovery Time<br/>Agent Lookup Duration]
        Registration[📋 Registration Health<br/>Registry Update Rate]
        Routing[🎯 Routing Efficiency<br/>Optimal Path Selection]
    end
    
    Latency --> Availability
    Throughput --> Capacity
    ErrorRate --> Response
    Discovery --> Registration
    Registration --> Routing
```

### Monitoring Implementation

```python
class A2APerformanceMonitor:
    """Monitor A2A protocol performance and health"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.dashboard = MonitoringDashboard()
        
    async def monitor_a2a_message(
        self, 
        message: Message, 
        response: A2AResponse,
        execution_time: float
    ) -> None:
        """Monitor individual A2A message performance"""
        
        metrics = {
            "message_id": message.message_id,
            "conversation_id": message.conversation_id,
            "source_agent": message.metadata.get("source_agent"),
            "target_agent": message.metadata.get("target_agent"),
            "operation": message.metadata.get("operation"),
            "execution_time": execution_time,
            "success": response.success,
            "error_code": response.error_code if not response.success else None,
            "payload_size": len(str(message)),
            "response_size": len(str(response)),
            "timestamp": datetime.now()
        }
        
        # Record metrics
        await self.metrics_collector.record_message_metrics(metrics)
        
        # Check for anomalies
        if execution_time > 10.0:  # Slow response
            await self.alert_manager.send_alert(
                "SLOW_A2A_RESPONSE", 
                f"A2A message took {execution_time:.2f}s",
                severity="warning",
                context=metrics
            )
            
        if not response.success:  # Error response
            await self.alert_manager.send_alert(
                "A2A_MESSAGE_FAILED",
                f"A2A message failed: {response.error_message}",
                severity="error", 
                context=metrics
            )
    
    async def monitor_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """Monitor individual agent health via A2A"""
        
        health_metrics = {
            "agent_id": agent_id,
            "timestamp": datetime.now(),
            "available": False,
            "response_time": None,
            "error_rate": 0.0,
            "capacity_usage": 0.0
        }
        
        try:
            # Send health check via A2A
            start_time = time.time()
            health_response = await self.send_health_check(agent_id)
            response_time = time.time() - start_time
            
            health_metrics.update({
                "available": True,
                "response_time": response_time,
                "agent_status": health_response.get("status", "unknown"),
                "version": health_response.get("version"),
                "capabilities": health_response.get("capabilities", []),
                "current_load": health_response.get("current_load", 0),
                "max_capacity": health_response.get("max_capacity", 100)
            })
            
            # Calculate derived metrics
            if health_metrics["max_capacity"] > 0:
                health_metrics["capacity_usage"] = (
                    health_metrics["current_load"] / health_metrics["max_capacity"]
                )
                
        except Exception as e:
            health_metrics["error"] = str(e)
            await self.alert_manager.send_alert(
                "AGENT_HEALTH_CHECK_FAILED",
                f"Health check failed for agent {agent_id}: {str(e)}",
                severity="critical"
            )
        
        await self.metrics_collector.record_agent_health(health_metrics)
        return health_metrics
        
    async def generate_performance_report(
        self, 
        time_range: str = "1h"
    ) -> Dict[str, Any]:
        """Generate A2A performance report"""
        
        report = await self.metrics_collector.query_metrics({
            "time_range": time_range,
            "metrics": [
                "message_count",
                "average_latency", 
                "error_rate",
                "agent_availability",
                "throughput"
            ]
        })
        
        return {
            "report_timestamp": datetime.now(),
            "time_range": time_range,
            "summary": {
                "total_messages": report.get("message_count", 0),
                "average_latency_ms": report.get("average_latency", 0) * 1000,
                "error_rate_percent": report.get("error_rate", 0) * 100,
                "system_availability": report.get("agent_availability", 0) * 100,
                "messages_per_second": report.get("throughput", 0)
            },
            "agent_breakdown": report.get("agent_metrics", {}),
            "top_errors": report.get("error_analysis", []),
            "performance_trends": report.get("trend_analysis", {}),
            "recommendations": self._generate_recommendations(report)
        }
        
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if metrics.get("error_rate", 0) > 0.05:  # >5% error rate
            recommendations.append(
                "High error rate detected. Review agent error logs and consider scaling."
            )
            
        if metrics.get("average_latency", 0) > 5.0:  # >5s average latency
            recommendations.append(
                "High latency detected. Consider optimizing agent processing or scaling infrastructure."
            )
            
        agent_metrics = metrics.get("agent_metrics", {})
        for agent_id, agent_data in agent_metrics.items():
            if agent_data.get("capacity_usage", 0) > 0.8:  # >80% capacity
                recommendations.append(
                    f"Agent {agent_id} is running at high capacity. Consider horizontal scaling."
                )
                
        return recommendations
```

This comprehensive documentation provides detailed insights into the A2A protocol implementation, message flows, agent capabilities, error handling, and monitoring within the Sasya Chikitsa multi-agent system.
