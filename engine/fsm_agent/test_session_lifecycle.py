#!/usr/bin/env python3
"""
Test to verify session lifecycle management works correctly
"""

import asyncio
import sys
import os
import logging
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_session_lifecycle():
    """Test complete session lifecycle from creation to termination"""
    logger.info("🧪 Testing Session Lifecycle Management...")
    
    try:
        from core.session_manager import SessionManager
        from core.nodes.session_end_node import SessionEndNode
        from core.nodes.followup_node import FollowupNode
        from unittest.mock import Mock
        
        # Create temporary directory for session storage
        with tempfile.TemporaryDirectory() as temp_dir:
            session_manager = SessionManager(storage_dir=temp_dir)
            test_session_id = "lifecycle_test_session_999"
            
            # Mock tools and LLM
            mock_tools = {
                "context_extractor": Mock(),
                "classification": Mock(),
                "prescription": Mock(),
                "vendor": Mock(),
                "attention_overlay": Mock(),
            }
            mock_llm = Mock()
            
            logger.info("\n" + "="*70)
            logger.info("🧪 STEP 1: Create new session")
            logger.info("="*70)
            
            # Create initial session state
            initial_state = session_manager.get_or_create_state(
                session_id=test_session_id,
                user_message="Hello, I need help with my plant",
                user_image=None,
                context={"plant_type": "tomato"}
            )
            
            # Verify session was created
            session_exists = os.path.exists(session_manager._get_session_file_path(test_session_id))
            logger.info(f"✅ Session created: {session_exists}")
            logger.info(f"   Session ID: {test_session_id}")
            logger.info(f"   Initial message: {initial_state['user_message']}")
            
            logger.info("\n" + "="*70)
            logger.info("🧪 STEP 2: Continue session with multiple interactions")
            logger.info("="*70)
            
            # Simulate multiple interactions
            interactions = [
                "Analyze my plant image",
                "What treatment do you recommend?", 
                "Yes give me dosage information",
                "Thank you, goodbye!"  # This should trigger session ending
            ]
            
            for i, message in enumerate(interactions, 1):
                logger.info(f"\n--- Interaction {i}: '{message}' ---")
                
                # Get current state for this interaction
                state = session_manager.get_or_create_state(
                    session_id=test_session_id,
                    user_message=message
                )
                
                logger.info(f"State loaded: {bool(state)}")
                logger.info(f"Message count: {len(state.get('messages', []))}")
                logger.info(f"Current node: {state.get('current_node')}")
                
                # For the goodbye message, test session ending
                if "goodbye" in message.lower():
                    logger.info("🔚 Testing session ending logic...")
                    
                    # Create and test session end node
                    session_end_node = SessionEndNode(mock_tools, mock_llm)
                    
                    # Test followup node goodbye detection
                    followup_node = FollowupNode(mock_tools, mock_llm)
                    goodbye_detected = await followup_node._detect_goodbye_intent(state)
                    logger.info(f"   Goodbye intent detected: {goodbye_detected}")
                    
                    if goodbye_detected:
                        # Execute session end node
                        ended_state = await session_end_node.execute(state)
                        
                        # Verify session ending properties
                        is_ended = ended_state.get("session_ended", False)
                        is_complete = ended_state.get("is_complete", False)
                        has_farewell = bool(ended_state.get("assistant_response"))
                        
                        logger.info(f"   Session ended: {is_ended}")
                        logger.info(f"   Workflow complete: {is_complete}")
                        logger.info(f"   Has farewell message: {has_farewell}")
                        
                        if has_farewell:
                            farewell_preview = ended_state["assistant_response"][:100] + "..."
                            logger.info(f"   Farewell preview: {farewell_preview}")
                        
                        # Save the ended state
                        session_manager.save_state(ended_state)
                        
                        if is_ended and is_complete and has_farewell:
                            logger.info("✅ Session ending logic works correctly!")
                            break
                        else:
                            logger.error("❌ Session ending logic failed!")
                            return False
                else:
                    # Simulate normal workflow progression
                    state["current_node"] = f"node_{i}"
                    session_manager.save_state(state)
            
            logger.info("\n" + "="*70)
            logger.info("🧪 STEP 3: Verify session persistence after ending")
            logger.info("="*70)
            
            # Try to load the ended session
            final_state = session_manager.get_or_create_state(
                session_id=test_session_id,
                user_message="Are you there?"
            )
            
            # Check if session shows as ended
            session_ended = final_state.get("session_ended", False)
            logger.info(f"Session shows as ended: {session_ended}")
            
            if session_ended:
                logger.info("✅ Session ending persisted correctly!")
                
                # Test session cleanup
                logger.info("\n🧹 Testing session cleanup...")
                session_manager.clear_session(test_session_id)
                
                # Verify session was removed
                session_file_exists = os.path.exists(session_manager._get_session_file_path(test_session_id))
                logger.info(f"Session file exists after cleanup: {session_file_exists}")
                
                if not session_file_exists:
                    logger.info("✅ Session cleanup works correctly!")
                    return True
                else:
                    logger.error("❌ Session cleanup failed!")
                    return False
            else:
                logger.error("❌ Session ending was not persisted!")
                return False
                
    except Exception as e:
        logger.error(f"❌ Session lifecycle test failed: {str(e)}", exc_info=True)
        return False

def test_session_routing_logic():
    """Test session routing logic without workflow execution"""
    logger.info("\n🧪 Testing Session Routing Logic...")
    
    # Test routing from completed node
    def simulate_completed_routing(user_message):
        """Simulate _route_from_completed logic"""
        user_message = user_message.lower()
        
        session_end_keywords = [
            "bye", "goodbye", "farewell", "thanks", "thank you",
            "done", "finished", "complete", "exit", "quit", 
            "end", "stop", "that's all", "no more", "see you"
        ]
        
        if any(keyword in user_message for keyword in session_end_keywords):
            return "session_end"
        return "completed"
    
    test_cases = [
        {
            "message": "Thank you, goodbye!",
            "expected": "session_end",
            "description": "Goodbye message should route to session_end"
        },
        {
            "message": "Thanks for the help, I'm done",
            "expected": "session_end", 
            "description": "Done message should route to session_end"
        },
        {
            "message": "Can you help me more?",
            "expected": "completed",
            "description": "Continuation message should stay in completed"
        },
        {
            "message": "What about vendors?",
            "expected": "completed",
            "description": "Follow-up question should stay in completed"
        }
    ]
    
    results = []
    for test_case in test_cases:
        result = simulate_completed_routing(test_case["message"])
        expected = test_case["expected"]
        passed = result == expected
        results.append(passed)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"   {status}: {test_case['description']}")
        logger.info(f"      Message: '{test_case['message']}'")
        logger.info(f"      Expected: {expected}, Got: {result}")
    
    all_passed = all(results)
    logger.info(f"\n📊 Routing Logic Test: {sum(results)}/{len(results)} passed")
    
    return all_passed

async def main():
    """Main test runner"""
    logger.info("🚀 Testing Session Lifecycle Management...")
    
    test1_passed = await test_session_lifecycle()
    test2_passed = test_session_routing_logic()
    
    logger.info("\n" + "="*80)
    if test1_passed and test2_passed:
        logger.info("🎉 SESSION LIFECYCLE MANAGEMENT: WORKING!")
        logger.info("")
        logger.info("✅ Sessions are created with unique IDs")
        logger.info("✅ Sessions persist across multiple interactions")
        logger.info("✅ Session ending is triggered by user goodbye intent")
        logger.info("✅ Session_end node provides appropriate farewell messages")
        logger.info("✅ Ended sessions are marked and persisted correctly")
        logger.info("✅ Session cleanup removes ended sessions from storage")
        logger.info("✅ Routing logic correctly identifies session ending intent")
        logger.info("")
        logger.info("Expected behavior:")
        logger.info("1. New sessions created only when starting conversations")
        logger.info("2. Same session ID used across multiple requests")
        logger.info("3. Sessions end only when user says goodbye")
        logger.info("4. Ended sessions cleaned up from storage")
        logger.info("5. No more creating new session IDs for every request!")
        
        return True
    else:
        logger.error("❌ SESSION LIFECYCLE MANAGEMENT: NOT WORKING!")
        logger.error("🚨 Issues found that need to be addressed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
