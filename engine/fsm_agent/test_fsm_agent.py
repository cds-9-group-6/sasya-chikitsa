#!/usr/bin/env python3
"""
Test script for Dynamic Planning Agent using LangGraph

This script demonstrates the basic functionality of the FSM agent.
"""

import asyncio
import logging
import sys
import os
from typing import Optional

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fsm_agent.core.fsm_agent import DynamicPlanningAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_basic_conversation():
    """Test basic conversation flow"""
    print("🧪 Testing Basic Conversation Flow")
    print("=" * 50)
    
    # Initialize agent
    llm_config = {
        "model": "llama3.1:8b",
        "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"), 
        "temperature": 0.1,
    }
    
    try:
        agent = DynamicPlanningAgent(llm_config)
        print("✅ Agent initialized successfully")
        
        # Start session
        result = await agent.start_session(
            user_message="Hello, I need help with my tomato plant. The leaves are showing yellow spots and I'm located in Tamil Nadu.",
            user_image=None
        )
        
        if result["success"]:
            session_id = result["session_id"]
            print(f"✅ Session started: {session_id}")
            
            # Print initial response
            messages = result["result"]["messages"]
            for msg in messages:
                if msg["role"] == "assistant":
                    print(f"🤖 Agent: {msg['content']}")
            
            # Continue conversation
            follow_up = await agent.process_message(
                session_id,
                "I have uploaded an image of the affected leaves. Can you analyze it?"
            )
            
            if follow_up["success"]:
                messages = follow_up["messages"]
                for msg in messages:
                    if msg["role"] == "assistant":
                        print(f"🤖 Agent: {msg['content']}")
            else:
                print(f"❌ Error in follow-up: {follow_up.get('error')}")
            
            # Get session info
            session_info = await agent.get_session_info(session_id)
            if session_info["success"]:
                print(f"\n📊 Session Info:")
                print(f"   Current State: {session_info.get('current_state')}")
                print(f"   Message Count: {session_info.get('message_count')}")
                print(f"   Has Classification: {session_info.get('has_classification')}")
                print(f"   Has Prescription: {session_info.get('has_prescription')}")
            
            # End session
            end_result = await agent.end_session(session_id)
            if end_result["success"]:
                print(f"✅ Session ended successfully")
            
        else:
            print(f"❌ Failed to start session: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        logger.error(f"Test error: {str(e)}", exc_info=True)


async def test_streaming():
    """Test streaming functionality"""
    print("\n🧪 Testing Streaming Functionality")
    print("=" * 50)
    
    llm_config = {
        "model": "llama3.1:8b", 
        "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "temperature": 0.1,
    }
    
    try:
        agent = DynamicPlanningAgent(llm_config)
        print("✅ Agent initialized for streaming test")
        
        # Start session first
        result = await agent.start_session(
            user_message="I have a plant disease problem and need help with diagnosis.",
            user_image=None
        )
        
        if result["success"]:
            session_id = result["session_id"]
            print(f"✅ Session started for streaming: {session_id}")
            
            # Test streaming
            print("🔄 Starting stream...")
            stream_content = []
            
            async for chunk in agent.stream_message(
                session_id,
                "Can you guide me through the process of plant disease diagnosis?"
            ):
                if chunk.get("type") == "message":
                    content = chunk.get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        stream_content.append(content)
                elif chunk.get("type") == "state_update":
                    print(f"\n[State Update: {chunk.get('data', {})}]")
                elif chunk.get("type") == "error":
                    print(f"\n❌ Stream Error: {chunk.get('error')}")
                    break
            
            print(f"\n✅ Streaming completed. Total content length: {len(''.join(stream_content))}")
            
            # Clean up
            await agent.end_session(session_id)
        else:
            print(f"❌ Failed to start session for streaming: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Streaming test failed: {str(e)}")
        logger.error(f"Streaming test error: {str(e)}", exc_info=True)


async def test_context_extraction():
    """Test context extraction functionality"""
    print("\n🧪 Testing Context Extraction")
    print("=" * 50)
    
    try:
        from fsm_agent.tools.context_extractor import ContextExtractorTool
        
        tool = ContextExtractorTool()
        
        test_messages = [
            "I'm from Tamil Nadu and growing tomatoes in summer season. The leaves are yellowing.",
            "My potato plants in Karnataka are showing brown spots during monsoon.",
            "I have a problem with my chili plants in Bangalore. They are in flowering stage.",
            "Need help with rice crop in West Bengal. The plants are wilting."
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\nTest {i}: {message}")
            result = await tool._arun(user_message=message)
            
            if result.get("error"):
                print(f"❌ Error: {result['error']}")
            else:
                print("✅ Extracted context:")
                for key, value in result.items():
                    if value:
                        print(f"   {key}: {value}")
    
    except Exception as e:
        print(f"❌ Context extraction test failed: {str(e)}")
        logger.error(f"Context extraction test error: {str(e)}", exc_info=True)


async def test_tool_integration():
    """Test individual tool functionality"""
    print("\n🧪 Testing Tool Integration")
    print("=" * 50)
    
    # Test Context Extractor
    try:
        from fsm_agent.tools.context_extractor import run_context_extractor_tool
        
        context_result = await run_context_extractor_tool({
            "user_message": "I'm growing tomatoes in Tamil Nadu during summer and the leaves are showing yellow spots"
        })
        
        if context_result.get("error"):
            print(f"❌ Context Extractor Error: {context_result['error']}")
        else:
            print("✅ Context Extractor working")
            print(f"   Location: {context_result.get('location')}")
            print(f"   Plant Type: {context_result.get('plant_type')}")
            print(f"   Season: {context_result.get('season')}")
    
    except Exception as e:
        print(f"❌ Context Extractor test failed: {str(e)}")
    
    # Test Prescription Tool
    try:
        from fsm_agent.tools.prescription_tool import run_prescription_tool
        
        prescription_result = await run_prescription_tool({
            "disease_name": "Early Blight",
            "plant_type": "Tomato",
            "location": "Tamil Nadu",
            "season": "Summer"
        })
        
        if prescription_result.get("error"):
            print(f"❌ Prescription Tool Error: {prescription_result['error']}")
        else:
            print("✅ Prescription Tool working")
            treatments = prescription_result.get("treatments", [])
            print(f"   Generated {len(treatments)} treatments")
    
    except Exception as e:
        print(f"❌ Prescription Tool test failed: {str(e)}")
    
    # Test Vendor Tool
    try:
        from fsm_agent.tools.vendor_tool import run_vendor_tool
        
        vendor_result = await run_vendor_tool({
            "treatments": [
                {"name": "Copper Sulfate Fungicide", "type": "Chemical"},
                {"name": "Neem Oil Solution", "type": "Organic"}
            ],
            "location": "Tamil Nadu"
        })
        
        if vendor_result.get("error"):
            print(f"❌ Vendor Tool Error: {vendor_result['error']}")
        else:
            print("✅ Vendor Tool working")
            vendors = vendor_result.get("vendors", [])
            print(f"   Found {len(vendors)} vendors")
    
    except Exception as e:
        print(f"❌ Vendor Tool test failed: {str(e)}")


async def main():
    """Run all tests"""
    print("🚀 Starting FSM Agent Tests")
    print("=" * 50)
    
    # Check if Ollama is available
    try:
        import requests
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        health_timeout = int(os.getenv("HEALTH_CHECK_TIMEOUT", "5"))
        response = requests.get(f"{ollama_host}/api/tags", timeout=health_timeout)
        if response.status_code == 200:
            print("✅ Ollama server is accessible")
        else:
            print("⚠️  Ollama server responded but may not be ready")
    except Exception as e:
        print(f"⚠️  Ollama server not accessible: {str(e)}")
        print("   Tests will continue but LLM functionality may fail")
    
    # Run tests
    await test_context_extraction()
    await test_tool_integration()
    
    # These tests require Ollama to be running
    try:
        await test_basic_conversation()
        await test_streaming()
    except Exception as e:
        print(f"⚠️  LLM-dependent tests failed (likely due to Ollama not being available): {str(e)}")
    
    print("\n🏁 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
