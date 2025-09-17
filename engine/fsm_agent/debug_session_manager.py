#!/usr/bin/env python3
"""
Debug script to investigate session manager functionality
"""

import asyncio
import sys
import os
import logging
import json
import tempfile

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_session_loading():
    """Debug session loading issue step by step"""
    logger.info("🔍 Starting session loading debug...")
    
    try:
        from core.session_manager import SessionManager
        from core.workflow_state import create_initial_state
        
        # Create temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        logger.info(f"📁 Using temp storage: {temp_dir}")
        
        session_manager = SessionManager(storage_dir=temp_dir)
        test_session_id = "debug_session_123"
        
        logger.info("\n🔬 STEP 1: Create and save initial state")
        logger.info("-" * 50)
        
        # Create initial state with image and results
        initial_state = session_manager.get_or_create_state(
            session_id=test_session_id,
            user_message="Analyze my plant",
            user_image="base64_fake_image_data",
            context={"plant_type": "tomato"}
        )
        
        # Add some results to simulate completed workflow
        initial_state.update({
            "classification_results": {
                "disease_name": "early_blight",
                "confidence": 0.87,
                "severity": "moderate"
            },
            "disease_name": "early_blight", 
            "confidence": 0.87,
            "current_node": "classifying"
        })
        
        # Save the state
        session_manager.save_state(initial_state)
        logger.info(f"💾 Saved initial state with results")
        logger.info(f"   - Disease: {initial_state.get('disease_name')}")
        logger.info(f"   - Confidence: {initial_state.get('confidence')}")
        logger.info(f"   - Has Image: {bool(initial_state.get('user_image'))}")
        logger.info(f"   - Current Node: {initial_state.get('current_node')}")
        
        logger.info("\n🔬 STEP 2: Load state for followup message")
        logger.info("-" * 50)
        
        # Try to load the state for a followup message
        followup_state = session_manager.get_or_create_state(
            session_id=test_session_id,
            user_message="Yes give me dosage"
        )
        
        # Analyze what we got back
        has_previous_image = bool(followup_state.get("user_image"))
        has_classification = bool(followup_state.get("classification_results"))
        has_disease_name = bool(followup_state.get("disease_name"))
        message_count = len(followup_state.get("messages", []))
        current_node = followup_state.get("current_node", "unknown")
        
        logger.info(f"📊 Loaded state analysis:")
        logger.info(f"   - Has Previous Image: {has_previous_image}")
        logger.info(f"   - Has Classification Results: {has_classification}")
        logger.info(f"   - Has Disease Name: {has_disease_name}")
        logger.info(f"   - Current Node: {current_node}")
        logger.info(f"   - Message History Length: {message_count}")
        
        if has_classification:
            disease = followup_state["classification_results"]["disease_name"]
            confidence = followup_state["classification_results"]["confidence"]
            logger.info(f"   - Previous Disease: {disease}")
            logger.info(f"   - Previous Confidence: {confidence}")
        
        logger.info("\n🔬 STEP 3: Verify session continuation vs new session")
        logger.info("-" * 50)
        
        # Test with different session ID to confirm isolation
        different_session = session_manager.get_or_create_state(
            session_id="different_session_456",
            user_message="Hello"
        )
        
        different_has_results = bool(different_session.get("classification_results"))
        logger.info(f"📊 Different session verification:")
        logger.info(f"   - Different session has results: {different_has_results}")
        
        # Final assessment
        logger.info("\n🎯 ASSESSMENT:")
        logger.info("-" * 50)
        
        if has_classification and has_disease_name and not different_has_results:
            logger.info("✅ SUCCESS: Session is continuing properly!")
            logger.info(f"   - Has Previous Image: {has_previous_image}")
            logger.info(f"   - Has Classification Results: {has_classification}")  
            logger.info(f"   - Previous Disease: {followup_state['classification_results']['disease_name']}")
            logger.info(f"   - Current Node: {current_node}")
            logger.info(f"   - Message History Length: {message_count}")
            return True
        else:
            logger.error("❌ FAILURE: Session continuation not working properly")
            logger.error(f"   - Expected classification results: True, Got: {has_classification}")
            logger.error(f"   - Expected disease name: True, Got: {has_disease_name}")
            logger.error(f"   - Different session isolated: {not different_has_results}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Debug failed: {str(e)}", exc_info=True)
        return False

async def main():
    """Main debug runner"""
    logger.info("🚀 Starting Session Manager Debug...")
    
    success = await debug_session_loading()
    
    logger.info("\n" + "="*80)
    if success:
        logger.info("🎉 SESSION MANAGER DEBUG: SUCCESS!")
        logger.info("")
        logger.info("✅ Session loading is working correctly")
        logger.info("✅ Previous results are preserved")
        logger.info("✅ Followup messages can access previous data")
        logger.info("✅ Different sessions are properly isolated")
    else:
        logger.error("❌ SESSION MANAGER DEBUG: ISSUES FOUND!")
        logger.error("🚨 Session loading needs investigation!")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
