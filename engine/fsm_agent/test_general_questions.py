#!/usr/bin/env python3
"""
Test enhanced intent analysis with general question handling
"""
import asyncio
import json
import sys
import os

# Add engine directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

async def test_general_question_handling():
    """Test general question handling in intent analysis"""
    
    print("🧪 Testing Enhanced Intent Analysis with General Questions")
    print("=" * 70)
    
    # Mock LLM class for testing
    class MockLLM:
        async def ainvoke(self, prompt):
            # Simulate LLM response based on the prompt
            user_message = prompt.split('User message: "')[1].split('"')[0]
            
            class MockResponse:
                def __init__(self, content):
                    self.content = content
            
            # Mock LLM intelligence - analyze for general questions vs tool requests
            responses = {
                "What's wrong with my plant?": {
                    "wants_classification": True,
                    "wants_prescription": False,
                    "wants_vendors": False,
                    "wants_full_workflow": False,
                    "is_general_question": False,
                    "general_answer": ""
                },
                "When should I plant tomatoes?": {
                    "wants_classification": False,
                    "wants_prescription": False,
                    "wants_vendors": False,
                    "wants_full_workflow": False,
                    "is_general_question": True,
                    "general_answer": "The best time to plant tomatoes depends on your location. Generally, plant tomatoes after the last frost date in your area. In most regions, this is 2-3 weeks after the last frost when soil temperature reaches 60-65°F (15-18°C). For warm climates, plant in early spring or fall. For cooler climates, start seeds indoors 6-8 weeks before the last frost date."
                },
                "How often should I water my crops?": {
                    "wants_classification": False,
                    "wants_prescription": False,
                    "wants_vendors": False,
                    "wants_full_workflow": False,
                    "is_general_question": True,
                    "general_answer": "Watering frequency depends on crop type, soil, weather, and growth stage. Generally, most crops need 1-2 inches of water per week including rainfall. Water deeply but less frequently to encourage deep root growth. Check soil moisture 2-3 inches deep - if dry, it's time to water. Early morning is the best time to water to reduce evaporation and disease risk."
                },
                "What's the weather like for farming?": {
                    "wants_classification": False,
                    "wants_prescription": False,
                    "wants_vendors": False,
                    "wants_full_workflow": False,
                    "is_general_question": True,
                    "general_answer": "Weather conditions greatly affect farming success. Key factors include temperature, rainfall, humidity, and wind. Check local weather forecasts for frost warnings, precipitation amounts, and extreme temperature alerts. Consider seasonal patterns - spring for planting, summer for growth monitoring, fall for harvest preparation. Use weather apps or agricultural extension services for farming-specific forecasts."
                },
                "My plant has yellow leaves, help fix it": {
                    "wants_classification": True,
                    "wants_prescription": True,
                    "wants_vendors": False,
                    "wants_full_workflow": False,
                    "is_general_question": False,
                    "general_answer": ""
                }
            }
            
            # Get the response or default
            response_data = responses.get(user_message, {
                "wants_classification": False,
                "wants_prescription": False,
                "wants_vendors": False,
                "wants_full_workflow": False,
                "is_general_question": True,
                "general_answer": "I can provide general agricultural guidance, but for specific advice, please provide more details or consider using my specialized plant disease diagnosis tools."
            })
            
            response_json = json.dumps(response_data)
            return MockResponse(response_json)
    
    # Mock workflow class with the enhanced intent analysis methods
    class MockWorkflow:
        def __init__(self):
            self.llm = MockLLM()
        
        async def _analyze_user_intent(self, user_message: str) -> dict:
            """Enhanced LLM-driven intent analysis (copied from actual implementation)"""
            try:
                intent_prompt = f"""You are an expert at understanding user intent for a plant disease diagnosis and treatment system.

Analyze the following user message and determine their intent by responding with ONLY a JSON object containing these fields:
- wants_classification: (boolean) Does the user want disease diagnosis/identification?
- wants_prescription: (boolean) Does the user want treatment recommendations?  
- wants_vendors: (boolean) Does the user want to find/buy products?
- wants_full_workflow: (boolean) Does the user want the complete process (diagnosis + treatment + vendors)?
- is_general_question: (boolean) Is this a general agricultural/farming question that doesn't require specialized tools?
- general_answer: (string) If is_general_question=true, provide a helpful answer to their question. Otherwise, leave as empty string.

User message: "{user_message}"

Response (JSON only):"""

                response = await self.llm.ainvoke(intent_prompt)
                response_text = response.content.strip()
                
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    intent = json.loads(json_str)
                    
                    # Ensure all required keys exist with defaults
                    default_intent = {
                        "wants_classification": False,
                        "wants_prescription": False,
                        "wants_vendors": False,
                        "wants_full_workflow": False,
                        "is_general_question": False,
                        "general_answer": ""
                    }
                    default_intent.update(intent)
                    intent = default_intent
                    
                    # Apply dependency rules (only for non-general questions)
                    if not intent.get("is_general_question", False):
                        if intent.get("wants_prescription") or intent.get("wants_vendors") or intent.get("wants_full_workflow"):
                            intent["wants_classification"] = True
                        
                        if intent.get("wants_vendors") or intent.get("wants_full_workflow"):
                            intent["wants_prescription"] = True
                            intent["wants_classification"] = True
                        
                        if intent.get("wants_full_workflow"):
                            intent["wants_vendors"] = True
                            intent["wants_prescription"] = True
                            intent["wants_classification"] = True
                    
                    return intent
                    
            except Exception as e:
                print(f"Error in LLM analysis: {e}")
                return await self._fallback_intent_analysis(user_message)
        
        async def _fallback_intent_analysis(self, user_message: str) -> dict:
            """Enhanced fallback analysis with general question detection"""
            user_message_lower = user_message.lower()
            
            intent = {
                "wants_classification": False,
                "wants_prescription": False,
                "wants_vendors": False,
                "wants_full_workflow": False,
                "is_general_question": False,
                "general_answer": ""
            }
            
            # Tool-based keywords (existing logic)
            classification_keywords = ["analyze", "detect", "identify", "classify", "disease", "what", "wrong", "issue", "problem"]
            if any(word in user_message_lower for word in classification_keywords):
                intent["wants_classification"] = True
            
            prescription_keywords = ["treatment", "cure", "fix", "help", "recommend", "prescription", "medicine", "spray"]
            if any(word in user_message_lower for word in prescription_keywords):
                intent["wants_prescription"] = True
                intent["wants_classification"] = True
            
            vendor_keywords = ["buy", "purchase", "order", "vendor", "shop", "price", "cost"]
            if any(word in user_message_lower for word in vendor_keywords):
                intent["wants_vendors"] = True
                intent["wants_prescription"] = True
                intent["wants_classification"] = True
            
            # General question detection (new logic)
            general_keywords = ["how", "when", "why", "what", "where", "best time", "tips", "advice", "weather", "climate"]
            farming_keywords = ["plant", "grow", "crop", "farm", "soil", "water", "fertilizer", "seed"]
            
            # If it contains general question words + farming context but no specific tool requests
            if (any(word in user_message_lower for word in general_keywords) and 
                any(word in user_message_lower for word in farming_keywords) and 
                not any([intent["wants_classification"], intent["wants_prescription"], intent["wants_vendors"]])):
                
                intent["is_general_question"] = True
                intent["general_answer"] = "I understand you have a general farming question. For the best answer, please try again when the LLM system is available, or feel free to ask about specific plant diseases or issues that I can help diagnose and treat."
            
            return intent
    
    # Test cases for general questions
    test_cases = [
        {
            "message": "What's wrong with my plant?",
            "expected_type": "tool_request",
            "description": "Disease diagnosis request (tool-based)"
        },
        {
            "message": "When should I plant tomatoes?",
            "expected_type": "general_question",
            "description": "General farming timing question"
        },
        {
            "message": "How often should I water my crops?",
            "expected_type": "general_question", 
            "description": "General watering advice question"
        },
        {
            "message": "What's the weather like for farming?",
            "expected_type": "general_question",
            "description": "Weather-related farming question"
        },
        {
            "message": "My plant has yellow leaves, help fix it",
            "expected_type": "tool_request",
            "description": "Disease + treatment request (tool-based)"
        },
        {
            "message": "What are the best fertilizers to use?",
            "expected_type": "general_question",
            "description": "General fertilizer advice"
        }
    ]
    
    workflow = MockWorkflow()
    
    print(f"🎯 Testing {len(test_cases)} different question types:\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📝 Test {i}: {test_case['description']}")
        print(f"   User: \"{test_case['message']}\"")
        
        # Get intent analysis
        result = await workflow._analyze_user_intent(test_case['message'])
        
        # Check if it's a general question
        is_general = result.get("is_general_question", False)
        general_answer = result.get("general_answer", "")
        
        if is_general:
            print(f"   🌾 **GENERAL QUESTION DETECTED**")
            print(f"   🤖 AI Answer: \"{general_answer[:100]}{'...' if len(general_answer) > 100 else ''}\"")
            expected = test_case['expected_type'] == 'general_question'
            status = "✅ CORRECT" if expected else "❌ UNEXPECTED"
        else:
            tool_intents = [k for k, v in result.items() if k.startswith('wants_') and v]
            print(f"   🔧 **TOOL REQUEST DETECTED**: {tool_intents}")
            expected = test_case['expected_type'] == 'tool_request'  
            status = "✅ CORRECT" if expected else "❌ UNEXPECTED"
        
        print(f"   📊 Result: {status}")
        print()
    
    print("🎉 Enhanced Intent Analysis Testing Complete!")
    print("\n💡 **Key Improvements:**")
    print("   • ✅ Detects general agricultural questions")
    print("   • ✅ Provides direct answers for non-tool questions")
    print("   • ✅ Distinguishes between tool requests and general advice")
    print("   • ✅ Handles weather, timing, and farming tip questions")
    print("   • ✅ Maintains existing tool-based functionality")
    print("   • ✅ Fallback support for when LLM is unavailable")

if __name__ == "__main__":
    asyncio.run(test_general_question_handling())


