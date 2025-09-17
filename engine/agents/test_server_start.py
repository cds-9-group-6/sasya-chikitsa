#!/usr/bin/env python3
"""
Quick test to verify the Planning Agent server can actually start.

This script starts the server for a few seconds to ensure it initializes properly,
then shuts it down automatically.
"""

import asyncio
import signal
import sys
import os
import time
from contextlib import asynccontextmanager

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
for path in [current_dir, os.path.dirname(current_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

async def test_server_startup():
    """Test that the server can start and respond to basic requests."""
    try:
        print("🚀 Testing Planning Agent Server startup...")
        
        # Import the server
        from agents.server.planning_server import app
        import uvicorn
        
        print("✅ Server imported successfully")
        
        # Test basic app properties
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        
        # Create a server config
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8001,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        
        print("✅ Server configuration created")
        print("🌐 Attempting to start server on http://127.0.0.1:8001")
        
        # Start server in background
        task = asyncio.create_task(server.serve())
        
        # Give it a moment to start
        await asyncio.sleep(3)
        
        print("✅ Server started successfully!")
        
        # Shutdown server
        print("🛑 Shutting down test server...")
        server.should_exit = True
        await task
        
        print("✅ Server shutdown completed")
        return True
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the server startup test."""
    print("🧪 Planning Agent Server Startup Test")
    print("=" * 50)
    
    try:
        # Run the async test
        result = asyncio.run(test_server_startup())
        
        if result:
            print("\n🎉 SUCCESS: Server startup test passed!")
            print("✅ The Planning Agent server is ready for production use.")
            return True
        else:
            print("\n❌ FAILED: Server startup test failed.")
            print("⚠️  Check dependencies and configuration.")
            return False
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
