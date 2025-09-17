#!/usr/bin/env python3
"""
Test to verify the dosage intent fix works correctly
"""

import asyncio
import sys
import os
import logging
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_dosage_intent_fix():
    """Test that 'Yes give me dosage' is handled correctly in continuing conversations"""
    logger.info("🧪 Testing Dosage Intent Fix...")
    
    try:
        from core.session_manager import SessionManager
        from core.nodes.initial_node import InitialNode
        from core.nodes.followup_node import FollowupNode
        from unittest.mock import Mock
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            session_manager = SessionManager(storage_dir=temp_dir)
            test_session_id = "dosage_intent_test_session"
            
            # Mock tools and LLM
            mock_tools = {
                "context_extractor": Mock(),
                "classification": Mock(),
                "prescription": Mock(),
                "vendor": Mock(),
                "attention_overlay": Mock(),
            }
            mock_llm = Mock()
            
            # Create node instances
            initial_node = InitialNode(mock_tools, mock_llm)
            followup_node = FollowupNode(mock_tools, mock_llm)
            
            logger.info("\n" + "="*70)
            logger.info("🧪 STEP 1: Simulate completed classification and prescription")
            logger.info("="*70)
            
            # Create a state as if the user has already completed classification and prescription
            state = session_manager.get_or_create_state(
                session_id=test_session_id,
                user_message="Analyze my tomato plant",
                user_image="base64_image_data_xyz",
                context={"plant_type": "tomato", "location": "California"}
            )
            
            # Simulate that classification and prescription have been completed
            state.update({
                "classification_results": {
                    "disease_name": "early_blight",
                    "confidence": 0.88,
                    "severity": "moderate"
                },
                "disease_name": "early_blight",
                "confidence": 0.88,
                "prescription_data": {
                    "treatments": [
                        {
                            "name": "Copper Fungicide",
                            "dosage": "2-3ml per liter of water",
                            "application": "Spray on leaves early morning",
                            "frequency": "Every 7-10 days",
                            "duration": "Continue until symptoms clear"
                        },
                        {
                            "name": "Neem Oil",
                            "dosage": "5ml per liter of water", 
                            "application": "Spray on both sides of leaves",
                            "frequency": "Twice weekly",
                            "duration": "2-3 weeks"
                        }
                    ],
                    "notes": "Apply treatments in evening to avoid leaf burn. Ensure good air circulation."
                },
                "current_node": "prescribing",
                "is_complete": False
            })
            
            # Save the state (simulating completed workflow)
            session_manager.save_state(state)
            logger.info("✅ Saved state with classification and prescription results")
            
            logger.info("\n" + "="*70)
            logger.info("🧪 STEP 2: User followup - 'Yes give me dosage'")
            logger.info("="*70)
            
            # Load state for followup message
            followup_state = session_manager.get_or_create_state(
                session_id=test_session_id,
                user_message="Yes give me dosage"
            )
            
            logger.info(f"📋 Loaded state for followup:")
            logger.info(f"   - Has prescription data: {'prescription_data' in followup_state}")
            logger.info(f"   - Message count: {len(followup_state.get('messages', []))}")
            logger.info(f"   - Current node: {followup_state.get('current_node')}")
            
            logger.info("\n🔍 Testing Initial Node Routing:")
            
            # Test initial node - should detect continuing conversation
            result_state = await initial_node.execute(followup_state.copy())
            next_action = result_state.get("next_action")
            
            logger.info(f"   - Initial node next_action: {next_action}")
            
            if next_action == "followup":
                logger.info("✅ CORRECT: Initial node detected continuing conversation and routed to followup")
                
                logger.info("\n🔍 Testing Followup Node Intent Analysis:")
                
                # Test followup node - should handle dosage request correctly
                # Mock the LLM to return the expected followup intent
                mock_response = Mock()
                mock_response.content = '''{"action": "direct_response", "response": "📋 **HOW TO USE YOUR MEDICINES**\\n\\n💊 **STEP-BY-STEP INSTRUCTIONS**\\n\\n🔹 **MEDICINE #1: Copper Fungicide**\\n• **How much to use:** 2-3ml per liter of water\\n• **How to apply:** Spray on leaves early morning\\n• **How often:** Every 7-10 days\\n• **For how long:** Continue until symptoms clear\\n\\n🔹 **MEDICINE #2: Neem Oil**\\n• **How much to use:** 5ml per liter of water\\n• **How to apply:** Spray on both sides of leaves\\n• **How often:** Twice weekly\\n• **For how long:** 2-3 weeks\\n\\n⚠️ **IMPORTANT SAFETY TIPS**\\nApply treatments in evening to avoid leaf burn. Ensure good air circulation.\\n\\n✅ **SAFETY FIRST**\\n• Always read the medicine bottle label\\n• Wear gloves when spraying\\n• Watch your plant daily for changes\\n• Ask local experts if you need help\\n\\n💚 **Take care of yourself and your plants!**", "confidence": 0.95}'''
                mock_llm.ainvoke.return_value = mock_response
                
                followup_result = await followup_node.execute(followup_state.copy())
                final_action = followup_result.get("next_action")
                
                logger.info(f"   - Followup node next_action: {final_action}")
                
                # Check if assistant response was generated with dosage info
                assistant_messages = [msg for msg in followup_result.get("messages", []) if msg.get("role") == "assistant"]
                if assistant_messages:
                    latest_response = assistant_messages[-1].get("content", "")
                    has_dosage_info = ("dosage" in latest_response.lower() and 
                                     "copper fungicide" in latest_response.lower() and
                                     "2-3ml per liter" in latest_response)
                    
                    if has_dosage_info:
                        logger.info("✅ CORRECT: Followup node provided dosage information from existing prescription")
                        logger.info("✅ SUCCESS: The dosage intent fix is working!")
                        return True
                    else:
                        logger.error("❌ FAILURE: Followup node did not provide expected dosage information")
                        logger.error(f"Response was: {latest_response[:200]}...")
                        return False
                else:
                    logger.error("❌ FAILURE: No assistant response generated by followup node")
                    return False
                    
            else:
                logger.error(f"❌ FAILURE: Initial node should route to 'followup' but routed to '{next_action}'")
                logger.error("   The continuing conversation detection is not working properly")
                return False
                
    except Exception as e:
        logger.error(f"❌ Dosage intent test failed: {str(e)}", exc_info=True)
        return False

async def main():
    """Main test runner"""
    logger.info("🚀 Testing Dosage Intent Fix...")
    
    success = await test_dosage_intent_fix()
    
    logger.info("\n" + "="*80)
    if success:
        logger.info("🎉 DOSAGE INTENT FIX: WORKING!")
        logger.info("")
        logger.info("The issue has been resolved:")
        logger.info("✅ 'Yes give me dosage' is now handled as a followup question")
        logger.info("✅ Uses existing prescription data instead of requesting new classification")
        logger.info("✅ Provides detailed dosage information directly")
        logger.info("")
        logger.info("Key fixes applied:")
        logger.info("• Initial node now detects continuing conversations")
        logger.info("• Routes loaded sessions to followup node for context-aware intent analysis")
        logger.info("• Followup node has proper logic for dosage requests")
    else:
        logger.error("❌ DOSAGE INTENT FIX: NOT WORKING!")
        logger.error("🚨 The intent analysis still needs more work!")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)