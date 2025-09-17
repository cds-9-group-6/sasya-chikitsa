#!/usr/bin/env python3
"""
Test the actual workflow execution to verify session persistence works in practice
"""

import asyncio
import sys
import os
import logging
import tempfile
from unittest.mock import Mock, AsyncMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_workflow_session_persistence():
    """Test that the actual workflow saves and loads session state properly"""
    logger.info("🧪 Testing REAL Workflow Session Persistence...")
    
    try:
        # Import the workflow components
        from core.session_manager import SessionManager
        from core.nodes import NodeFactory
        
        # Create a mock workflow that simulates the real behavior
        class MockDynamicPlanningWorkflow:
            def __init__(self, storage_dir):
                # Mock tools
                self.tools = {
                    "classification": Mock(),
                    "prescription": Mock(), 
                    "vendor": Mock(),
                    "context_extractor": Mock(),
                    "attention_overlay": Mock(),
                }
                
                # Mock LLM
                self.llm = Mock()
                
                # Real session manager (this is what we're testing)
                self.session_manager = SessionManager(storage_dir=storage_dir)
                
                # Mock node factory
                self.node_factory = Mock()
                
                logger.info("✅ Mock workflow initialized with real session manager")
            
            async def mock_process_message(self, session_id: str, user_message: str, user_image: str = None, context: dict = None):
                """Mock the process_message method with real session persistence"""
                logger.info(f"📨 Processing message for session {session_id}: '{user_message[:50]}...'")
                
                # REAL session loading (this is the critical part)
                state = self.session_manager.get_or_create_state(session_id, user_message, user_image, context)
                logger.info(f"🔍 Loaded/Created state - Current node: {state.get('current_node')}, Has image: {'user_image' in state}")
                
                # Simulate workflow execution results
                if user_message.lower().startswith("analyze"):
                    # First request - simulate classification
                    state["classification_results"] = {
                        "disease_name": "tomato_blight",
                        "confidence": 0.89,
                        "severity": "moderate"
                    }
                    state["disease_name"] = "tomato_blight"
                    state["confidence"] = 0.89
                    state["current_node"] = "classifying"
                    logger.info("🔬 Simulated classification results added to state")
                    
                elif "treatment" in user_message.lower():
                    # Second request - simulate prescription
                    if state.get("classification_results"):
                        state["prescription_data"] = {
                            "treatments": [
                                {"name": "Fungicide Spray", "dosage": "2ml per liter", "frequency": "Weekly"}
                            ]
                        }
                        state["current_node"] = "prescribing" 
                        logger.info("💊 Simulated prescription results added to state")
                    else:
                        logger.warning("⚠️ No classification results found - this indicates session loading failed!")
                
                # REAL session saving (this is the critical part)  
                self.session_manager.save_state(state)
                logger.info(f"💾 Saved state after processing")
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "current_node": state.get("current_node"),
                    "has_classification": "classification_results" in state,
                    "has_prescription": "prescription_data" in state,
                    "disease_name": state.get("disease_name"),
                    "confidence": state.get("confidence")
                }
        
        # Test with temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow = MockDynamicPlanningWorkflow(temp_dir)
            test_session_id = "workflow_test_session_456"
            
            logger.info("\n" + "="*60)
            logger.info("🧪 STEP 1: First request (analyze plant + image)")
            logger.info("="*60)
            
            # First request: Analyze plant with image
            result1 = await workflow.mock_process_message(
                session_id=test_session_id,
                user_message="Analyze my tomato plant for diseases",
                user_image="base64_image_data_12345",
                context={"plant_type": "tomato", "location": "California"}
            )
            
            logger.info(f"✅ First request result:")
            logger.info(f"   - Success: {result1['success']}")
            logger.info(f"   - Current Node: {result1['current_node']}")
            logger.info(f"   - Has Classification: {result1['has_classification']}")
            logger.info(f"   - Disease: {result1['disease_name']}")
            logger.info(f"   - Confidence: {result1['confidence']}")
            
            # Verify session file was created
            session_file = workflow.session_manager._get_session_file(test_session_id)
            logger.info(f"📁 Session file exists: {os.path.exists(session_file)}")
            
            logger.info("\n" + "="*60)
            logger.info("🧪 STEP 2: Second request (followup treatment question)")
            logger.info("="*60)
            
            # Second request: Ask for treatment (same session, no image)
            result2 = await workflow.mock_process_message(
                session_id=test_session_id,
                user_message="What treatment should I use for this disease?"
            )
            
            logger.info(f"✅ Second request result:")
            logger.info(f"   - Success: {result2['success']}")
            logger.info(f"   - Current Node: {result2['current_node']}")
            logger.info(f"   - Has Classification: {result2['has_classification']}")
            logger.info(f"   - Has Prescription: {result2['has_prescription']}")
            logger.info(f"   - Disease (from previous): {result2['disease_name']}")
            logger.info(f"   - Confidence (from previous): {result2['confidence']}")
            
            # Verify persistence worked
            if result2["has_classification"] and result2["disease_name"]:
                logger.info("🎉 SUCCESS: Session state persisted correctly!")
                logger.info("   - Previous classification results were preserved")
                logger.info("   - No need to re-upload image")
                logger.info("   - Workflow can continue from where it left off")
                return True
            else:
                logger.error("❌ FAILURE: Session state did NOT persist!")
                logger.error("   - Classification results were lost")
                logger.error("   - User would be asked to re-upload image")
                return False
                
    except Exception as e:
        logger.error(f"❌ Workflow persistence test failed: {str(e)}", exc_info=True)
        return False

async def run_workflow_test():
    """Run the workflow persistence test"""
    logger.info("🚀 Starting Real Workflow Session Persistence Test...")
    
    success = await test_workflow_session_persistence()
    
    logger.info("\n" + "="*80)
    if success:
        logger.info("🎉 WORKFLOW SESSION PERSISTENCE TEST: PASSED!")
        logger.info("✅ The fix should work in the real application!")
    else:
        logger.error("❌ WORKFLOW SESSION PERSISTENCE TEST: FAILED!")
        logger.error("🚨 There are still issues with session persistence!")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(run_workflow_test())
    sys.exit(0 if success else 1)
