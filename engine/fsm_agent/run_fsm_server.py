#!/usr/bin/env python3
"""
Runner script for Dynamic Planning Agent FSM Server

This script provides a simple way to start the FSM server with various configurations.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from fsm_agent.server.fsm_server import FSMServer


def setup_logging(log_level: str):
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_environment():
    """Check environment variables and dependencies"""
    print("🔍 Checking environment...")
    
    # Check Ollama configuration
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    
    print(f"   OLLAMA_HOST: {ollama_host}")
    print(f"   OLLAMA_MODEL: {ollama_model}")
    
    # Check if Ollama is accessible
    try:
        import requests
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            print(f"   ✅ Ollama accessible with {len(models)} models available")
            
            if not any(ollama_model in name for name in model_names):
                print(f"   ⚠️  Model '{ollama_model}' not found. Available models: {model_names}")
            else:
                print(f"   ✅ Model '{ollama_model}' is available")
        else:
            print(f"   ❌ Ollama not accessible (status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Cannot connect to Ollama: {str(e)}")
    
    # Check required directories
    required_dirs = [
        "../models",
        "../rag/data",
    ]
    
    for dir_path in required_dirs:
        full_path = Path(__file__).parent / dir_path
        if full_path.exists():
            print(f"   ✅ Directory exists: {dir_path}")
        else:
            print(f"   ⚠️  Directory missing: {dir_path}")
    
    print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Dynamic Planning Agent FSM Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_fsm_server.py                    # Start with default settings
  python run_fsm_server.py --port 8002        # Start on port 8002
  python run_fsm_server.py --host 0.0.0.0     # Bind to all interfaces
  python run_fsm_server.py --log-level debug  # Enable debug logging
  python run_fsm_server.py --reload           # Enable auto-reload for development
        """
    )
    
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080,
        help="Port to bind to (default: 8002)"
    )
    parser.add_argument(
        "--log-level", 
        default="info", 
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: info)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--check-env", 
        action="store_true", 
        help="Check environment and exit"
    )
    parser.add_argument(
        "--no-check", 
        action="store_true", 
        help="Skip environment check"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    print("🚀 Dynamic Planning Agent FSM Server")
    print("=" * 50)
    
    # Check environment
    if not args.no_check:
        check_environment()
    
    if args.check_env:
        print("Environment check completed.")
        return
    
    # Start server
    try:
        logger.info(f"Starting FSM server on {args.host}:{args.port}")
        
        server = FSMServer(args.host, args.port)
        
        server_config = {
            "log_level": args.log_level,
            "reload": args.reload,
        }
        
        if args.workers > 1:
            server_config["workers"] = args.workers
        
        print(f"🌐 Server starting at http://{args.host}:{args.port}")
        print("📡 API endpoints:")
        print(f"   Health Check: http://{args.host}:{args.port}/health")
        print(f"   Chat: http://{args.host}:{args.port}/sasya-chikitsa/chat")
        print(f"   Streaming Chat: http://{args.host}:{args.port}/sasya-chikitsa/chat-stream")
        print(f"   API Docs: http://{args.host}:{args.port}/docs")
        print()
        print("Press Ctrl+C to stop the server")
        print()
        
        server.run(**server_config)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
