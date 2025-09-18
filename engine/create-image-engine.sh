#! /bin/bash

# Check if we're in the correct directory (should be /sasya-chikitsa)
CURRENT_DIR=$(pwd)
if [[ ! "$CURRENT_DIR" =~ .*/sasya-chikitsa$ ]]; then
    echo "Error: This script must be run from the sasya-chikitsa directory."
    echo "Current directory: $CURRENT_DIR"
    echo "Please navigate to the sasya-chikitsa directory and run the script again."
    echo "Example: cd /path/to/sasya-chikitsa && ./engine/create-image-engine.sh"
    exit 1
fi

echo "Running from correct directory: $CURRENT_DIR"

# Check for container runtime (podman or docker)
CONTAINER_RUNTIME=""
if command -v podman &> /dev/null; then
    CONTAINER_RUNTIME="podman"
    echo "Using Podman as container runtime"
    
    # Check if logged in to container registry
    if ! podman info --format "{{.Registries}}" | grep -q "quay.io"; then
        echo "Warning: You may not be logged in to quay.io registry."
        echo "To login, run: podman login quay.io"
    fi
elif command -v docker &> /dev/null; then
    CONTAINER_RUNTIME="docker"
    echo "Using Docker as container runtime"
    
    # Check if logged in to container registry
    if ! docker info 2>/dev/null | grep -q "Registry:"; then
        echo "Warning: Docker daemon may not be running or you may not be logged in."
        echo "To login to quay.io, run: docker login quay.io"
    fi
else
    echo "Error: Neither Podman nor Docker is installed."
    echo "Please install either Podman or Docker to use this script."
    echo "Podman: https://podman.io/getting-started/installation"
    echo "Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Parse command line arguments
RUN_AFTER_BUILD=false
ARCH=""
VERSION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --run)
            RUN_AFTER_BUILD=true
            shift
            ;;
        --platform)
            if [[ $# -lt 2 ]] || [[ ! "$2" =~ ^(amd64|arm64)$ ]]; then
                echo "Error: --platform requires a value (amd64 or arm64)"
                echo "Usage: $0 --version <version> [--platform amd64|arm64] [--run]"
                exit 1
            fi
            ARCH="$2"
            shift 2
            ;;
        --version)
            if [[ $# -lt 2 ]] || [[ -z "$2" ]]; then
                echo "Error: --version requires a value"
                echo "Usage: $0 --version <version> [--platform amd64|arm64] [--run]"
                exit 1
            fi
            VERSION="$2"
            shift 2
            ;;
        *)
            echo "Error: Unknown option $1"
            echo "Usage: $0 --version <version> [--platform amd64|arm64] [--run]"
            echo "  --version: Version number for the image (mandatory)"
            echo "  --platform: Build for specific architecture (amd64 or arm64, default: both)"
            echo "  --run: Run the container after building (default: false)"
            exit 1
            ;;
    esac
done

# Validation: version is mandatory
if [ -z "$VERSION" ]; then
    echo "Error: --version is mandatory"
    echo "Usage: $0 --version <version> [--platform amd64|arm64] [--run]"
    echo "Example: $0 --version 6 --platform amd64 --run"
    exit 1
fi

# Validation: if --run is true, --platform must be specified
if [ "$RUN_AFTER_BUILD" = true ] && [ -z "$ARCH" ]; then
    echo "Error: --run requires --platform to be specified"
    echo "Usage: $0 --version <version> --platform amd64|arm64 --run"
    exit 1
fi

if [ -z "$ARCH" ]; then
    ARCH="both"
fi

echo "--------------------------------"
echo "Container runtime: $CONTAINER_RUNTIME"
echo "Building for architecture: $ARCH"
echo "Version: $VERSION"
echo "Running after build: $RUN_AFTER_BUILD"
echo "Starting the script"

# create the requirement file
if command -v uv &> /dev/null; then
    echo "Using uv package manager to compile requirements..."
    uv pip compile ./engine/pyproject.toml -o ./engine/requirements.txt
else
    echo "*** for now the script will assume an upto date requirements.txt file is present in the engine subdirectory ***"
    echo "Reason:"
    echo "uv package manager not found. Please install uv first."
    echo "You can install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "or you can install it with: pip install uv"
fi

if [ "$ARCH" = "amd64" ] || [ "$ARCH" = "both" ]; then
    $CONTAINER_RUNTIME pull --arch=amd64  python:3.12-slim
    $CONTAINER_RUNTIME tag docker.io/library/python:3.12-slim  localhost/python:amd64-3.12-slim
    $CONTAINER_RUNTIME build --platform linux/amd64 --build-arg BASE_TAG=amd64-3.12-slim -t engine:amd64-v$VERSION -f ./engine/Dockerfile.engine .
    $CONTAINER_RUNTIME tag localhost/engine:amd64-v$VERSION quay.io/rajivranjan/engine:amd64-v$VERSION
    $CONTAINER_RUNTIME push quay.io/rajivranjan/engine:amd64-v$VERSION
fi

if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "both" ]; then
    $CONTAINER_RUNTIME pull --arch=arm64  python:3.12-slim 
    $CONTAINER_RUNTIME tag docker.io/library/python:3.12-slim  localhost/python:arm64-3.12-slim
    $CONTAINER_RUNTIME build --platform linux/arm64 --build-arg BASE_TAG=arm64-3.12-slim -t engine:arm64-v$VERSION -f ./engine/Dockerfile.engine .
    $CONTAINER_RUNTIME tag localhost/engine:arm64-v$VERSION quay.io/rajivranjan/engine:arm64-v$VERSION
    $CONTAINER_RUNTIME push quay.io/rajivranjan/engine:arm64-v$VERSION
fi

if [ "$RUN_AFTER_BUILD" = true ]; then
    if [ "$ARCH" = "amd64" ]; then
        $CONTAINER_RUNTIME run -it --rm -p 8080:8080 -e OLLAMA_HOST=http://192.168.0.100:11434 localhost/engine:amd64-v$VERSION
    elif [ "$ARCH" = "arm64" ]; then
        $CONTAINER_RUNTIME run -it --rm -p 8080:8080 -e OLLAMA_HOST=http://192.168.0.100:11434 localhost/engine:arm64-v$VERSION
    fi    
fi
