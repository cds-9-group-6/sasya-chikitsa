#!/bin/bash

# Planning Agent Server Startup Script
# Usage: ./run_planning_server.sh [--dev] [--debug] [--port PORT]

set -e  # Exit on any error

# Default values
HOST="0.0.0.0"
PORT="8080"
RELOAD=""
DEBUG=""
ENV_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev|--reload)
            RELOAD="--reload"
            echo "🔄 Development mode enabled (auto-reload)"
            shift
            ;;
        --debug)
            DEBUG="--debug"
            echo "🐛 Debug logging enabled"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --env)
            ENV_FILE="$2"
            echo "🌍 Using environment file: $ENV_FILE"
            shift 2
            ;;
        --help|-h)
            echo "Planning Agent Server Startup Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dev, --reload    Enable auto-reload for development"
            echo "  --debug           Enable debug logging"
            echo "  --port PORT       Specify port (default: 8001)"
            echo "  --host HOST       Specify host (default: 0.0.0.0)"
            echo "  --env FILE        Load environment variables from .env file"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Start server on 0.0.0.0:8001"
            echo "  $0 --dev --port 8002  # Development mode on port 8002"
            echo "  $0 --debug            # Start with debug logging"
            echo "  $0 --env ../.env      # Load environment from engine/.env"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ENGINE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$ENGINE_DIR")"

echo "🌱 Sasya Chikitsa Planning Agent Server"
echo "========================================"
echo ""
echo "📁 Script directory: $SCRIPT_DIR"
echo "📁 Engine directory: $ENGINE_DIR" 
echo "📁 Project root: $PROJECT_ROOT"
echo ""

# Load environment variables from .env file if specified
load_env_file() {
    local env_file="$1"
    if [[ -f "$env_file" ]]; then
        echo "🌍 Loading environment variables from: $env_file"
        # Export variables from .env file, ignoring comments and empty lines
        set -a  # Automatically export all variables
        source "$env_file"
        set +a  # Stop auto-exporting
        echo "✅ Environment variables loaded"
        
        # Show important variables if they're set
        if [[ -n "$OLLAMA_HOST" ]]; then
            echo "   🦙 OLLAMA_HOST: $OLLAMA_HOST"
        fi
        if [[ -n "$OLLAMA_MODEL" ]]; then
            echo "   🤖 OLLAMA_MODEL: $OLLAMA_MODEL"
        fi
        if [[ -n "$OPENAI_API_KEY" ]]; then
            echo "   🔑 OPENAI_API_KEY: [CONFIGURED]"
        fi
    else
        echo "⚠️  Environment file not found: $env_file"
        echo "   Creating example .env file..."
        cat > "$env_file" << 'EOF'
# Planning Agent Environment Configuration

# Ollama Configuration (uncomment and configure for local Ollama)
#OLLAMA_HOST=http://localhost:11434
#OLLAMA_MODEL=llama3.1:8b

# OpenAI Configuration (uncomment and add your API key)
#OPENAI_API_KEY=your_openai_api_key_here
#OPENAI_MODEL=gpt-4

# Other Configuration
#DEBUG=true
EOF
        echo "   📝 Example .env file created at: $env_file"
        echo "   Edit it with your configuration and rerun the script"
        exit 1
    fi
}

# Auto-detect and load .env file
if [[ -n "$ENV_FILE" ]]; then
    # User specified explicit .env file
    load_env_file "$ENV_FILE"
elif [[ -f "$ENGINE_DIR/.env" ]]; then
    # Load from engine directory
    echo "🔍 Auto-detected .env file in engine directory"
    load_env_file "$ENGINE_DIR/.env"
elif [[ -f "$PROJECT_ROOT/.env" ]]; then
    # Load from project root
    echo "🔍 Auto-detected .env file in project root"
    load_env_file "$PROJECT_ROOT/.env"
elif [[ -f ".env" ]]; then
    # Load from current directory
    echo "🔍 Auto-detected .env file in current directory"
    load_env_file ".env"
else
    echo "💡 No .env file found. Creating example .env in current directory..."
    load_env_file ".env"  # This will create the example file
fi

echo ""

# Set up Python path
export PYTHONPATH="$SCRIPT_DIR:$ENGINE_DIR:$PROJECT_ROOT:$PYTHONPATH"
echo "🐍 PYTHONPATH: $PYTHONPATH"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

echo "Python prefix: $(python3 -c 'import sys; print(sys.prefix)')"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected (recommended to use one)"
fi

# Change to script directory
cd "$SCRIPT_DIR"

# Check dependencies first
echo ""
echo "🔍 Checking dependencies..."
if ! python3 start_server.py --check-only; then
    echo ""
    echo "❌ Dependency check failed. Install requirements:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Start the server
echo ""
echo "🚀 Starting Planning Agent Server..."
echo "   Host: $HOST"
echo "   Port: $PORT"
if [[ "$RELOAD" != "" ]]; then
    echo "   Mode: Development (auto-reload)"
else
    echo "   Mode: Production"
fi
if [[ "$DEBUG" != "" ]]; then
    echo "   Logging: Debug level"
else
    echo "   Logging: Info level"
fi
echo ""
echo "📡 Server will be available at: http://$HOST:$PORT"
echo "📖 API documentation: http://$HOST:$PORT/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
python3 start_server.py --host "$HOST" --port "$PORT" $RELOAD $DEBUG
