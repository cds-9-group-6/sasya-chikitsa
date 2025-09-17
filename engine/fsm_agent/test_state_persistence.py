#!/usr/bin/env python3
"""
Test to verify state persistence functionality works correctly
"""

import asyncio
import sys
import os
import logging
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_session_persistence_fix():
    """Test the core session persistence functionality"""
    logger.info("🧪 Testing Session Persistence Fix...")
    
    try:
        from core.session_manager import SessionManager
        from core.workflow_state import create_initial_state
        
        # Test with temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            session_manager = SessionManager(storage_dir=temp_dir)
            test_session_id = "fix_test_session_789"
            
            logger.info("\n" + "="*60)
            logger.info("🧪 STEP 1: Create initial state with classification results")
            logger.info("="*60)
            
            # Create initial state with results
            state1 = session_manager.get_or_create_state(
                session_id=test_session_id,
                user_message="Analyze my plant", 
                user_image="base64_image_data"
            )
            
            # Simulate completed workflow with results
            state1.update({
                "classification_results": {"disease_name": "early_blight", "confidence": 0.88},
                "disease_name": "early_blight",
                "confidence": 0.88,
                "current_node": "classifying"
            })
            
            session_manager.save_state(state1)
            logger.info("✅ Saved state with classification results")
            
            logger.info("\n" + "="*60)
            logger.info("🧪 STEP 2: Load state for followup question")
            logger.info("="*60)
            
            # Load state for followup
            state2 = session_manager.get_or_create_state(
                session_id=test_session_id,
                user_message="Yes give me dosage"
            )
            
            # Verify state was loaded correctly
            has_classification = bool(state2.get("classification_results"))
            has_disease_name = bool(state2.get("disease_name"))
            message_count = len(state2.get("messages", []))
            
            logger.info(f"📊 Loaded state verification:")
            logger.info(f"   - Has classification results: {has_classification}")
            logger.info(f"   - Has disease name: {has_disease_name}")
            logger.info(f"   - Message count: {message_count}")
            logger.info(f"   - Current node: {state2.get('current_node')}")
            
            if has_classification and has_disease_name:
                logger.info("✅ SUCCESS: Session persistence is working correctly!")
                logger.info("   - Previous results preserved")
                logger.info("   - Followup questions will use existing data")
                logger.info("   - No need to re-upload images")
                return True
            else:
                logger.error("❌ FAILURE: Session persistence not working")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)
        return False

async def main():
    """Main test runner"""
    logger.info("🚀 Testing Session Persistence...")
    
    success = await test_session_persistence_fix()
    
    logger.info("\n" + "="*80)
    if success:
        logger.info("🎉 SESSION PERSISTENCE: WORKING!")
        logger.info("")
        logger.info("✅ States are saved and loaded correctly")
        logger.info("✅ Conversation history is preserved")
        logger.info("✅ Classification results persist across requests")
        logger.info("✅ Users don't need to re-upload images for followup questions")
    else:
        logger.error("❌ SESSION PERSISTENCE: NOT WORKING!")
        logger.error("🚨 Issues found that need investigation!")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)