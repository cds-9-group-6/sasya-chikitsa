# 🤖 Sasya Chikitsa Ollama Multi-Model Build System

**Complete Docker build system for agricultural AI models with platform-specific containers.**

## 📚 Documentation Index

| Document | Purpose | Target Audience |
|----------|---------|-----------------|
| **[🚀 Quick Reference](./OLLAMA_QUICK_REFERENCE.md)** | Essential commands and common workflows | Developers, daily users |
| **[📖 Complete Guide](./README_OLLAMA_BUILDS.md)** | Comprehensive documentation with all details | Team leads, new users |
| **[🔄 Build Flow](./OLLAMA_BUILD_FLOW.md)** | Visual guides and architecture diagrams | Technical architects |
| **[📋 This Index](./OLLAMA_INDEX.md)** | Navigation and overview | All users |

## 🎯 Choose Your Starting Point

### 👩‍💻 **I'm a Developer** → Start with [Quick Reference](./OLLAMA_QUICK_REFERENCE.md)
- Need to build images quickly
- Familiar with Docker/containers
- Want essential commands only

### 🎓 **I'm New to This** → Start with [Complete Guide](./README_OLLAMA_BUILDS.md)
- First time using the system
- Need setup instructions
- Want detailed explanations

### 🏗️ **I'm an Architect** → Start with [Build Flow](./OLLAMA_BUILD_FLOW.md)
- Understanding system architecture
- Planning deployment strategies
- Customizing the build process

### 👥 **I'm a Team Lead** → Read [Complete Guide](./README_OLLAMA_BUILDS.md) sections:
- Team Collaboration Workflows
- Registry Management
- CI/CD Integration

## ⚡ Ultra-Quick Start

```bash
# 1. Setup
./engine/setup-ollama-build.sh

# 2. Build (choose one)
./engine/build-ollama-models.sh --version v1.0 --platform arm64 --models llama31  # Single model
./engine/build-ollama-models.sh --version v1.0 --platform both --models all      # Everything

# 3. Run
podman run -it --rm -p 11434:11434 ollama-llama31-only:arm64-v1.0

# 4. Test
curl http://localhost:11434/api/version
```

## 🛠️ What This System Builds

| Output | Platform | Models | Use Case |
|--------|----------|--------|----------|
| `ollama-llama31-only:arm64-v1.0` | Apple Silicon | Text AI | M1/M2 Mac chat |
| `ollama-llama31-only:amd64-v1.0` | Intel/AMD | Text AI | Server chat |
| `ollama-llava-only:arm64-v1.0` | Apple Silicon | Vision AI | M1/M2 Mac vision |
| `ollama-llava-only:amd64-v1.0` | Intel/AMD | Vision AI | Server vision |
| `ollama-both-models:arm64-v1.0` | Apple Silicon | Both AIs | M1/M2 Mac full suite |
| `ollama-both-models:amd64-v1.0` | Intel/AMD | Both AIs | Server full suite |

## 🔍 Key Features

- ✅ **6 different image combinations** (platforms × model configs)
- ✅ **Auto-detects Docker/Podman** for seamless operation
- ✅ **Interactive registry control** (asks before pushing)
- ✅ **Platform-specific optimization** (ARM64 vs AMD64)
- ✅ **Agricultural AI specialization** (custom prompts for farming)
- ✅ **Comprehensive error handling** and troubleshooting
- ✅ **Team collaboration support** (shared registry workflows)

## 🤔 Common Questions

**Q: Which document should I read first?**  
A: If you just want to build and run → [Quick Reference](./OLLAMA_QUICK_REFERENCE.md). If you're setting up for a team → [Complete Guide](./README_OLLAMA_BUILDS.md).

**Q: How long does it take to build all images?**  
A: 1-3 hours total, depending on internet speed. Each model is ~4-5GB download.

**Q: Can I build just one image?**  
A: Yes! Use `--platform arm64 --models llama31` for a single image.

**Q: Do I need to push to a registry?**  
A: No, the script asks first. Press Enter to keep local only.

**Q: What if I have problems?**  
A: Check the [Troubleshooting section](./README_OLLAMA_BUILDS.md#-troubleshooting) in the Complete Guide.

## 📁 File Structure

```
sasya-chikitsa/engine/
├── 📄 OLLAMA_INDEX.md              ← You are here
├── 🚀 OLLAMA_QUICK_REFERENCE.md    ← Essential commands
├── 📖 README_OLLAMA_BUILDS.md      ← Complete documentation  
├── 🔄 OLLAMA_BUILD_FLOW.md         ← Architecture diagrams
├── 🔧 build-ollama-models.sh       ← Main build script
├── 🐳 Dockerfile.ollama-models     ← Multi-model Dockerfile
├── 📝 Modelfile.llama3.1           ← Text AI configuration
├── 📝 Modelfile.llava              ← Vision AI configuration
├── 🛠️ container-runtime-utils.sh   ← Docker/Podman utilities
└── ⚙️ setup-ollama-build.sh        ← Environment setup
```

## 🎯 Success Criteria

After using this system, you should be able to:

- [ ] Build Ollama images for your platform
- [ ] Run agricultural AI models in containers
- [ ] Deploy vision and text AI models
- [ ] Share images with your team
- [ ] Troubleshoot common issues
- [ ] Customize AI prompts for farming use cases

## 🆘 Get Help

1. **Check the docs**: Start with appropriate guide above
2. **Test with dry-run**: `./engine/build-ollama-models.sh --dry-run`
3. **Validate setup**: `./engine/setup-ollama-build.sh`
4. **View help**: `./engine/build-ollama-models.sh --help`

---

**Ready to get started?** Choose your path above and begin building! 🚀
