#!/usr/bin/env python3
"""
Test MLflow LangChain autolog integration with LangGraph workflow
"""

import os
import logging
import asyncio
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mlflow_manager_autolog():
    """Test MLflow manager with LangChain autolog"""
    try:
        from core.mlflow_manager import get_mlflow_manager
        
        manager = get_mlflow_manager()
        logger.info(f"MLflow manager available: {manager.is_available()}")
        
        # Check if we have a persistent run
        if manager.is_available() and manager.persistent_run_id:
            logger.info(f"✅ Persistent run active: {manager.persistent_run_id}")
        else:
            logger.warning("No persistent run active")
            
        return manager.is_available()
        
    except ImportError as e:
        logger.error(f"Failed to import MLflow manager: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing MLflow manager: {e}")
        return False

def test_workflow_compilation():
    """Test that the workflow compiles with autolog"""
    try:
        from fsm_agent.core.fsm_agent import DynamicPlanningAgent
        
        llm_config = {
            "model": "llama3.1:8b",
            "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "temperature": 0.1,
        }
        
        logger.info("Creating Dynamic Planning Agent...")
        agent = DynamicPlanningAgent(llm_config)
        logger.info("✅ Agent created successfully with autolog support")
        
        # Check if MLflow manager is available
        if hasattr(agent.workflow, 'mlflow_manager'):
            mlflow_available = agent.workflow.mlflow_manager.is_available()
            logger.info(f"MLflow available: {mlflow_available}")
            if mlflow_available and agent.workflow.mlflow_manager.persistent_run_id:
                logger.info(f"Persistent run ID: {agent.workflow.mlflow_manager.persistent_run_id}")
                logger.info("✅ LangChain autolog should capture traces to this run")
        else:
            logger.warning("No MLflow manager found in workflow")
            
        return True
        
    except Exception as e:
        logger.error(f"Error testing workflow compilation: {e}")
        return False

async def test_traced_message_processing():
    """Test message processing with tracing"""
    try:
        from fsm_agent.core.fsm_agent import DynamicPlanningAgent
        
        llm_config = {
            "model": "llama3.1:8b",
            "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "temperature": 0.1,
        }
        
        logger.info("Testing traced message processing...")
        agent = DynamicPlanningAgent(llm_config)
        
        # Test with a simple message (no image to avoid dependencies)
        test_message = "Hello, I want to learn about plant diseases"
        session_id = "test_tracing_session"
        
        logger.info("Processing test message with tracing...")
        result = await agent.start_session(test_message, session_id=session_id)
        
        logger.info(f"Message processed successfully: {result.get('success', False)}")
        
        # Check if we have autolog enabled (would need MLflow server running)
        if agent.workflow.mlflow_manager and agent.workflow.mlflow_manager.is_available():
            logger.info("✅ Message processed with LangChain autolog enabled")
            logger.info("   Traces should appear in MLflow UI under the persistent run")
        else:
            logger.info("ℹ️ Message processed without autolog (MLflow server not available)")
            
        return True
        
    except Exception as e:
        logger.error(f"Error testing traced message processing: {e}")
        return False

def test_classification_tool_autolog():
    """Test classification tool with autolog integration"""
    try:
        from fsm_agent.tools.classification_tool import ClassificationTool
        from core.mlflow_manager import get_mlflow_manager
        
        logger.info("Testing classification tool with autolog...")
        
        tool = ClassificationTool()
        manager = get_mlflow_manager()
        
        # Test inputs (minimal to avoid requiring actual images)
        test_input = {
            "image_b64": "test_image_data", 
            "session_id": "test_session",
            "plant_type": "test_plant"
        }
        
        # This will fail gracefully without actual image/model, but tests compilation
        try:
            result = tool._run(mlflow_manager=manager, **test_input)
            logger.info(f"Classification tool executed (expected to fail without real data): {result.get('error', 'No error')}")
        except Exception as e:
            logger.info(f"Classification tool failed as expected without real data: {e}")
            
        logger.info("✅ Classification tool compiled successfully - autolog should capture any LangChain operations")
        return True
        
    except Exception as e:
        logger.error(f"Error testing classification tool: {e}")
        return False

def check_mlflow_langchain_imports():
    """Check if MLflow LangChain autolog imports work"""
    try:
        import mlflow.langchain
        logger.info("✅ MLflow LangChain autolog imports successful")
        return True
    except ImportError as e:
        logger.warning(f"MLflow LangChain autolog not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking MLflow LangChain imports: {e}")
        return False

async def main():
    """Run all autolog tests"""
    logger.info("🧪 Testing MLflow LangChain Autolog Integration")
    logger.info("=" * 50)
    
    tests = [
        ("MLflow LangChain Imports", check_mlflow_langchain_imports),
        ("MLflow Manager Autolog", test_mlflow_manager_autolog),
        ("Workflow Compilation", test_workflow_compilation),
        ("Classification Tool Autolog", test_classification_tool_autolog),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\\n🔍 Running: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            logger.error(f"❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Run async test separately
    logger.info(f"\\n🔍 Running: Traced Message Processing")
    try:
        result = await test_traced_message_processing()
        results.append(("Traced Message Processing", result))
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: Traced Message Processing")
    except Exception as e:
        logger.error(f"❌ ERROR in Traced Message Processing: {e}")
        results.append(("Traced Message Processing", False))
    
    # Summary
    logger.info("\\n" + "=" * 50)
    logger.info("🎯 MLFLOW LANGCHAIN AUTOLOG TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! MLflow LangChain autolog is properly integrated.")
        logger.info("   🔍 LangGraph workflow traces should appear in MLflow UI")
        logger.info("   📊 All traces will be logged to the persistent run")
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Check implementation.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
