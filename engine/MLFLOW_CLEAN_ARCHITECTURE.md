# MLflow Clean Architecture Implementation

## 🎯 **Overview**

We have successfully refactored the MLflow integration to follow a clean dependency injection pattern. MLflow is now initialized **once** at the workflow level and passed cleanly down through the dependency chain without repeated initialization.

## 🏗️ **Clean Architecture Flow**

```
DynamicPlanningWorkflow (Initialize MLflow Once)
    ↓
NodeFactory (Receive & Pass MLflow Manager)
    ↓
BaseNode (Receive MLflow Manager)
    ↓
Tools (Receive MLflow Manager as Parameter)
```

## 📋 **Implementation Details**

### **1. Workflow Level - Single Initialization**
**File:** `engine/fsm_agent/core/langgraph_workflow.py`

```python
def __init__(self, llm_config: Dict[str, Any]):
    # Initialize LLM
    self.llm = ChatOllama(**llm_config)
    
    # Initialize MLflow manager once for the entire workflow
    self.mlflow_manager = None
    try:
        from engine.core.mlflow_manager import initialize_mlflow, get_mlflow_manager
        mlflow_initialized = initialize_mlflow()
        if mlflow_initialized:
            self.mlflow_manager = get_mlflow_manager()
            logger.info("✅ MLflow tracking initialized in workflow")
        else:
            logger.warning("⚠️ MLflow tracking initialization failed - metrics will not be logged")
    except ImportError:
        logger.warning("MLflow components not available - metrics will not be logged")
    except Exception as e:
        logger.warning(f"MLflow initialization error: {e}")
    
    # Pass MLflow manager to NodeFactory
    self.node_factory = NodeFactory(self.tools, self.llm, self.mlflow_manager)
```

### **2. Node Factory - Clean Dependency Injection**
**File:** `engine/fsm_agent/core/nodes/node_factory.py`

```python
def __init__(self, tools: Dict[str, Any], llm: Any, mlflow_manager=None):
    self.tools = tools
    self.llm = llm
    self.mlflow_manager = mlflow_manager
    self.nodes = {}
    self._create_nodes()

def _create_nodes(self) -> None:
    for node_name, node_class in node_classes.items():
        try:
            # Pass MLflow manager to each node
            self.nodes[node_name] = node_class(self.tools, self.llm, self.mlflow_manager)
            logger.debug(f"Created node: {node_name}")
        except Exception as e:
            logger.error(f"Failed to create node {node_name}: {str(e)}")
            raise
```

### **3. Base Node - Receive and Store MLflow Manager**
**File:** `engine/fsm_agent/core/nodes/base_node.py`

```python
def __init__(self, tools: Dict[str, Any], llm: Any, mlflow_manager=None):
    self.tools = tools
    self.llm = llm
    self.mlflow_manager = mlflow_manager  # Store for use by tools
    self.logger = logger
```

### **4. Classification Tool - Accept MLflow Manager**
**File:** `engine/fsm_agent/tools/classification_tool.py`

```python
def _run(self, mlflow_manager=None, **kwargs) -> Dict[str, Any]:
    session_id = kwargs.get("session_id", "unknown")
    
    try:
        # Start MLflow run if manager is available
        if mlflow_manager and mlflow_manager.is_available():
            try:
                run_id = mlflow_manager.start_run(session_id, f"classification_{session_id}")
                logger.debug(f"Started MLflow tracking for session: {session_id}")
            except Exception as e:
                logger.warning(f"Failed to start MLflow run: {e}")
                mlflow_manager = None
        
        # ... rest of classification logic with clean MLflow usage
```

### **5. Node Usage - Pass MLflow Manager to Tools**
**Files:** `classifying_node.py`, `followup_node.py`

```python
# In classifying node
result = await classification_tool._arun(mlflow_manager=self.mlflow_manager, **classification_input)

# In followup node  
classification_result = await classification_tool._arun(mlflow_manager=self.mlflow_manager, **classification_input)
```

## ✅ **Benefits of Clean Architecture**

### **1. Single Initialization**
- MLflow is initialized **once** at the workflow level
- No repeated initialization in tools or nodes
- Cleaner startup and better performance

### **2. Clean Dependency Injection**
- Clear dependency flow: Workflow → NodeFactory → BaseNode → Tools
- No hidden dependencies or imports scattered throughout codebase
- Easy to test and mock MLflow for unit tests

### **3. Graceful Degradation**
- If MLflow is not available, the entire system continues to work
- No cascading failures
- Clean error handling at each level

### **4. Maintainable Code**
- MLflow logic is contained in dedicated files (`mlflow_manager.py`, `classification_metrics.py`)
- Easy to add MLflow support to new tools
- Clear separation of concerns

### **5. Testability**
- Can easily pass mock MLflow manager for testing
- No hidden global state
- Each component has clear inputs and outputs

## 🔧 **Usage Flow**

1. **Startup**: `DynamicPlanningWorkflow` initializes MLflow once
2. **Dependency Injection**: MLflow manager flows through NodeFactory → BaseNode
3. **Tool Execution**: Nodes pass MLflow manager to tools when calling them
4. **Metrics Logging**: Tools use the provided MLflow manager to log metrics
5. **Clean Shutdown**: MLflow runs are properly ended by the tools

## 🚀 **Testing the Architecture**

To test the clean architecture:

1. **Start MLflow Server**: 
   ```bash
   cd engine && python start_mlflow_server.py
   ```

2. **Run Agent**: 
   ```bash
   python fsm_agent/server/fsm_server.py
   ```

3. **Verify**: Check MLflow UI at `http://localhost:5000` for tracked experiments and metrics

## 📝 **Notes**

- **No Breaking Changes**: All existing functionality is preserved
- **Backward Compatible**: Code gracefully handles MLflow unavailability  
- **Performance**: Single initialization reduces overhead
- **Scalable**: Easy to add MLflow support to additional tools

The architecture is now clean, maintainable, and follows proper dependency injection patterns! 🎉
