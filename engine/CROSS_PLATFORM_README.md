# 🏗️ Cross-Platform Ollama Multi-Model Build

Build **AMD64** Ollama images on **ARM64** MacBook for **OpenShift** deployment.

## 🎯 What This Creates

A single Docker image containing **two AI models**:

| Model | Type | Purpose | Size |
|-------|------|---------|------|
| **llama3.1:8b** | 📝 Text AI | Conversations, Q&A, text analysis | ~4GB |  
| **llava-llama3:8b** | 👁️ Vision AI | Image analysis, visual understanding | ~4GB |
| **Total** | 🤖 Multi-modal | Complete AI suite | **~8GB** |

## 🚀 Quick Start

```bash
cd /Users/rajranja/Documents/github/cds-9-group-6/sasya-chikitsa

# Build AMD64 image for OpenShift
./engine/build-cross-platform.sh --version v1.0

# Build and push to registry  
./engine/build-cross-platform.sh \
  --version v1.0 \
  --registry quay.io/yourusername \
  --push
```

## 🛠️ How It Works

### **Problem Solved**: Cross-Platform Emulation Crashes
- ❌ **Old approach**: Run `ollama serve` during AMD64 build → segmentation faults
- ✅ **New approach**: Download models natively on ARM64 → copy files during build

### **Build Process**:
1. **Download models** using native ARM64 Ollama (no crashes)
2. **Copy model files** into Docker image (no emulation)
3. **Build AMD64 image** fast and reliably
4. **Deploy to OpenShift** with instant startup

## 📋 Usage Examples

### **Text AI (llama3.1:8b)**
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "prompt": "How do I treat wheat rust disease?",
    "stream": false
  }'
```

### **Vision AI (llava-llama3:8b)**
```bash
# Upload image as base64 and analyze
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llava-llama3:8b", 
    "prompt": "What disease does this plant have?",
    "images": ["<base64-encoded-image>"],
    "stream": false
  }'
```

## 🎛️ Configuration Options

### **Build Script Options**:
```bash
./engine/build-cross-platform.sh [OPTIONS]

Options:
  --version <version>     Version tag (default: v1.0)
  --registry <registry>   Registry to push to (e.g., quay.io/username)
  --push                  Push to registry after build
  --platforms <list>      Platforms (default: linux/amd64)
  --help                  Show help
```

### **Examples**:
```bash
# Local build only
./engine/build-cross-platform.sh --version v1.0

# Build for multiple platforms
./engine/build-cross-platform.sh \
  --platforms linux/amd64,linux/arm64 \
  --version v1.0

# Build and push to team registry
./engine/build-cross-platform.sh \
  --version v1.0 \
  --registry quay.io/myteam \
  --push
```

## 🏢 OpenShift Deployment

### **Deployment YAML**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama-multi-model
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama-multi-model
  template:
    metadata:
      labels:
        app: ollama-multi-model
    spec:
      containers:
      - name: ollama
        image: quay.io/yourusername/ollama-multi-model:linux-amd64-v1.0
        ports:
        - containerPort: 11434
        resources:
          requests:
            memory: "8Gi"   # Both models need more RAM
            cpu: "2"
          limits:
            memory: "12Gi"
            cpu: "4"
        readinessProbe:
          httpGet:
            path: /api/version
            port: 11434
          initialDelaySeconds: 30
        livenessProbe:
          httpGet:
            path: /api/version
            port: 11434
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: ollama-service
spec:
  selector:
    app: ollama-multi-model
  ports:
  - port: 11434
    targetPort: 11434
```

### **Deploy to OpenShift**:
```bash
# Apply the deployment
oc apply -f openshift-deployment.yaml

# Check status
oc get pods -l app=ollama-multi-model

# Test the service
oc port-forward svc/ollama-service 11434:11434
curl http://localhost:11434/api/version
```

## 📊 Performance & Resources

### **Resource Requirements**:
| Resource | Development | Production |
|----------|-------------|------------|
| **RAM** | 8GB minimum | 12GB recommended |
| **CPU** | 2 cores | 4 cores recommended |
| **Storage** | 10GB | 15GB |
| **Network** | Standard | High for vision tasks |

### **Startup Times**:
| Phase | Time | Notes |
|-------|------|-------|
| **Container start** | ~5 seconds | Pre-loaded models |
| **Model loading** | ~10 seconds | Both models ready |
| **API ready** | ~15 seconds | Ready for requests |

### **Image Sizes**:
- **Base ollama image**: ~1GB
- **llama3.1:8b model**: ~4GB  
- **llava-llama3:8b model**: ~4GB
- **Final image**: **~9GB total**

## 🔧 Troubleshooting

### **Common Issues**:

#### **Model files not found**:
```bash
# Solution: Download models first
./engine/download-models.sh
```

#### **Out of memory during build**:
```bash
# Solution: Clean up Docker/Podman
podman system prune -a
```

#### **Registry push failed**:
```bash
# Solution: Login to registry
podman login quay.io
```

#### **OpenShift deployment fails**:
```bash
# Check resource limits
oc describe pod <pod-name>

# Increase memory if needed
# Edit deployment.yaml → memory: "12Gi"
```

### **Validation Commands**:
```bash
# Check if models are in image
podman run -it --rm <image-name> ls -la /root/.ollama/models/

# Test both models
podman run -d -p 11434:11434 <image-name>
sleep 15
curl http://localhost:11434/api/tags  # Should show both models
```

## 📁 File Structure

```
engine/
├── Dockerfile.ollamamodel      # Multi-model cross-platform Dockerfile
├── build-cross-platform.sh     # Main build script
├── download-models.sh          # Native model download script
├── model_files/               # Downloaded model files (temporary)
└── CROSS_PLATFORM_README.md   # This documentation
```

## 🎯 Benefits

✅ **Cross-platform**: Build AMD64 on ARM64 Mac  
✅ **Multi-modal**: Text + Vision AI in one container  
✅ **Fast startup**: Models pre-loaded (~15 seconds vs 15 minutes)  
✅ **OpenShift ready**: Health checks, proper resource handling  
✅ **No emulation crashes**: File-based approach avoids segfaults  
✅ **Production optimized**: Proper signal handling, cleanup  

---

**For questions or issues**: Check the troubleshooting section or create an issue in the repository.
