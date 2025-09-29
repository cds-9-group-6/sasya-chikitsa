# 🚀 Ollama Builds - Quick Reference

**TL;DR**: Build 6 different Ollama images with pre-configured agricultural AI models.

## ⚡ Quick Commands

```bash
# Setup (once)
./engine/setup-ollama-build.sh

# Build everything
./engine/build-ollama-models.sh --version v1.0

# Build for your platform only
./engine/build-ollama-models.sh --version v1.0 --platform arm64

# Test without building
./engine/build-ollama-models.sh --dry-run --version test

# Help
./engine/build-ollama-models.sh --help
```

## 📋 Build Matrix

| Command | Result | Use Case |
|---------|--------|----------|
| `--models llama31` | Text AI only | Chat, Q&A, text analysis |
| `--models llava` | Vision AI only | Image analysis, crop diseases |
| `--models both` | Full AI suite | Complete agricultural AI |
| `--platform arm64` | Apple Silicon | M1/M2/M3 Macs |
| `--platform amd64` | Intel/AMD | Most servers, older Macs |
| `--platform both` | Universal | All platforms |

## 🏃‍♂️ Common Workflows

### Developer (Apple Silicon)
```bash
./engine/build-ollama-models.sh --version dev --platform arm64 --models llama31
```

### Production (All platforms)
```bash
./engine/build-ollama-models.sh --version v1.0 --platform both --models all
```

### Vision-only deployment
```bash
./engine/build-ollama-models.sh --version vision --platform both --models llava
```

## 🐳 Running Images

```bash
# Run and test
podman run -it --rm -p 11434:11434 ollama-llama31-only:arm64-v1.0

# Test API
curl http://localhost:11434/api/version
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | `chmod +x ./engine/*.sh` |
| Wrong directory | `cd sasya-chikitsa` first |
| No container runtime | Install Docker or Podman |
| Registry push failed | `podman login quay.io` |

## 📖 Full Documentation

For complete details, see: [README_OLLAMA_BUILDS.md](./README_OLLAMA_BUILDS.md)
