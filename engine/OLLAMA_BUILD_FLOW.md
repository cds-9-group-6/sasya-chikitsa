# 🔄 Ollama Build System Flow

## 📋 Build Decision Tree

```
Start: ./engine/build-ollama-models.sh
│
├── Which platform?
│   ├── --platform arm64    → Apple Silicon builds
│   ├── --platform amd64    → Intel/AMD builds  
│   └── --platform both     → Universal builds
│
├── Which models?
│   ├── --models llama31    → Text AI only (1 model)
│   ├── --models llava      → Vision AI only (1 model)
│   ├── --models both       → Both models (2 models)
│   └── --models all        → All combinations (3 configs)
│
└── Registry options?
    ├── Default             → Ask before pushing
    ├── --push              → Auto-push to registry
    └── Skip prompts        → Keep local only
```

## 🏗️ Build Architecture

```
Input: Your Requirements
        ↓
┌─────────────────────────┐
│   Platform Detection   │ ← Docker/Podman auto-detect
│   (ARM64 vs AMD64)     │
└─────────┬───────────────┘
          ↓
┌─────────────────────────┐
│   Model Selection      │ ← llama31, llava, both, all
│   (Text vs Vision)     │
└─────────┬───────────────┘
          ↓
┌─────────────────────────┐
│   Dockerfile Build     │ ← Parameterized build
│   (Multi-stage)        │
└─────────┬───────────────┘
          ↓
┌─────────────────────────┐
│   Model Download       │ ← Ollama pulls from internet
│   (Inside container)   │
└─────────┬───────────────┘
          ↓
┌─────────────────────────┐
│   Custom Model Config  │ ← Agricultural AI prompts
│   (Modelfiles)         │
└─────────┬───────────────┘
          ↓
┌─────────────────────────┐
│   Registry Push        │ ← Optional, interactive
│   (quay.io/yourorg)    │
└─────────┬───────────────┘
          ↓
Output: Ready-to-use Docker images
```

## 🎯 Image Output Matrix

```
                    │ llama31-only │ llava-only │ both-models │
────────────────────┼──────────────┼────────────┼─────────────┤
ARM64 (Apple M1/M2) │      ✅      │     ✅     │      ✅     │
AMD64 (Intel/AMD)   │      ✅      │     ✅     │      ✅     │
────────────────────┴──────────────┴────────────┴─────────────┘
Total: 6 different images
```

## 🚀 Usage Flow

```
1. Setup (once)
   ./engine/setup-ollama-build.sh
        ↓
2. Choose build strategy
   ├── Quick test     → --dry-run --version test
   ├── Development    → --platform arm64 --models llama31
   ├── Production     → --platform both --models all
   └── Vision-only    → --platform both --models llava
        ↓
3. Build execution
   ├── Platform-specific base image pull
   ├── Model download and configuration
   ├── Custom Modelfile application
   └── Image tagging and registry push (optional)
        ↓
4. Deployment
   ├── Local testing  → podman run -p 11434:11434 <image>
   ├── Production     → Registry pull + deploy
   └── Team sharing   → Registry push + team pull
```

## 🔧 Build Process Detail

```
build-ollama-models.sh execution:

1. Environment Check
   ├── Detect Docker/Podman
   ├── Validate script permissions
   └── Check available disk space

2. Platform Loop
   ├── For each platform (arm64, amd64)
   │   └── Pull platform-specific base image
   
3. Model Loop  
   ├── For each model combination
   │   ├── Parse model string
   │   ├── Set build arguments
   │   └── Execute docker build
   
4. Build Process (per image)
   ├── Copy Modelfiles into container
   ├── Start Ollama server
   ├── Pull required models (llama31, llava)
   ├── Create custom models with Modelfiles
   └── Setup health checks
   
5. Post-Build
   ├── Display image info
   ├── Prompt for registry push
   └── Tag and push (if requested)
```

## 📊 Resource Requirements

```
Per Build:
├── Time: 10-30 minutes (depending on internet speed)
├── Network: 4-8GB download per model
├── Storage: 5-10GB per final image
└── Memory: 2-4GB during build

For All 6 Images:
├── Total time: 1-3 hours
├── Total download: 20-40GB
├── Total storage: 30-60GB
└── Peak memory: 4-8GB
```

## 🎛️ Configuration Points

```
Customizable Elements:
├── Model Selection
│   ├── Base models (llama-3.1:8b, llava-llama3:8b)
│   └── Custom models (via Modelfiles)
│
├── System Prompts
│   ├── Agricultural focus (Modelfile.llama3.1)
│   └── Vision analysis (Modelfile.llava)
│
├── Model Parameters
│   ├── Temperature, context length
│   ├── Memory management
│   └── Performance tuning
│
└── Container Settings
    ├── Health checks
    ├── Port exposure
    └── Environment variables
```

---

This visual guide helps understand the complete build system architecture and decision points.
