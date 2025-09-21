#!/usr/bin/env python3
"""
Test script for the refactored LangGraph workflow

This script tests the basic functionality of the refactored workflow
to ensure the modular node architecture works correctly.
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_llm_config() -> Dict[str, Any]:
    """Create a test LLM configuration"""
    return {
        "model": "llama2",  # Replace with actual model
        "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),  # Configurable Ollama URL
        "temperature": 0.1
    }

async def test_workflow_initialization():
    """Test that the workflow initializes correctly with the new architecture"""
    logger.info("🧪 Testing workflow initialization...")
    
    try:
        from core.langgraph_workflow import DynamicPlanningWorkflow
        
        llm_config = create_test_llm_config()
        workflow = DynamicPlanningWorkflow(llm_config)
        
        # Check that node factory was created
        assert hasattr(workflow, 'node_factory'), "Workflow should have node_factory attribute"
        
        # Check that all expected nodes were created
        expected_nodes = ["initial", "classifying", "prescribing", "vendor_query", "show_vendors", 
                         "order_booking", "followup", "completed", "error"]
        actual_nodes = workflow.node_factory.list_node_names()
        
        for expected_node in expected_nodes:
            assert expected_node in actual_nodes, f"Expected node '{expected_node}' not found in {actual_nodes}"
        
        logger.info("✅ Workflow initialization test passed!")
        logger.info(f"✅ Created {len(actual_nodes)} nodes: {actual_nodes}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Workflow initialization test failed: {str(e)}")
        return False

async def test_node_factory_functionality():
    """Test that the node factory works correctly"""
    logger.info("🧪 Testing node factory functionality...")
    
    try:
        from core.langgraph_workflow import DynamicPlanningWorkflow
        
        llm_config = create_test_llm_config()
        workflow = DynamicPlanningWorkflow(llm_config)
        
        # Test getting individual nodes
        initial_node = workflow.node_factory.get_node("initial")
        assert initial_node is not None, "Should be able to get initial node"
        
        classifying_node = workflow.node_factory.get_node("classifying")
        assert classifying_node is not None, "Should be able to get classifying node"
        
        # Test node properties
        assert initial_node.node_name == "initial", f"Initial node should have name 'initial', got '{initial_node.node_name}'"
        assert classifying_node.node_name == "classifying", f"Classifying node should have name 'classifying', got '{classifying_node.node_name}'"
        
        # Test that nodes have required attributes
        assert hasattr(initial_node, 'tools'), "Nodes should have tools attribute"
        assert hasattr(initial_node, 'llm'), "Nodes should have llm attribute"
        assert hasattr(initial_node, 'execute'), "Nodes should have execute method"
        
        logger.info("✅ Node factory functionality test passed!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Node factory functionality test failed: {str(e)}")
        return False

async def test_basic_workflow_structure():
    """Test that the workflow has the correct structure"""
    logger.info("🧪 Testing workflow structure...")
    
    try:
        from core.langgraph_workflow import DynamicPlanningWorkflow
        
        llm_config = create_test_llm_config()
        workflow = DynamicPlanningWorkflow(llm_config)
        
        # Check that workflow has been compiled
        assert hasattr(workflow, 'app'), "Workflow should have compiled app attribute"
        assert workflow.app is not None, "Workflow app should not be None"
        
        # Check that workflow has required methods
        assert hasattr(workflow, 'process_message'), "Workflow should have process_message method"
        assert hasattr(workflow, 'stream_process_message'), "Workflow should have stream_process_message method"
        
        logger.info("✅ Workflow structure test passed!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Workflow structure test failed: {str(e)}")
        return False

async def test_state_creation():
    """Test that workflow state can be created"""
    logger.info("🧪 Testing state creation...")
    
    try:
        from core.workflow_state import create_initial_state
        
        # Create a test state
        session_id = "test_session_123"
        user_message = "Hello, can you help me analyze my plant?"
        user_image = None
        context = {"plant_type": "tomato", "location": "California", "season": "summer"}
        
        state = create_initial_state(session_id, user_message, user_image, context)
        
        # Verify state has required fields
        assert state["session_id"] == session_id, f"State should have correct session_id, got {state['session_id']}"
        assert state["user_message"] == user_message, f"State should have correct user_message, got {state['user_message']}"
        assert state["plant_type"] == "tomato", f"State should have correct plant_type, got {state.get('plant_type')}"
        assert state["location"] == "California", f"State should have correct location, got {state.get('location')}"
        assert state["season"] == "summer", f"State should have correct season, got {state.get('season')}"
        
        logger.info("✅ State creation test passed!")
        logger.info(f"✅ Created state with keys: {list(state.keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ State creation test failed: {str(e)}")
        return False

async def run_all_tests():
    """Run all tests"""
    logger.info("🚀 Starting refactored workflow tests...")
    
    tests = [
        test_workflow_initialization,
        test_node_factory_functionality, 
        test_basic_workflow_structure,
        test_state_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            logger.error(f"❌ Test {test.__name__} threw exception: {str(e)}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info("\n" + "="*60)
    logger.info(f"🧪 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The refactored workflow is working correctly.")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
