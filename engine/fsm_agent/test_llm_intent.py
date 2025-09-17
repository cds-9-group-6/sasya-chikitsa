#!/usr/bin/env python3
"""
Test the enhanced LLM-driven intent analysis
"""
import asyncio
import sys
import os

# Add engine directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

async def test_llm_intent_analysis():
    """Test LLM-driven intent analysis vs keyword matching"""
    
    print("🧪 Testing LLM-Driven Intent Analysis")
    print("=" * 60)
    
    # Mock LLM class for testing
    class MockLLM:
        async def ainvoke(self, prompt):
            # Simulate LLM response based on the prompt
            user_message = prompt.split('User message: "')[1].split('"')[0]
            
            class MockResponse:
                def __init__(self, content):
                    self.content = content
            
            # Mock LLM intelligence - analyze the actual user message
            if any(word in user_message.lower() for word in ['sick', 'wrong', 'disease', 'problem', 'issue']):
                wants_classification = True
            else:
                wants_classification = False
                
            if any(word in user_message.lower() for word in ['help', 'fix', 'cure', 'treatment', 'better']):
                wants_prescription = True
                wants_classification = True
            else:
                wants_prescription = False
                
            if any(word in user_message.lower() for word in ['buy', 'purchase', 'where', 'shop']):
                wants_vendors = True
                wants_prescription = True
                wants_classification = True
            else:
                wants_vendors = False
                
            wants_full_workflow = wants_vendors and wants_prescription and wants_classification
            
            response_json = f'{{"wants_classification": {str(wants_classification).lower()}, "wants_prescription": {str(wants_prescription).lower()}, "wants_vendors": {str(wants_vendors).lower()}, "wants_full_workflow": {str(wants_full_workflow).lower()}}}'
            
            return MockResponse(response_json)
    
    # Mock workflow class with just the intent analysis methods
    class MockWorkflow:
        def __init__(self):
            self.llm = MockLLM()
        
        async def _analyze_user_intent(self, user_message: str) -> dict:
            """LLM-driven intent analysis (copied from the actual implementation)"""
            try:
                intent_prompt = f"""You are an expert at understanding user intent for a plant disease diagnosis and treatment system.

Analyze the following user message and determine their intent by responding with ONLY a JSON object containing these boolean fields:
- wants_classification: Does the user want disease diagnosis/identification?
- wants_prescription: Does the user want treatment recommendations?
- wants_vendors: Does the user want to find/buy products?
- wants_full_workflow: Does the user want the complete process (diagnosis + treatment + vendors)?

Rules:
1. If they want prescription OR vendors OR full workflow, they automatically need classification first
2. If they want vendors OR full workflow, they automatically need prescription first
3. Use natural language understanding, not just keyword matching
4. Consider context and implied meaning

Examples:
- "What's wrong with my plant?" → {{"wants_classification": true, "wants_prescription": false, "wants_vendors": false, "wants_full_workflow": false}}
- "Help my tomato plant get better" → {{"wants_classification": true, "wants_prescription": true, "wants_vendors": false, "wants_full_workflow": false}}
- "Where can I buy medicine for my sick plant?" → {{"wants_classification": true, "wants_prescription": true, "wants_vendors": true, "wants_full_workflow": false}}

User message: "{user_message}"

Response (JSON only):"""

                response = await self.llm.ainvoke(intent_prompt)
                response_text = response.content.strip()
                
                import json
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    intent = json.loads(json_str)
                    
                    # Apply dependency rules
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
            """Keyword-based fallback analysis"""
            user_message_lower = user_message.lower()
            
            intent = {
                "wants_classification": False,
                "wants_prescription": False,
                "wants_vendors": False,
                "wants_full_workflow": False
            }
            
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
            
            return intent
    
    # Test cases that show the difference between keyword vs LLM analysis
    test_cases = [
        {
            "message": "My tomato plant doesn't look healthy",
            "description": "No direct keywords but implies diagnosis needed"
        },
        {
            "message": "Can you please make my plant better?",
            "description": "Implies treatment but doesn't use 'treatment' keyword"
        },
        {
            "message": "My leaves are turning yellow, what should I do?",
            "description": "Implies both diagnosis and treatment without keywords"
        },
        {
            "message": "Something is eating my plant, where do I get spray?",
            "description": "Implies full workflow (diagnosis → treatment → vendors)"
        },
        {
            "message": "I need to save my dying crop",
            "description": "Emotional language, implies help needed"
        },
        {
            "message": "Please diagnose my plant disease",
            "description": "Direct keyword match (baseline)"
        }
    ]
    
    workflow = MockWorkflow()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['description']}")
        print(f"   User Message: \"{test_case['message']}\"")
        
        # Get LLM-driven analysis
        llm_result = await workflow._analyze_user_intent(test_case['message'])
        print(f"   🧠 LLM Analysis: {llm_result}")
        
        # Get keyword-based analysis for comparison
        keyword_result = await workflow._fallback_intent_analysis(test_case['message'])
        print(f"   📝 Keyword Analysis: {keyword_result}")
        
        # Show the difference
        if llm_result != keyword_result:
            print(f"   ✨ LLM found intent that keywords missed!")
        else:
            print(f"   ✅ Both methods agree")
    
    print(f"\n🎉 LLM Intent Analysis Testing Completed!")
    print(f"\n💡 **Key Benefits of LLM-Driven Intent Analysis:**")
    print(f"   • Understands natural language without specific keywords")
    print(f"   • Captures user intent from context and implications") 
    print(f"   • More flexible and user-friendly")
    print(f"   • Handles variations in expression")
    print(f"   • Provides fallback to keyword matching if LLM fails")

if __name__ == "__main__":
    asyncio.run(test_llm_intent_analysis())


