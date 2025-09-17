#!/usr/bin/env python3
"""
Simple test to verify the refactored workflow structure
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all refactored components can be imported"""
    logger.info("🧪 Testing imports...")
    
    try:
        # Test node imports
        from core.nodes import (
            BaseNode, InitialNode, ClassifyingNode, PrescribingNode,
            VendorQueryNode, ShowVendorsNode, OrderBookingNode,
            FollowupNode, CompletedNode, ErrorNode, NodeFactory
        )
        logger.info("✅ All node classes imported successfully")
        
        # Test that nodes have expected methods
        assert hasattr(BaseNode, 'execute'), "BaseNode should have execute method"
        assert hasattr(NodeFactory, 'get_node'), "NodeFactory should have get_node method"
        
        logger.info("✅ Node classes have expected methods")
        
        # Test workflow state import
        from core.workflow_state import create_initial_state, WorkflowState
        logger.info("✅ Workflow state imports successful")
        
        # Test workflow import  
        from core.langgraph_workflow import DynamicPlanningWorkflow
        logger.info("✅ Main workflow class imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import test failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Import test failed with exception: {str(e)}")
        return False

def test_node_factory_creation():
    """Test that node factory can be created"""
    logger.info("🧪 Testing node factory creation...")
    
    try:
        from core.nodes import NodeFactory
        
        # Mock tools and LLM
        mock_tools = {"test_tool": "mock"}
        mock_llm = "mock_llm"
        
        # Create node factory
        factory = NodeFactory(mock_tools, mock_llm)
        
        # Check that it has expected methods
        assert hasattr(factory, 'get_node'), "Factory should have get_node method"
        assert hasattr(factory, 'list_node_names'), "Factory should have list_node_names method"
        
        # Check that it created nodes
        node_names = factory.list_node_names()
        expected_nodes = ["initial", "classifying", "prescribing", "vendor_query", 
                         "show_vendors", "order_booking", "followup", "completed", "error"]
        
        for expected in expected_nodes:
            assert expected in node_names, f"Expected node {expected} not in {node_names}"
        
        logger.info(f"✅ Node factory created {len(node_names)} nodes successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Node factory creation test failed: {str(e)}")
        return False

def test_workflow_state_creation():
    """Test that workflow state can be created"""
    logger.info("🧪 Testing workflow state creation...")
    
    try:
        from core.workflow_state import create_initial_state
        
        # Create test state
        state = create_initial_state("test_session", "test message", None, {"test": "context"})
        
        # Verify state structure
        assert isinstance(state, dict), "State should be a dictionary"
        assert "session_id" in state, "State should have session_id"
        assert "user_message" in state, "State should have user_message"
        assert "current_node" in state, "State should have current_node"
        
        logger.info("✅ Workflow state created successfully")
        logger.info(f"✅ State has {len(state)} fields")
        return True
        
    except Exception as e:
        logger.error(f"❌ Workflow state creation test failed: {str(e)}")
        return False

def run_simple_tests():
    """Run simple structure tests"""
    logger.info("🚀 Running simple refactoring tests...")
    
    tests = [
        test_imports,
        test_node_factory_creation,
        test_workflow_state_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            logger.error(f"❌ Test {test.__name__} threw exception: {str(e)}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info("\n" + "="*60)
    logger.info(f"🧪 SIMPLE TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All simple tests passed! The refactored structure is working.")
        logger.info("🎯 The langgraph_workflow refactoring has been completed successfully!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)
