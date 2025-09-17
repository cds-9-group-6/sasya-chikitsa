#!/usr/bin/env python3
"""
Simple startup script for the Planning Agent Server.

This script sets up the environment and starts the server with sensible defaults.
"""

import os
import sys
import argparse

def setup_environment():
    """Set up the Python environment for the planning agent."""
    # Add the current directory and engine directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    engine_dir = os.path.dirname(current_dir)
    project_root = os.path.dirname(engine_dir)
    
    # Add all necessary paths
    paths_to_add = [current_dir, engine_dir, project_root]
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # Set PYTHONPATH environment variable
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    new_pythonpath = ':'.join(paths_to_add)
    if current_pythonpath:
        new_pythonpath += ':' + current_pythonpath
    
    os.environ['PYTHONPATH'] = new_pythonpath
    
    print(f"✅ Environment setup complete")
    print(f"   Current directory: {current_dir}")
    print(f"   Engine directory: {engine_dir}")
    print(f"   PYTHONPATH: {new_pythonpath}")

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(description="Start Planning Agent Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to (default: 8001)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--check-only", action="store_true", help="Only check dependencies, don't start server")
    
    args = parser.parse_args()
    
    print("🌱 Sasya Chikitsa Planning Agent Server Startup")
    print("=" * 50)
    
    # Set up environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    if args.check_only:
        print("✅ Environment check complete. Server ready to start.")
        sys.exit(0)
    
    # Start the server
    print(f"\n🚀 Starting server on {args.host}:{args.port}")
    if args.reload:
        print("🔄 Auto-reload enabled (development mode)")
    if args.debug:
        print("🐛 Debug logging enabled")
    
    try:
        # Import and run the server
        from agents.server.planning_server import app
        import uvicorn
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="debug" if args.debug else "info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed and paths are correct")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
