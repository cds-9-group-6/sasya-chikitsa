#!/bin/bash

# Container Runtime Utilities - Shared functions for Docker/Podman compatibility
# This file provides common functions for detecting and working with both Docker and Podman
# Adapted for Sasya Chikitsa Ollama model builds

# Global variables
CONTAINER_RUNTIME=""
RUNTIME_VERSION=""
SUPPORTS_BUILDKIT=false
SUPPORTS_CACHE_MOUNT=false

# Function to detect and configure container runtime
detect_container_runtime() {
    echo "🔍 Detecting container runtime..."
    
    # Check for Podman first (preferred by user)
    if command -v podman &> /dev/null; then
        CONTAINER_RUNTIME="podman"
        RUNTIME_VERSION=$(podman --version | cut -d' ' -f3)
        
        echo "🐙 Found Podman v$RUNTIME_VERSION"
        
        # Check Podman capabilities
        if podman --help | grep -q "buildx\|build.*cache"; then
            SUPPORTS_CACHE_MOUNT=true
            echo "  ✅ Cache mount support detected"
        else
            echo "  ℹ️  Cache mount not available (consider upgrading Podman)"
        fi
        
        # Check if logged in to registry
        if podman info --format "{{.Registries}}" 2>/dev/null | grep -q "quay.io\|docker.io"; then
            echo "  ✅ Registry credentials detected"
        else
            echo "  ⚠️  No registry credentials found"
            echo "     💡 To login: podman login quay.io"
        fi
        
    # Check for Docker as fallback
    elif command -v docker &> /dev/null; then
        CONTAINER_RUNTIME="docker"
        RUNTIME_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        
        echo "🐳 Found Docker v$RUNTIME_VERSION"
        
        # Check if Docker daemon is running
        if ! docker info &>/dev/null; then
            echo "  ❌ Docker daemon is not running!"
            echo "     💡 Start Docker Desktop or run: sudo systemctl start docker"
            return 1
        fi
        
        # Check Docker capabilities
        if docker version --format '{{.Server.Version}}' &>/dev/null; then
            # Check for BuildKit support
            if docker buildx version &>/dev/null; then
                SUPPORTS_BUILDKIT=true
                SUPPORTS_CACHE_MOUNT=true
                echo "  ✅ BuildKit and cache mount support detected"
            else
                echo "  ℹ️  BuildKit not available (install docker-buildx for cache mounts)"
            fi
            
            # Check registry credentials
            if docker info 2>/dev/null | grep -q "Registry:"; then
                echo "  ✅ Docker daemon accessible"
            fi
        fi
        
    else
        echo "❌ No container runtime found!"
        echo ""
        echo "Please install one of the following:"
        echo "  🐙 Podman (recommended): https://podman.io/getting-started/installation"
        echo "  🐳 Docker: https://docs.docker.com/get-docker/"
        echo ""
        echo "📱 macOS users can use:"
        echo "  • brew install podman"
        echo "  • Docker Desktop from docker.com"
        return 1
    fi
    
    return 0
}

# Function to check if image exists (compatible with both runtimes)
image_exists() {
    local image_name="$1"
    
    if [ -z "$image_name" ]; then
        echo "❌ Error: image_exists() requires an image name"
        return 1
    fi
    
    case "$CONTAINER_RUNTIME" in
        "podman")
            podman image exists "$image_name" 2>/dev/null
            ;;
        "docker")
            docker image inspect "$image_name" &>/dev/null
            ;;
        *)
            echo "❌ Error: Unknown container runtime: $CONTAINER_RUNTIME"
            return 1
            ;;
    esac
}

# Function to pull image with progress (compatible with both runtimes)
pull_image() {
    local image_name="$1"
    local platform="$2"
    
    if [ -z "$image_name" ]; then
        echo "❌ Error: pull_image() requires an image name"
        return 1
    fi
    
    echo "📥 Pulling $image_name for $platform..."
    
    case "$CONTAINER_RUNTIME" in
        "podman")
            if [ -n "$platform" ]; then
                podman pull --arch="$platform" "$image_name"
            else
                podman pull "$image_name"
            fi
            ;;
        "docker")
            if [ -n "$platform" ]; then
                docker pull --platform="linux/$platform" "$image_name"
            else
                docker pull "$image_name"
            fi
            ;;
        *)
            echo "❌ Error: Unknown container runtime: $CONTAINER_RUNTIME"
            return 1
            ;;
    esac
}

# Function to build image with optimal settings for each runtime
build_image() {
    local dockerfile="$1"
    local image_tag="$2"
    local platform="$3"
    local build_args="$4"
    local use_cache="$5"
    
    if [ -z "$dockerfile" ] || [ -z "$image_tag" ]; then
        echo "❌ Error: build_image() requires dockerfile and image_tag"
        return 1
    fi
    
    echo "🔨 Building $image_tag..."
    
    local build_cmd="$CONTAINER_RUNTIME build"
    
    # Add platform if specified
    if [ -n "$platform" ]; then
        build_cmd="$build_cmd --platform linux/$platform"
    fi
    
    # Add build arguments
    if [ -n "$build_args" ]; then
        build_cmd="$build_cmd $build_args"
    fi
    
    # Add cache options based on runtime and support
    if [ "$use_cache" = "true" ]; then
        case "$CONTAINER_RUNTIME" in
            "podman")
                if [ "$SUPPORTS_CACHE_MOUNT" = "true" ]; then
                    echo "  📦 Using Podman cache mounting"
                    # Podman cache mount syntax (if supported)
                    build_cmd="$build_cmd --cache-to type=local,dest=/tmp/podman-cache"
                else
                    echo "  📦 Using standard Podman build (no cache mount)"
                fi
                ;;
            "docker")
                if [ "$SUPPORTS_BUILDKIT" = "true" ]; then
                    echo "  📦 Using Docker BuildKit with cache mounting"
                    export DOCKER_BUILDKIT=1
                    # BuildKit cache mount is handled in Dockerfile with RUN --mount
                else
                    echo "  📦 Using standard Docker build (no cache mount)"
                fi
                ;;
        esac
    fi
    
    # Add dockerfile and tag
    build_cmd="$build_cmd -f $dockerfile -t $image_tag ."
    
    echo "  🔧 Command: $build_cmd"
    echo ""
    
    # Execute the build
    eval "$build_cmd"
}

# Function to run container with runtime-specific optimizations
run_container() {
    local image_name="$1"
    local port_mapping="$2"
    local env_vars="$3"
    local extra_args="$4"
    
    if [ -z "$image_name" ]; then
        echo "❌ Error: run_container() requires an image name"
        return 1
    fi
    
    echo "🚀 Starting container from $image_name..."
    
    local run_cmd="$CONTAINER_RUNTIME run -it --rm"
    
    # Add port mapping
    if [ -n "$port_mapping" ]; then
        run_cmd="$run_cmd -p $port_mapping"
    fi
    
    # Add environment variables
    if [ -n "$env_vars" ]; then
        run_cmd="$run_cmd $env_vars"
    fi
    
    # Add extra arguments
    if [ -n "$extra_args" ]; then
        run_cmd="$run_cmd $extra_args"
    fi
    
    # Add image name
    run_cmd="$run_cmd $image_name"
    
    echo "  🔧 Command: $run_cmd"
    echo ""
    
    # Execute the run
    eval "$run_cmd"
}

# Function to display runtime-specific information
show_runtime_info() {
    echo ""
    echo "🔧 Container Runtime Information:"
    echo "  📦 Runtime: $CONTAINER_RUNTIME v$RUNTIME_VERSION"
    echo "  🚀 Cache Mount: $([ "$SUPPORTS_CACHE_MOUNT" = "true" ] && echo "✅ Supported" || echo "❌ Not available")"
    echo "  🏗️  BuildKit: $([ "$SUPPORTS_BUILDKIT" = "true" ] && echo "✅ Supported" || echo "❌ Not available")"
    
    case "$CONTAINER_RUNTIME" in
        "podman")
            echo "  💡 Podman Tips:"
            echo "     • Rootless by default (more secure)"
            echo "     • Compatible with Docker commands"
            echo "     • No daemon required"
            ;;
        "docker")
            echo "  💡 Docker Tips:"
            echo "     • Enable BuildKit: export DOCKER_BUILDKIT=1"
            echo "     • Use Docker Desktop for macOS/Windows"
            echo "     • Requires daemon to be running"
            ;;
    esac
    echo ""
}

# Function to handle registry operations
registry_login_help() {
    local registry="${1:-quay.io}"
    
    echo "🔐 Registry Login Help for $CONTAINER_RUNTIME:"
    case "$CONTAINER_RUNTIME" in
        "podman")
            echo "  podman login $registry"
            ;;
        "docker")
            echo "  docker login $registry"
            ;;
    esac
}

# Function to clean up resources
cleanup_resources() {
    echo "🧹 Cleanup commands for $CONTAINER_RUNTIME:"
    case "$CONTAINER_RUNTIME" in
        "podman")
            echo "  • Remove unused images: podman image prune -a"
            echo "  • Remove all containers: podman container prune"
            echo "  • System cleanup: podman system prune -a"
            ;;
        "docker")
            echo "  • Remove unused images: docker image prune -a"
            echo "  • Remove all containers: docker container prune"
            echo "  • System cleanup: docker system prune -a"
            ;;
    esac
}

# Export functions for use in other scripts
export -f detect_container_runtime
export -f image_exists
export -f pull_image
export -f build_image
export -f run_container
export -f show_runtime_info
export -f registry_login_help
export -f cleanup_resources
