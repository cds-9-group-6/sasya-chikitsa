#!/usr/bin/env python3
"""
MLflow Server Startup Script

This script starts the MLflow tracking server for the classification system.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def start_mlflow_server(host: str = "0.0.0.0", port: int = 5000, artifacts_path: str = "./mlflow_artifacts"):
    """
    Start MLflow tracking server
    
    Args:
        host: Host to bind to
        port: Port to bind to  
        artifacts_path: Path to store artifacts
    """
    
    # Create artifacts directory if it doesn't exist
    artifacts_dir = Path(artifacts_path)
    artifacts_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting MLflow Tracking Server")
    print("=" * 50)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Artifacts Path: {artifacts_path}")
    print()
    print("📊 MLflow UI will be available at:")
    print(f"   http://{host}:{port}")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    # MLflow server command
    cmd = [
        "mlflow", "server",
        "--host", host,
        "--port", str(port),
        "--default-artifact-root", str(artifacts_dir.absolute()),
        "--backend-store-uri", f"sqlite:///{artifacts_dir.absolute()}/mlflow.db"
    ]
    
    try:
        # Start MLflow server
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start MLflow server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 MLflow server stopped by user")
    except Exception as e:
        print(f"❌ Error starting MLflow server: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Start MLflow Tracking Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_mlflow_server.py                        # Start with defaults
  python start_mlflow_server.py --port 5001            # Start on port 5001
  python start_mlflow_server.py --host localhost       # Bind to localhost only
  python start_mlflow_server.py --artifacts ./data     # Use custom artifacts path
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
        default=5000,
        help="Port to bind to (default: 5000)"
    )
    parser.add_argument(
        "--artifacts", 
        default="./mlflow_artifacts",
        help="Path to store artifacts (default: ./mlflow_artifacts)"
    )
    
    args = parser.parse_args()
    
    start_mlflow_server(
        host=args.host,
        port=args.port, 
        artifacts_path=args.artifacts
    )

if __name__ == "__main__":
    main()

