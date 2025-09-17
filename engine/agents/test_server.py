#!/usr/bin/env python3
"""
Test script to verify Planning Agent Server components can be initialized.

This script tests the core components without starting the full server.
"""

import sys
import os
import traceback

# Add paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        print(f"  ✅ FastAPI {fastapi.__version__}")
    except ImportError as e:
        print(f"  ❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print(f"  ✅ Uvicorn {uvicorn.__version__}")
    except ImportError as e:
        print(f"  ❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import pydantic
        print(f"  ✅ Pydantic {pydantic.__version__}")
    except ImportError as e:
        print(f"  ❌ Pydantic import failed: {e}")
        return False
    
    return True

def test_planning_agent():
    """Test that planning agent components can be imported."""
    print("\n🧠 Testing Planning Agent components...")
    
    try:
        from agents.server.planning_agent import PlanningAgent, WorkflowState
        print("  ✅ PlanningAgent imported")
        print("  ✅ WorkflowState imported")
    except ImportError as e:
        print(f"  ❌ Planning Agent import failed: {e}")
        print("     This is expected if CNN/LLM dependencies aren't fully installed")
        return False
    
    try:
        from agents.session.session_manager import SessionManager
        print("  ✅ SessionManager imported")
    except ImportError as e:
        print(f"  ❌ SessionManager import failed: {e}")
        return False
    
    try:
        from agents.flow.workflow_controller import WorkflowController
        print("  ✅ WorkflowController imported")
    except ImportError as e:
        print(f"  ❌ WorkflowController import failed: {e}")
        return False
    
    return True

def test_server_module():
    """Test that the server module can be imported."""
    print("\n🖥️  Testing Server module...")
    
    try:
        from agents.server.planning_server import app
        print("  ✅ FastAPI app imported")
        print(f"  ✅ App title: {app.title}")
        print(f"  ✅ App version: {app.version}")
    except ImportError as e:
        print(f"  ❌ Server module import failed: {e}")
        print("     This is expected if CNN/LLM dependencies aren't fully installed")
        return False
    except Exception as e:
        print(f"  ❌ Server initialization failed: {e}")
        print(f"  🔍 Full traceback:\n{traceback.format_exc()}")
        return False
    
    return True

def test_initialization():
    """Test component initialization without starting the server."""
    print("\n⚙️  Testing component initialization...")
    
    try:
        # Test SessionManager initialization
        from agents.session.session_manager import SessionManager
        session_manager = SessionManager()
        print("  ✅ SessionManager initialized")
    except Exception as e:
        print(f"  ❌ SessionManager initialization failed: {e}")
        return False
    
    try:
        # Test WorkflowController initialization  
        from agents.flow.workflow_controller import WorkflowController
        workflow_controller = WorkflowController()
        print("  ✅ WorkflowController initialized")
    except Exception as e:
        print(f"  ❌ WorkflowController initialization failed: {e}")
        return False
    
    # Planning Agent initialization requires external dependencies
    # so we'll skip that for this basic test
    print("  ⏭️  Skipping PlanningAgent initialization (requires CNN/LLM)")
    
    return True

def main():
    """Run all tests."""
    print("🧪 Planning Agent Server Component Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_imports),
        ("Planning Agent Components", test_planning_agent), 
        ("Server Module", test_server_module),
        ("Component Initialization", test_initialization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n💥 {test_name}: ERROR - {e}")
            print(f"   Traceback: {traceback.format_exc()}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Server is ready to run.")
        return True
    else:
        print("⚠️  Some tests failed. Check dependencies and setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
