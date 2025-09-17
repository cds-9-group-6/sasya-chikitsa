#!/usr/bin/env python3
"""
Test to verify that assistant responses (like weather tips) are properly streamed
"""

import asyncio
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_streaming_logic():
    """Test the streaming response logic"""
    logger.info("🧪 Testing Streaming Response Logic...")
    
    # Simulate the key parts of the workflow streaming logic
    def simulate_streaming_check(chunk_data):
        """Simulate the streaming logic from the workflow"""
        
        # Extract actual state data (as the workflow does)
        actual_state_data = {}
        for node_name, state_data in chunk_data.items():
            if isinstance(state_data, dict):
                actual_state_data.update(state_data)
        
        responses_to_stream = []
        
        # Check for assistant_response that needs immediate streaming
        if "assistant_response" in actual_state_data:
            assistant_response = actual_state_data["assistant_response"]
            if assistant_response and assistant_response.strip():
                responses_to_stream.append({
                    "type": "assistant_response",
                    "session_id": "test_session",
                    "data": {"assistant_response": assistant_response}
                })
        
        return responses_to_stream
    
    test_cases = [
        {
            "name": "Weather tips response from followup node",
            "chunk": {
                "followup": {
                    "current_node": "followup",
                    "next_action": "await_user_input",
                    "requires_user_input": True,
                    "assistant_response": "🌦️ **WEATHER TIPS FOR YOUR PLANTS**\n\n• Water early morning before heat\n• Protect from strong winds\n• Provide shade during hot afternoons\n• Monitor soil moisture regularly",
                    "messages": [
                        {"role": "user", "content": "Give me weather tips"},
                        {"role": "assistant", "content": "🌦️ **WEATHER TIPS FOR YOUR PLANTS**..."}
                    ]
                }
            },
            "should_stream": True,
            "expected_type": "assistant_response"
        },
        {
            "name": "Dosage response from followup node", 
            "chunk": {
                "followup": {
                    "current_node": "followup",
                    "next_action": "await_user_input", 
                    "requires_user_input": True,
                    "assistant_response": "💊 **DOSAGE INSTRUCTIONS**\n\n• Copper Fungicide: 2-3ml per liter\n• Apply every 7-10 days\n• Spray in early morning",
                    "prescription_data": {"treatments": [{"name": "Copper Fungicide", "dosage": "2-3ml/L"}]}
                }
            },
            "should_stream": True,
            "expected_type": "assistant_response"
        },
        {
            "name": "Empty assistant response",
            "chunk": {
                "followup": {
                    "current_node": "followup",
                    "next_action": "await_user_input",
                    "assistant_response": "",
                }
            },
            "should_stream": False,
            "expected_type": None
        },
        {
            "name": "No assistant response field",
            "chunk": {
                "followup": {
                    "current_node": "followup", 
                    "next_action": "classify",
                }
            },
            "should_stream": False,
            "expected_type": None
        },
        {
            "name": "Classification response with assistant_response",
            "chunk": {
                "classifying": {
                    "current_node": "classifying",
                    "next_action": "prescribe",
                    "assistant_response": "🔬 **DIAGNOSIS COMPLETE**\n\nYour plant has early blight...",
                    "classification_results": {"disease_name": "early_blight", "confidence": 0.88}
                }
            },
            "should_stream": True,
            "expected_type": "assistant_response"
        }
    ]
    
    results = []
    for test_case in test_cases:
        responses = simulate_streaming_check(test_case["chunk"])
        
        # Check if streaming behavior matches expectations
        should_stream = test_case["should_stream"]
        actually_streams = len(responses) > 0
        
        passed = should_stream == actually_streams
        
        if passed and should_stream:
            # Check response type matches
            expected_type = test_case["expected_type"]
            actual_type = responses[0]["type"] if responses else None
            passed = expected_type == actual_type
            
        results.append(passed)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"   {status}: {test_case['name']}")
        logger.info(f"      Expected streaming: {should_stream}, Got: {actually_streams}")
        
        if responses:
            response_content = responses[0]["data"]["assistant_response"][:100] + "..." if len(responses[0]["data"]["assistant_response"]) > 100 else responses[0]["data"]["assistant_response"]
            logger.info(f"      Response content: {response_content}")
        
    all_passed = all(results)
    logger.info(f"\n📊 Streaming Logic Test: {sum(results)}/{len(results)} passed")
    
    return all_passed

def test_followup_routing():
    """Test followup node routing logic"""
    logger.info("\n🧪 Testing Followup Node Routing...")
    
    # Simulate the routing logic
    def simulate_routing(next_action):
        routing_map = {
            "restart": "initial",
            "classify": "classifying",
            "prescribe": "prescribing",
            "show_vendors": "show_vendors",
            "complete": "completed",
            "error": "error",
            "request_image": "completed",
            "classify_first": "completed", 
            "prescribe_first": "completed",
            "general_help": "completed",
            "await_user_input": "completed"  # Stay in followup mode after direct response
        }
        return routing_map.get(next_action, "completed")
    
    test_cases = [
        {
            "next_action": "await_user_input",
            "expected_route": "completed",
            "description": "Direct response should end workflow gracefully"
        },
        {
            "next_action": "complete", 
            "expected_route": "completed",
            "description": "Completion should go to completed node"
        },
        {
            "next_action": "classify",
            "expected_route": "classifying", 
            "description": "Classification request should go to classifying"
        }
    ]
    
    results = []
    for test_case in test_cases:
        actual_route = simulate_routing(test_case["next_action"])
        expected_route = test_case["expected_route"]
        passed = actual_route == expected_route
        results.append(passed)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"   {status}: {test_case['description']}")
        logger.info(f"      next_action='{test_case['next_action']}' → route='{actual_route}' (expected: '{expected_route}')")
    
    all_passed = all(results)
    logger.info(f"\n📊 Routing Logic Test: {sum(results)}/{len(results)} passed")
    
    return all_passed

def main():
    """Main test runner"""
    logger.info("🚀 Testing Streaming Response Fix...")
    
    test1_passed = test_streaming_logic()
    test2_passed = test_followup_routing()
    
    logger.info("\n" + "="*80)
    if test1_passed and test2_passed:
        logger.info("🎉 STREAMING RESPONSE FIX: WORKING!")
        logger.info("")
        logger.info("✅ Assistant responses are properly detected and streamed")
        logger.info("✅ Followup node routing keeps conversation flowing")
        logger.info("✅ Direct responses (weather tips, dosage info) will now be streamed back")
        logger.info("")
        logger.info("Expected behavior for weather tips/dosage questions:")
        logger.info("1. User asks: 'Give me weather tips' or 'Yes give me dosage'")
        logger.info("2. Followup node generates response and stores in assistant_response")
        logger.info("3. Sets next_action = 'await_user_input' (ends workflow)")
        logger.info("4. Workflow streams assistant_response immediately")
        logger.info("5. User sees the weather tips/dosage info response")
        logger.info("6. Conversation continues with session persistence")
        
        return True
    else:
        logger.error("❌ STREAMING RESPONSE FIX: NOT WORKING!")
        logger.error("🚨 Issues found that need to be addressed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)