# MLflow Persistent Run Refactor 🚀

## 🎯 **Overview**

We successfully refactored the MLflow integration from creating individual runs per session to using a **single persistent run for the entire agent lifetime**. This dramatically improves the MLflow UI experience and provides better operational metrics tracking.

## 🔄 **What Changed**

### **Before: Session-Based Runs (❌ Problematic)**
- ❌ New MLflow run created for every user session
- ❌ Hundreds/thousands of runs cluttering the MLflow UI  
- ❌ Run management overhead (start/end) for each classification
- ❌ Difficult to get aggregate metrics across sessions
- ❌ Poor scalability with high user activity

### **After: Persistent Run (✅ Optimal)**
- ✅ **Single persistent run** for the entire agent lifetime
- ✅ **Clean MLflow UI** with manageable number of runs
- ✅ **Session context** tracked via tags and timestamps
- ✅ **Time-series metrics** showing agent performance over time
- ✅ **Aggregate analytics** across all sessions in one view
- ✅ **Better scalability** and performance

## 🏗️ **Architecture Changes**

### **1. MLflow Manager Refactoring**

**File:** `engine/core/mlflow_manager.py`

#### **New Persistent Run Model**
```python
class MLflowManager:
    def __init__(self):
        self.persistent_run_id: Optional[str] = None  # NEW: Track persistent run
        
    def _start_persistent_run(self) -> Optional[str]:
        """Start a single persistent run for agent lifetime"""
        run_name = f"agent_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        run = mlflow.start_run(run_name=run_name)
        
        # Tag as persistent agent run
        mlflow.set_tag("run_type", "agent_persistent")
        mlflow.set_tag("agent_start_time", datetime.now().isoformat())
        
        self.persistent_run_id = run.info.run_id
```

#### **Session Context via Tags & Steps**
```python
def log_classification_metrics(self, session_id: str, ...):
    step = int(time.time())  # Use timestamp as step
    
    # Log session-specific tags
    mlflow.set_tag(f"session_{session_id}_processed", "true")
    mlflow.set_tag(f"session_{session_id}_disease", final_result.get("disease_name"))
    
    # Log time-series metrics
    mlflow.log_metric("final_confidence", confidence, step=step)
    mlflow.log_metric("classification_count", 1.0, step=step)
```

### **2. Classification Tool Simplification**

**File:** `engine/fsm_agent/tools/classification_tool.py`

#### **Before: Complex Run Management**
```python
# OLD: Tool managed its own runs
mlflow_manager.start_run(session_id, f"classification_{session_id}")
# ... do classification ...
mlflow_manager.end_run()
```

#### **After: Simple Metrics Logging**  
```python
# NEW: Tool just logs metrics to persistent run
if mlflow_manager and mlflow_manager.is_available():
    mlflow_manager.log_classification_metrics(
        session_id=session_id,
        cnn_result=cnn_result,
        llava_result=llava_result,
        final_result=final_result,
        similarity_score=similarity
    )
```

### **3. Agent Lifecycle Integration**

**File:** `engine/fsm_agent/server/fsm_server.py`

#### **Startup: Initialize Persistent Run**
```python
# MLflow persistent run started automatically in workflow initialization
agent = DynamicPlanningAgent(llm_config)  # MLflow run starts here
```

#### **Shutdown: Clean Cleanup**
```python
# Cleanup on shutdown
if agent.workflow.mlflow_manager:
    agent.workflow.mlflow_manager.end_persistent_run()
    logger.info("MLflow persistent run ended")
```

## 📊 **MLflow UI Benefits**

### **Session Tracking**
Each session is tracked via:
- **Tags**: `session_<id>_processed`, `session_<id>_disease`, etc.
- **Time-series**: All metrics have timestamp-based steps
- **Searchable**: Filter by session tags in MLflow UI

### **Time-Series Analytics**
- **Classification Rate**: See classifications over time
- **Confidence Trends**: Track model confidence patterns  
- **Error Rates**: Monitor system reliability
- **Model Comparison**: CNN vs LLaVA performance over time

### **Aggregate Insights**
- **Total Classifications**: Count across all sessions
- **Average Confidence**: Overall model performance
- **Disease Distribution**: Most common classifications
- **System Uptime**: Agent operational metrics

## 🔧 **Key Changes by File**

| File | Key Changes |
|------|-------------|
| `mlflow_manager.py` | Added persistent run management, session context tagging |
| `classification_tool.py` | Removed run management, simplified to metrics logging only |
| `langgraph_workflow.py` | Initialize MLflow manager with persistent run on startup |
| `fsm_server.py` | Added MLflow cleanup on agent shutdown |

## 📈 **Usage & Query Examples**

### **Find Specific Session Metrics**
```python
# In MLflow UI, filter by tags
tags.session_<session_id>_processed = "true"
```

### **Time-Series Queries**
```python  
# Get classification rate over time
SELECT step, classification_count FROM metrics WHERE key = 'classification_count'

# Monitor confidence trends
SELECT step, final_confidence FROM metrics WHERE key = 'final_confidence'
```

### **Session Analysis**
```python
# Find all sessions processed
SELECT tag_value FROM tags WHERE tag_key LIKE 'session_%_processed'

# Get disease distribution
SELECT tag_value, COUNT(*) FROM tags WHERE tag_key LIKE 'session_%_disease'
```

## ✅ **Benefits Achieved**

### **🎯 User Experience**
- **Clean MLflow UI**: No run clutter, easy navigation
- **Better Analytics**: Time-series and aggregate views
- **Faster Queries**: Single run vs hundreds of runs

### **⚡ Performance**  
- **Reduced Overhead**: No run creation/teardown per session
- **Better Scalability**: Handles high session volumes efficiently
- **Lower Memory**: Single run state vs many run objects

### **🔍 Operational Insights**
- **Agent Health**: Monitor overall system performance
- **Usage Patterns**: See peak usage times and trends
- **Model Performance**: Track CNN vs LLaVA effectiveness over time
- **Error Analysis**: Identify systematic issues across sessions

## 🧪 **Testing**

To test the new architecture:

1. **Start MLflow Server**: `cd engine && python start_mlflow_server.py`
2. **Start Agent**: `python fsm_agent/server/fsm_server.py`  
3. **Make Classifications**: Submit multiple images from different sessions
4. **Check MLflow UI**: Go to `http://localhost:5000`
   - Should see **single persistent run** with timestamps
   - Session tags should be visible: `session_<id>_processed`
   - Metrics should show time-series data

## 📝 **Migration Notes**

### **Backward Compatibility**
- ✅ All existing metrics are preserved
- ✅ Classification functionality unchanged  
- ✅ Session tracking still works (via tags instead of runs)
- ✅ Graceful degradation if MLflow unavailable

### **Breaking Changes**  
- ❌ Old per-session runs no longer created
- ❌ `start_run(session_id)` method deprecated (but kept for compatibility)
- ❌ MLflow UI will show fewer runs (by design)

## 🎉 **Result**

The MLflow integration is now **production-ready** with:
- **📊 Better Analytics**: Time-series insights across all sessions  
- **🎯 Cleaner UI**: Manageable number of runs in MLflow
- **⚡ Better Performance**: Reduced MLflow overhead
- **🔍 Session Context**: Full traceability via tags and timestamps
- **📈 Scalability**: Handles thousands of sessions efficiently

**Perfect for operational metrics tracking! 🚀**
