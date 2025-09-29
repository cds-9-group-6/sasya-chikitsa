# 🤖 Sasya Chikitsa Ollama Multi-Model Docker Build System

Complete guide for building platform-specific Ollama containers with pre-configured AI models for agricultural applications.

## 📊 Overview

This system creates **6 different Docker images** combining:
- **2 platforms**: ARM64 (Apple Silicon) and AMD64 (Intel/AMD)
- **3 model configurations**: llama-3.1:8b only, llava-llama3:8b only, or both models

### 🎯 Build Matrix

| # | Platform | Models | Image Tag | Use Case |
|---|----------|--------|-----------|----------|
| 1 | ARM64 | llama-3.1:8b | `ollama-llama31-only:arm64-{version}` | Text-only AI on Apple Silicon |
| 2 | AMD64 | llama-3.1:8b | `ollama-llama31-only:amd64-{version}` | Text-only AI on Intel/AMD |
| 3 | ARM64 | llava-llama3:8b | `ollama-llava-only:arm64-{version}` | Vision AI on Apple Silicon |
| 4 | AMD64 | llava-llama3:8b | `ollama-llava-only:amd64-{version}` | Vision AI on Intel/AMD |
| 5 | ARM64 | Both models | `ollama-both-models:arm64-{version}` | Full AI suite on Apple Silicon |
| 6 | AMD64 | Both models | `ollama-both-models:amd64-{version}` | Full AI suite on Intel/AMD |

## 🏗️ Architecture

```
sasya-chikitsa/engine/
├── Dockerfile.ollama-models        # Main multi-model Dockerfile
├── Modelfile.llama3.1             # Configuration for text AI
├── Modelfile.llava                 # Configuration for vision AI
├── build-ollama-models.sh          # Build script (this is your main tool)
├── container-runtime-utils.sh     # Docker/Podman compatibility layer
├── setup-ollama-build.sh          # One-time setup script
└── README_OLLAMA_BUILDS.md         # This documentation
```

## 🚀 Quick Start (TL;DR)

```bash
# 1. One-time setup
./engine/setup-ollama-build.sh

# 2. Build everything (6 images)
./engine/build-ollama-models.sh --version v1.0

# 3. Test a single image
podman run -it --rm -p 11434:11434 ollama-llama31-only:arm64-v1.0
```

## 📋 Prerequisites

### System Requirements
- **Container Runtime**: Docker Desktop OR Podman
- **Platform**: macOS (ARM64/Intel), Linux, or Windows with WSL2
- **Memory**: 8GB+ RAM recommended (models are ~4-5GB each)
- **Storage**: 20GB+ free space for all images
- **Network**: Internet connection for model downloads

### Software Installation

#### 🍎 macOS Users
```bash
# Option 1: Podman (Recommended - rootless, secure)
brew install podman

# Option 2: Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop/
```

#### 🐧 Linux Users
```bash
# Podman
sudo apt update && sudo apt install podman

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

#### 🪟 Windows Users
- Install Docker Desktop with WSL2 backend
- Or use Podman Desktop

### Verification
```bash
# Check container runtime
podman --version  # or docker --version

# Test basic functionality
podman run hello-world  # or docker run hello-world
```

## 🛠️ Setup Instructions

### Step 1: Clone and Navigate
```bash
git clone <repository-url>
cd sasya-chikitsa
```

### Step 2: One-Time Setup
```bash
# This makes scripts executable and validates environment
./engine/setup-ollama-build.sh
```

**Expected Output:**
```
🔧 Setting up Sasya Chikitsa Ollama build environment...
✅ Made scripts executable
🔍 Checking required files...
  ✅ Dockerfile.ollama-models
  ✅ Modelfile.llama3.1
  ✅ Modelfile.llava
  ✅ build-ollama-models.sh
  ✅ container-runtime-utils.sh

🎉 Setup completed successfully!
```

### Step 3: Verify Environment
```bash
# View all available options
./engine/build-ollama-models.sh --help

# Test with dry run (shows what would be built)
./engine/build-ollama-models.sh --dry-run --version test
```

## 🎯 Usage Guide

### Core Build Script: `build-ollama-models.sh`

This is your main tool for building Ollama images.

#### Basic Syntax
```bash
./engine/build-ollama-models.sh [OPTIONS]
```

#### Available Options

| Option | Values | Description | Example |
|--------|--------|-------------|---------|
| `--version` | any string | Version tag for images | `--version v1.0` |
| `--platform` | `amd64`, `arm64`, `both` | Target architecture | `--platform arm64` |
| `--models` | `llama31`, `llava`, `both`, `all` | Model combination | `--models llama31` |
| `--registry` | registry URL | Registry to push to | `--registry quay.io/myorg` |
| `--push` | (flag) | Auto-push to registry | `--push` |
| `--dry-run` | (flag) | Show what would be built | `--dry-run` |
| `--help` | (flag) | Show usage information | `--help` |

## 📖 Detailed Usage Scenarios

### Scenario 1: Development on Apple Silicon Mac

**Goal**: Build for local development and testing

```bash
# Build single model for your platform
./engine/build-ollama-models.sh \
  --version dev-$(date +%Y%m%d) \
  --platform arm64 \
  --models llama31

# Expected result: ollama-llama31-only:arm64-dev-20241226
```

### Scenario 2: Production Deployment

**Goal**: Build all combinations for production deployment

```bash
# Build everything with version tag
./engine/build-ollama-models.sh \
  --version v1.0 \
  --platform both \
  --models all

# This creates all 6 images:
# - ollama-llama31-only:arm64-v1.0
# - ollama-llama31-only:amd64-v1.0
# - ollama-llava-only:arm64-v1.0
# - ollama-llava-only:amd64-v1.0
# - ollama-both-models:arm64-v1.0
# - ollama-both-models:amd64-v1.0
```

### Scenario 3: Vision-Only Deployment

**Goal**: Build only vision AI models for image analysis

```bash
# Build llava-only for both platforms
./engine/build-ollama-models.sh \
  --version vision-v1.0 \
  --platform both \
  --models llava

# Creates:
# - ollama-llava-only:arm64-vision-v1.0
# - ollama-llava-only:amd64-vision-v1.0
```

### Scenario 4: Cross-Platform Team Development

**Goal**: Build and share images for team collaboration

```bash
# Build and push to registry for team sharing
./engine/build-ollama-models.sh \
  --version team-v1.0 \
  --platform both \
  --models all \
  --registry quay.io/yourorg \
  --push

# Team members can then pull:
# podman pull quay.io/yourorg/ollama-llama31-only:arm64-team-v1.0
```

### Scenario 5: CI/CD Pipeline

**Goal**: Automated builds in continuous integration

```bash
# In your CI/CD pipeline
export BUILD_VERSION=$(git rev-parse --short HEAD)

# Build without interactive prompts
echo "y" | ./engine/build-ollama-models.sh \
  --version $BUILD_VERSION \
  --platform both \
  --models all \
  --registry quay.io/yourorg

# Or use auto-push flag
./engine/build-ollama-models.sh \
  --version $BUILD_VERSION \
  --platform both \
  --models all \
  --registry quay.io/yourorg \
  --push
```

## 🔧 Running Built Images

### Basic Container Execution

```bash
# Run text-only model (llama-3.1)
podman run -it --rm -p 11434:11434 ollama-llama31-only:arm64-v1.0

# Run vision model (llava)
podman run -it --rm -p 11434:11434 ollama-llava-only:arm64-v1.0

# Run both models
podman run -it --rm -p 11434:11434 ollama-both-models:arm64-v1.0
```

### Testing the API

```bash
# Wait for container to start, then test
curl http://localhost:11434/api/version

# List available models
curl http://localhost:11434/api/tags

# Chat with llama-3.1
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "custom-llama3.1",
    "prompt": "How do I identify wheat rust disease?",
    "stream": false
  }'

# Vision analysis with llava (for images)
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "custom-llava",
    "prompt": "Analyze this crop image for diseases",
    "images": ["base64-encoded-image-here"],
    "stream": false
  }'
```

### Production Deployment

```bash
# Run as daemon with restart policy
podman run -d \
  --name ollama-production \
  --restart unless-stopped \
  -p 11434:11434 \
  -v ollama-data:/root/.ollama \
  ollama-both-models:arm64-v1.0

# Check logs
podman logs ollama-production

# Monitor health
curl http://localhost:11434/api/version
```

## 🎛️ Registry Management

### Understanding Push Behavior

The build script **asks before pushing** by default:

```bash
🎯 Image built successfully for arm64!
📦 Local image: ollama-llama31-only:arm64-v1.0
🌐 Registry target: quay.io/rajivranjan/ollama-llama31-only:arm64-v1.0

Do you want to push this image to registry? (y/N):
```

**Your options:**
- Press **Enter** (default): Keep local only
- Press **y**: Push to registry
- Use `--push` flag: Auto-push all images

### Registry Authentication

```bash
# Login to registry (one-time setup)
podman login quay.io
# Enter your quay.io username and password

# Verify login
podman info | grep -A 5 registries
```

### Manual Registry Operations

```bash
# Tag for different registry
podman tag ollama-llama31-only:arm64-v1.0 myregistry.com/ollama-llama31-only:arm64-v1.0

# Push manually
podman push myregistry.com/ollama-llama31-only:arm64-v1.0

# Pull from registry
podman pull quay.io/rajivranjan/ollama-llama31-only:arm64-v1.0
```

## 🐛 Troubleshooting

### Common Issues

#### ❌ "Container runtime not found"
```bash
# Solution: Install Docker or Podman
brew install podman  # macOS
sudo apt install podman  # Linux
```

#### ❌ "Permission denied" during build
```bash
# Solution: Fix script permissions
chmod +x ./engine/*.sh
./engine/setup-ollama-build.sh
```

#### ❌ "COPY failed: no such file or directory"
```bash
# Solution: Run from correct directory
pwd  # Should end with 'sasya-chikitsa'
cd /path/to/sasya-chikitsa
./engine/build-ollama-models.sh --version test
```

#### ❌ "Registry push failed"
```bash
# Solution: Login to registry
podman login quay.io
# Or check your internet connection
```

#### ❌ "Platform not supported"
```bash
# Solution: Use correct platform flag
--platform arm64     # for Apple Silicon
--platform amd64     # for Intel/AMD
--platform both      # for both architectures
```

#### ❌ "Out of disk space during build"
```bash
# Solution: Clean up Docker/Podman
podman system prune -a
podman volume prune

# Check disk usage
df -h
podman system df
```

### Model-Specific Issues

#### ❌ "Failed to pull llama-3.1:8b"
```bash
# This is expected during build - the container will pull it
# If persistent, check:
# 1. Internet connection
# 2. Ollama service availability
# 3. Try building with smaller models first
```

#### ❌ "Custom model creation failed"
```bash
# Check Modelfile syntax
cat engine/Modelfile.llama3.1
cat engine/Modelfile.llava

# Verify base model availability
podman run -it --rm ollama/ollama:latest ollama list
```

### Performance Issues

#### 🐌 "Build takes too long"
```bash
# Use dry-run to verify first
./engine/build-ollama-models.sh --dry-run --version test

# Build incrementally
./engine/build-ollama-models.sh --platform arm64 --models llama31 --version test
```

#### 🐌 "Container startup is slow"
```bash
# This is normal - models are large (4-5GB each)
# First startup downloads models from internet
# Monitor progress:
podman logs <container-name> -f
```

## 📊 Monitoring and Maintenance

### Image Management

```bash
# List all built images
podman images | grep ollama

# Check image sizes
podman images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Remove old images
podman rmi ollama-llama31-only:arm64-old-version

# Clean up unused images
podman image prune -a
```

### Container Health Monitoring

```bash
# Check running containers
podman ps

# View container health
podman inspect ollama-container | grep -A 10 Health

# Monitor API health
watch curl -s http://localhost:11434/api/version
```

### Log Analysis

```bash
# View container logs
podman logs ollama-container

# Follow logs in real-time
podman logs -f ollama-container

# Save logs to file
podman logs ollama-container > ollama.log
```

## 🔄 Update and Maintenance

### Rebuilding Images

```bash
# When base ollama/ollama image updates
podman pull ollama/ollama:latest

# Rebuild all images with new base
./engine/build-ollama-models.sh --version v1.1 --platform both --models all
```

### Model Updates

```bash
# Update Modelfile configurations
vi engine/Modelfile.llama3.1
vi engine/Modelfile.llava

# Rebuild with new configurations
./engine/build-ollama-models.sh --version updated --platform both --models all
```

### Script Updates

```bash
# Pull latest changes
git pull origin main

# Re-run setup
./engine/setup-ollama-build.sh

# Validate changes
./engine/build-ollama-models.sh --dry-run --version test
```

## 🤝 Team Collaboration Workflows

### Team Lead Workflow

1. **Create base images for team**:
   ```bash
   ./engine/build-ollama-models.sh --version team-v1.0 --platform both --models all --push
   ```

2. **Share registry information**:
   ```bash
   echo "Team images available at:"
   echo "quay.io/rajivranjan/ollama-llama31-only:arm64-team-v1.0"
   echo "quay.io/rajivranjan/ollama-llava-only:arm64-team-v1.0"
   # ... etc
   ```

### Team Member Workflow

1. **Pull pre-built images**:
   ```bash
   podman pull quay.io/rajivranjan/ollama-llama31-only:arm64-team-v1.0
   ```

2. **Or build locally for development**:
   ```bash
   ./engine/build-ollama-models.sh --version dev --platform arm64 --models llama31
   ```

### CI/CD Team Integration

```bash
# .github/workflows/ollama-build.yml example
name: Build Ollama Images
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build images
        run: |
          ./engine/setup-ollama-build.sh
          ./engine/build-ollama-models.sh \
            --version ${GITHUB_REF#refs/tags/} \
            --platform both \
            --models all \
            --registry ${{ secrets.REGISTRY_URL }} \
            --push
```

## 📚 Advanced Configuration

### Custom Model Configuration

Create your own Modelfile:

```bash
# Create custom Modelfile
cat > engine/Modelfile.custom << 'EOF'
FROM llama-3.1:8b

PARAMETER temperature 0.5
PARAMETER num_predict 256

SYSTEM """You are a specialized agricultural AI assistant focused on organic farming practices."""
EOF

# Update Dockerfile to use custom Modelfile
# Edit engine/Dockerfile.ollama-models and add handling for custom models
```

### Multi-Registry Deployment

```bash
# Build for multiple registries
for registry in "quay.io/rajivranjan" "docker.io/myorg" "ghcr.io/myorg"; do
  ./engine/build-ollama-models.sh \
    --version v1.0 \
    --platform both \
    --models all \
    --registry $registry \
    --push
done
```

### Resource Optimization

```bash
# Build with resource constraints
podman build \
  --memory 4g \
  --cpus 2 \
  -f engine/Dockerfile.ollama-models \
  -t ollama-optimized:latest .
```

## 📋 Checklists

### Pre-Build Checklist
- [ ] Container runtime installed and running
- [ ] Sufficient disk space (20GB+)
- [ ] Internet connection available
- [ ] Registry authentication configured (if pushing)
- [ ] Scripts have execute permissions

### Production Deployment Checklist
- [ ] All 6 images built and tested
- [ ] Images pushed to production registry
- [ ] Health checks passing
- [ ] API endpoints responding
- [ ] Models loading correctly
- [ ] Performance benchmarks completed

### Team Onboarding Checklist
- [ ] Repository cloned
- [ ] Container runtime installed
- [ ] Setup script executed
- [ ] Test build completed
- [ ] Registry access configured
- [ ] Documentation reviewed

## 🆘 Getting Help

### Self-Service Resources

1. **View built-in help**:
   ```bash
   ./engine/build-ollama-models.sh --help
   ```

2. **Test with dry-run**:
   ```bash
   ./engine/build-ollama-models.sh --dry-run --version test
   ```

3. **Check environment**:
   ```bash
   ./engine/setup-ollama-build.sh
   ```

### Common Questions

**Q: Which platform should I use?**
A: Use `arm64` for Apple Silicon Macs, `amd64` for Intel/AMD systems, `both` for universal deployment.

**Q: How much storage do I need?**
A: Each model is ~4-5GB, base images are ~1GB. Plan for 20GB+ for all combinations.

**Q: Can I run multiple models simultaneously?**
A: Yes, use the "both-models" images which include both llama-3.1 and llava models.

**Q: How do I update to newer model versions?**
A: Update the Modelfiles, then rebuild with a new version tag.

**Q: Can I customize the AI prompts?**
A: Yes, edit `engine/Modelfile.llama3.1` and `engine/Modelfile.llava`, then rebuild.

---

## 🎯 Summary

You now have a complete Docker build system for Ollama models that:

- ✅ **Builds 6 different image combinations** (platforms × model configs)
- ✅ **Auto-detects Docker/Podman** for seamless operation
- ✅ **Provides interactive control** over registry pushes
- ✅ **Includes comprehensive error handling** and troubleshooting
- ✅ **Supports team collaboration** workflows
- ✅ **Optimizes for agricultural AI** use cases

### Next Steps

1. **Test the system**: Run `./engine/build-ollama-models.sh --dry-run --version test`
2. **Build your first image**: Choose your platform and model combination
3. **Deploy and test**: Run the container and test the API endpoints
4. **Share with team**: Push to registry and share access

Happy building! 🚀

---

*This documentation was created for the Sasya Chikitsa agricultural AI project. For issues or improvements, please refer to the project repository.*
