# MLflow Integration for Plant Disease Classification System

This document describes the comprehensive MLflow integration implemented for tracking and monitoring the dual CNN+LLaVA classification system.

## 📊 **Overview**

The MLflow integration provides detailed tracking of classification metrics, model performance, and system behavior for research, monitoring, and optimization purposes.

### **Key Features**

- **Automatic Metrics Tracking**: Confidence scores, prediction margins, entropy, and similarity measures
- **Session-based Organization**: All metrics associated with session IDs for traceability
- **Dual Model Comparison**: Side-by-side comparison of CNN and LLaVA performance
- **Graceful Degradation**: System continues to work even when MLflow server is unavailable
- **Rich Metrics**: 20+ different metrics covering uncertainty, agreement, and decision quality

## 🏗️ **Architecture**

```
Classification Request
         ↓
┌─────────────────────┐
│  Classification     │
│  Tool               │
└─────────────────────┘
         ↓
┌─────────────────────┐      ┌──────────────────┐
│  MLflow Manager     │ ←→   │  MLflow Server   │
│  - Start Run        │      │  - Experiments   │
│  - Log Metrics      │      │  - Runs          │
│  - End Run          │      │  - UI Dashboard  │
└─────────────────────┘      └──────────────────┘
         ↓
┌─────────────────────┐
│  Classification     │
│  Metrics Calculator │
│  - Entropy          │
│  - Prediction Margin│
│  - Uncertainty      │
└─────────────────────┘
```

## ⚙️ **Configuration**

### **Environment Variables** (`.env`)

```bash
# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=plant_disease_classification  
MLFLOW_ARTIFACT_LOCATION=./mlflow_artifacts
MLFLOW_REGISTRY_URI=http://localhost:5000
```

### **Auto-Configuration**

The system automatically:
- Creates experiments if they don't exist
- Handles server unavailability gracefully
- Logs warnings when MLflow is disabled
- Falls back to normal operation without metrics

## 📋 **Tracked Metrics**

### **Core Classification Metrics**

| Metric | Description | Type |
|--------|-------------|------|
| `final_confidence` | Final classification confidence | Metric |
| `final_disease_name` | Final disease classification | Parameter |
| `result_source` | Source of final result (cnn/sme) | Parameter |

### **CNN Metrics**

| Metric | Description | Type |
|--------|-------------|------|
| `cnn_confidence` | CNN model confidence | Metric |
| `cnn_disease_name` | CNN disease prediction | Parameter |
| `cnn_entropy` | Information entropy of CNN prediction | Metric |
| `cnn_uncertainty` | CNN uncertainty (1 - confidence) | Metric |
| `cnn_uncertainty_level` | Categorical uncertainty (low/medium/high) | Parameter |

### **LLaVA Metrics**

| Metric | Description | Type |
|--------|-------------|------|
| `llava_confidence` | LLaVA model confidence | Metric |
| `llava_disease_name` | LLaVA disease prediction | Parameter |
| `llava_severity` | Disease severity assessment | Parameter |

### **Comparison Metrics**

| Metric | Description | Type |
|--------|-------------|------|
| `prediction_margin` | Absolute confidence difference | Metric |
| `confidence_ratio` | CNN/LLaVA confidence ratio | Metric |
| `disease_name_similarity` | Disease name similarity score | Metric |
| `agreement_strength` | Model agreement measure | Metric |
| `disagreement_level` | Categorical disagreement (low/medium/high) | Parameter |

### **Decision Logic Metrics**

| Metric | Description | Type |
|--------|-------------|------|
| `cnn_unknown_trigger` | Whether CNN returned unknown | Metric |
| `similarity_binary` | High similarity flag (≥0.6) | Metric |
| `system_coverage` | System availability score | Metric |
| `reliability_score` | Overall reliability measure | Metric |

### **System Availability**

| Metric | Description | Type |
|--------|-------------|------|
| `llava_available` | LLaVA system availability | Metric |
| `cnn_available` | CNN system availability | Metric |
| `both_available` | Both systems available | Metric |

## 🚀 **Usage**

### **Starting MLflow Server**

```bash
# Start MLflow server
python start_mlflow_server.py

# Custom configuration
python start_mlflow_server.py --port 5001 --host localhost
```

### **Running Classification with MLflow**

The system automatically tracks metrics when:
1. MLflow server is running
2. Classification tool is used
3. Session ID is provided

```python
# Classification automatically logs metrics
result = classification_tool.run(
    image_b64="...",
    session_id="user_session_123",
    plant_type="tomato"
)
```

### **Viewing Results**

1. **MLflow UI**: `http://localhost:5000`
2. **Experiment**: `plant_disease_classification`
3. **Runs**: Organized by session ID

## 🧪 **Testing**

### **Integration Test**

```bash
# Test MLflow integration
python test_mlflow_integration.py
```

### **Test Coverage**

- ✅ MLflow manager initialization
- ✅ Classification metrics calculation  
- ✅ Graceful degradation when server unavailable
- ✅ Classification tool integration
- ✅ Error handling and logging

## 📊 **Dashboard & Analysis**

### **Key MLflow UI Views**

1. **Experiment Overview**:
   - Run comparison table
   - Metric trends over time
   - Parameter distribution

2. **Individual Runs**:
   - Complete metric set
   - Plant context parameters
   - Error logs and tags

3. **Metric Comparisons**:
   - CNN vs LLaVA performance
   - Confidence distributions
   - Agreement patterns

### **Analysis Queries**

```python
# Find high-disagreement cases
high_disagreement = runs.filter(runs.disagreement_level == "high")

# Compare model performance
cnn_accuracy = runs.groupby("cnn_disease_name").mean("final_confidence")
llava_accuracy = runs.groupby("llava_disease_name").mean("final_confidence")

# System reliability analysis
reliability_by_coverage = runs.groupby("system_coverage").mean("reliability_score")
```

## 🔧 **Implementation Details**

### **File Structure**

```
engine/
├── .env                           # MLflow configuration
├── core/
│   ├── mlflow_manager.py         # MLflow integration manager
│   └── classification_metrics.py # Metrics calculation utilities
├── fsm_agent/
│   ├── server/fsm_server.py      # MLflow initialization on startup
│   └── tools/classification_tool.py # MLflow tracking integration
├── start_mlflow_server.py        # MLflow server startup script
└── test_mlflow_integration.py    # Integration tests
```

### **Key Classes**

- **`MLflowManager`**: Main MLflow integration class
- **`ClassificationMetrics`**: Utility functions for metric calculations
- **`ClassificationTool`**: Enhanced with MLflow tracking

## 🐛 **Troubleshooting**

### **MLflow Server Issues**

```bash
# Check server status
curl http://localhost:5000/health

# View server logs
python start_mlflow_server.py

# Test connectivity
python test_mlflow_integration.py
```

### **Common Issues**

1. **Server Not Running**: System logs warnings but continues operation
2. **Port Conflicts**: Change port in `.env` file
3. **Permission Issues**: Check artifacts directory permissions
4. **Import Errors**: Verify MLflow installation: `pip install mlflow`

### **Log Messages**

```
✅ MLflow tracking initialized successfully    # All good
⚠️ MLflow tracking initialization failed      # Server unavailable (expected)
❌ Failed to log metrics to MLflow            # Unexpected error
```

## 📈 **Performance Impact**

- **Overhead**: Minimal (~10-50ms per classification)
- **Network**: Only when MLflow server available
- **Storage**: Metrics stored in SQLite database
- **Memory**: Negligible additional memory usage

## 🔮 **Future Enhancements**

### **Planned Features**

- **Model Registry Integration**: Track model versions and performance
- **Automated Alerts**: Notifications for performance degradation
- **Advanced Analytics**: Statistical analysis and reporting
- **Batch Tracking**: Support for batch classification operations
- **Custom Dashboards**: Specialized views for different user roles

### **Research Applications**

- **Model Comparison**: Systematic CNN vs LLaVA evaluation
- **Uncertainty Analysis**: Understanding model confidence patterns
- **Error Analysis**: Identifying failure modes and patterns
- **Performance Optimization**: Data-driven system improvements

## 🎯 **Best Practices**

### **Development**

1. **Always provide session IDs** for traceability
2. **Start MLflow server** before running classifications for full metrics
3. **Monitor logs** for MLflow-related warnings
4. **Use test script** to validate integration

### **Production**

1. **Configure persistent storage** for MLflow artifacts
2. **Set up monitoring** for MLflow server availability
3. **Regular cleanup** of old experiments and runs
4. **Backup MLflow database** for data protection

### **Analysis**

1. **Use experiment tags** to organize different test scenarios
2. **Filter runs** by time periods for trend analysis
3. **Compare metrics** across different plant types/conditions
4. **Export data** for external analysis tools

---

## 📚 **Resources**

- **MLflow Documentation**: https://mlflow.org/docs/
- **Classification System**: [DUAL_CLASSIFICATION_README.md](DUAL_CLASSIFICATION_README.md)
- **Setup Guide**: [ENV_CONFIGURATION.md](agents/ENV_CONFIGURATION.md)

The MLflow integration provides comprehensive observability into the plant disease classification system, enabling data-driven improvements and research insights while maintaining system reliability and performance.

