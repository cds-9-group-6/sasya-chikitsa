# Hardcoding Fixes in FSM Agent 🔧

## 🎯 **Overview**

We successfully identified and fixed all hardcoded values across the `fsm_agent` directory, replacing them with configurable environment variables. This improves flexibility, testability, and deployment across different environments.

## ✅ **Fixed Hardcoded Values**

### **1. Ollama Server URLs**
**Files Fixed:**
- `test_fsm_agent.py` (3 instances)
- `test_refactored_workflow.py` (1 instance)
- `test_server_startup.py` (1 instance)
- `classification_tool.py` (1 instance) ✅ Already fixed

**Before:**
```python
"base_url": "http://localhost:11434"
response = requests.get("http://localhost:11434/api/tags", timeout=5)
```

**After:**
```python
"base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
response = requests.get(f"{ollama_host}/api/tags", timeout=health_timeout)
```

### **2. Session Storage Directory**
**File Fixed:** `core/session_manager.py`

**Before:**
```python
def __init__(self, storage_dir: str = "/tmp/fsm_sessions"):
```

**After:**
```python
def __init__(self, storage_dir: str = None):
    if storage_dir is None:
        storage_dir = os.getenv("SESSION_STORAGE_DIR", "/tmp/fsm_sessions")
    self.storage_dir = storage_dir
```

### **3. Request Timeouts**
**Files Fixed:**
- `classification_tool.py` - LLaVA requests
- `run_fsm_server.py` - Health checks
- `test_fsm_agent.py` - Ollama API checks

**Before:**
```python
timeout=120  # LLaVA requests
timeout=5    # Health checks
```

**After:**
```python
llava_timeout = int(os.getenv("LLAVA_TIMEOUT", "120"))
health_timeout = int(os.getenv("HEALTH_CHECK_TIMEOUT", "5"))
```

## 🔧 **New Environment Variables**

### **Core Configuration**
| Variable | Default | Purpose | Example |
|----------|---------|---------|---------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL | `http://192.168.1.100:11434` |
| `SESSION_STORAGE_DIR` | `/tmp/fsm_sessions` | Session storage directory | `/var/lib/fsm-agent/sessions` |

### **Timeout Configuration**
| Variable | Default | Purpose | Example |
|----------|---------|---------|---------|
| `LLAVA_TIMEOUT` | `120` | LLaVA inference timeout (seconds) | `180` |
| `HEALTH_CHECK_TIMEOUT` | `5` | Health check timeout (seconds) | `10` |

## 🚀 **Usage Examples**

### **Development Environment**
```bash
export OLLAMA_HOST=http://localhost:11434
export SESSION_STORAGE_DIR=./sessions
export LLAVA_TIMEOUT=120
export HEALTH_CHECK_TIMEOUT=5
```

### **Production Environment**
```bash
export OLLAMA_HOST=http://ollama-server:11434
export SESSION_STORAGE_DIR=/var/lib/fsm-agent/sessions
export LLAVA_TIMEOUT=180
export HEALTH_CHECK_TIMEOUT=10
```

### **Docker Environment**
```bash
docker run \
  -e OLLAMA_HOST=http://ollama:11434 \
  -e SESSION_STORAGE_DIR=/app/sessions \
  -e LLAVA_TIMEOUT=240 \
  -e HEALTH_CHECK_TIMEOUT=15 \
  fsm-agent:latest
```

### **Testing Environment**
```bash
export OLLAMA_HOST=http://test-ollama:11434
export SESSION_STORAGE_DIR=/tmp/test-sessions
export LLAVA_TIMEOUT=60  # Faster for tests
export HEALTH_CHECK_TIMEOUT=3  # Faster for tests
```

## 📋 **Benefits Achieved**

### **✅ Flexibility**
- Easy to configure for different environments
- No need to modify code for deployment
- Supports local, staging, production configurations

### **✅ Testing**
- Tests can use different configurations
- Easy to mock external services
- Configurable timeouts for different test scenarios

### **✅ Container-Ready**
- Works seamlessly in Docker/Kubernetes
- Environment-specific configuration via env vars
- No hardcoded assumptions about infrastructure

### **✅ Maintainability**
- Single source of configuration truth
- Clear documentation of configurable values
- Easier to troubleshoot deployment issues

## 🔍 **Files Modified**

| File | Changes | Purpose |
|------|---------|---------|
| `test_fsm_agent.py` | 3x Ollama URL, timeout | Test configuration |
| `test_refactored_workflow.py` | 1x Ollama URL | Test configuration |
| `test_server_startup.py` | 1x Ollama URL | Test configuration |
| `classification_tool.py` | Timeout config | LLaVA request timeout |
| `core/session_manager.py` | Storage directory | Session persistence |
| `run_fsm_server.py` | Health check timeout | Startup validation |

## 💡 **Best Practices Applied**

1. **Safe Defaults**: All environment variables have sensible defaults
2. **Type Safety**: Numeric env vars are properly converted with `int()`
3. **Backward Compatibility**: Existing deployments continue to work
4. **Clear Naming**: Environment variable names are descriptive
5. **Documentation**: Each variable is documented with purpose and examples

## 🎉 **Result**

The FSM Agent is now fully configurable via environment variables, making it:
- **Production-ready** for any environment
- **Test-friendly** with configurable parameters
- **Container-native** with proper env var support
- **Maintainable** with clear configuration patterns

All hardcoded values have been eliminated! 🚀
