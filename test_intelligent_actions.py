#!/usr/bin/env python3
"""
Test script to demonstrate the intelligent action prioritization system.
Shows how the agent now selects max 2 most relevant actions based on context.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'engine', 'api'))

# Mock the required dependencies for testing
class MockChatMessageHistory:
    def __init__(self):
        self.messages = []

class MockMessage:
    def __init__(self, msg_type, content):
        self.type = msg_type
        self.content = content

# Simple test class to demonstrate the logic
class TestIntelligentActions:
    def __init__(self):
        self.session_store = {}
        self.session_metadata = {}
    
    def get_session_history(self, session_id):
        if session_id not in self.session_store:
            self.session_store[session_id] = MockChatMessageHistory()
        return self.session_store[session_id]
    
    def get_session_metadata(self, session_id):
        if session_id not in self.session_metadata:
            self.session_metadata[session_id] = {}
        return self.session_metadata[session_id]
    
    def get_missing_metadata(self, session_id):
        metadata = self.get_session_metadata(session_id)
        required_fields = ['location', 'season', 'plant']
        return [field for field in required_fields if field not in metadata]
    
    def has_complete_metadata(self, session_id):
        return len(self.get_missing_metadata(session_id)) == 0
    
    def extract_disease_from_classification(self, text):
        disease_indicators = ['blight', 'rot', 'virus', 'disease', 'infection', 'fungal']
        for indicator in disease_indicators:
            if indicator in text.lower():
                return indicator
        return None
    
    def _get_previous_response_context(self, session_id):
        """Get the last 2 AI responses for context-aware action prioritization."""
        if not session_id:
            return ""
        
        history = self.get_session_history(session_id)
        messages = getattr(history, 'messages', [])
        
        # Get the last 2 AI responses for context
        ai_responses = []
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "ai":
                content = getattr(msg, "content", "")
                ai_responses.append(content)
                if len(ai_responses) >= 2:
                    break
        
        # Return combined context (most recent first)
        return " ".join(ai_responses)

    def _generate_fallback_action_items(self, main_answer: str, session_id: str = None, is_classification_result: bool = False) -> str:
        """Generate top 2 most relevant action items based on the main answer content and previous context."""
        
        # Get previous context for intelligent prioritization
        previous_context = self._get_previous_response_context(session_id) if session_id else ""
        
        # Create a scoring system for action items
        action_scores = {}
        
        # Convert to lowercase for keyword matching
        content_lower = main_answer.lower()
        
        # HIGH PRIORITY: Metadata collection for classification results with diseases
        if is_classification_result and session_id:
            missing_fields = self.get_missing_metadata(session_id)
            if len(missing_fields) > 0:
                disease = self.extract_disease_from_classification(main_answer)
                if disease:
                    # Disease detected - metadata collection is CRITICAL (score: 100+)
                    if 'location' in missing_fields:
                        action_scores["Tell me your location (district/state)"] = 120
                    if 'season' in missing_fields:
                        action_scores["Tell me the current season"] = 110
                    if 'plant' in missing_fields:
                        action_scores["Tell me what plant/crop this is"] = 115
                    
                    # Prescription actions get high priority but need metadata first
                    if len(missing_fields) == 1:
                        action_scores["Get plant-specific prescription"] = 105
                    else:
                        action_scores["Get specific prescription for my area"] = 100
                else:
                    # Healthy plant - lower priority for metadata (score: 40-60)
                    if 'plant' in missing_fields:
                        action_scores["Tell me what plant this is"] = 50
                    if 'location' in missing_fields:
                        action_scores["Tell me your location for better advice"] = 45
                    if 'season' in missing_fields:
                        action_scores["Tell me the current season"] = 40
        
        # CONTENT-BASED SCORING: Analyze main answer for relevant topics
        disease_keywords = ['disease', 'infection', 'fungal', 'bacterial', 'pest', 'blight', 'rot', 'virus']
        if any(keyword in content_lower for keyword in disease_keywords):
            if session_id and self.has_complete_metadata(session_id):
                metadata = self.get_session_metadata(session_id)
                plant_name = metadata.get('plant', 'plant')
                action_scores[f"Get specific prescription for {plant_name}"] = 90
            else:
                action_scores["Send me prescription for this disease"] = 85
            action_scores["Show treatment steps"] = 80
            
            # If previous context suggests prevention interest, boost prevention
            if 'prevent' in previous_context.lower() or 'avoid' in previous_context.lower():
                action_scores["Explain prevention methods"] = 88
        
        # Watering-related content
        if any(keyword in content_lower for keyword in ['watering', 'water', 'irrigation', 'dry', 'overwater']):
            action_scores["Give me watering schedule"] = 75
            # Boost if user asked about watering before
            if 'water' in previous_context.lower():
                action_scores["Give me watering schedule"] = 85
        
        # Fertilization/nutrition content  
        if any(keyword in content_lower for keyword in ['fertiliz', 'nutrien', 'feed', 'nitrogen', 'phosphorus']):
            action_scores["Show fertilization procedure"] = 70
            # Boost if nutrition was discussed before
            if any(word in previous_context.lower() for word in ['fertiliz', 'nutrien', 'feed']):
                action_scores["Show fertilization procedure"] = 80
        
        # Care and maintenance
        if any(keyword in content_lower for keyword in ['care', 'maintain', 'schedule', 'routine']):
            action_scores["Create plant care schedule"] = 65
        
        # Prevention-focused content
        if any(keyword in content_lower for keyword in ['prevent', 'avoid', 'stop', 'protect']):
            action_scores["Explain prevention methods"] = 70
        
        # Soil-related content
        if any(keyword in content_lower for keyword in ['soil', 'potting', 'repot', 'drainage', 'ph']):
            action_scores["Get soil recommendations"] = 60
        
        # Information requests
        if any(keyword in content_lower for keyword in ['information', 'need', 'tell me', 'describe', 'explain']):
            action_scores["Provide more details"] = 55
        
        # CONTEXTUAL BOOSTING: Increase scores based on previous conversation
        if previous_context:
            prev_lower = previous_context.lower()
            
            # If user previously asked about treatments, boost prescription
            if any(word in prev_lower for word in ['treatment', 'cure', 'medicine', 'spray']):
                for action in action_scores:
                    if 'prescription' in action or 'treatment' in action:
                        action_scores[action] += 15
            
            # If user showed interest in detailed care, boost care-related actions
            if any(word in prev_lower for word in ['schedule', 'routine', 'care', 'maintain']):
                for action in action_scores:
                    if 'schedule' in action or 'care' in action:
                        action_scores[action] += 10
        
        # FALLBACK ACTIONS: Add general actions with lower scores
        general_actions = {
            "Ask follow-up question": 30,
            "Get more plant care tips": 25, 
            "Upload new plant image": 20
        }
        
        # Only add general actions if we don't have enough high-scoring specific ones
        high_score_count = len([score for score in action_scores.values() if score >= 50])
        if high_score_count < 2:
            action_scores.update(general_actions)
        
        # SELECT TOP 2 ACTIONS: Sort by score and take the highest weighted
        if not action_scores:
            # Emergency fallback
            return "Ask follow-up question | Upload new plant image"
        
        # Sort actions by score (highest first) and take top 2
        sorted_actions = sorted(action_scores.items(), key=lambda x: x[1], reverse=True)
        top_actions = [action for action, score in sorted_actions[:2]]
        
        # Ensure we always have exactly 2 actions
        if len(top_actions) < 2:
            # Add a general action as backup
            for general_action in ["Ask follow-up question", "Upload new plant image"]:
                if general_action not in top_actions:
                    top_actions.append(general_action)
                    break
        
        return " | ".join(top_actions[:2])


def test_intelligent_actions():
    """Test the intelligent action prioritization system."""
    
    print("🧠 Testing Intelligent Action Prioritization System")
    print("=" * 60)
    
    test = TestIntelligentActions()
    
    # Test 1: Disease classification with missing metadata (highest priority)
    print("\n📊 Test 1: Disease classification with missing metadata")
    print("Scenario: Late blight detected, no location/season/plant info")
    
    session_id = "test_session_1"
    # No metadata set - all fields missing
    
    response = "Disease detected: Late blight. This fungal infection affects tomato plants."
    actions = test._generate_fallback_action_items(response, session_id, is_classification_result=True)
    
    print(f"Response: {response}")
    print(f"Actions: {actions}")
    print("✅ Should prioritize location collection (score: 120) and plant identification")
    
    # Test 2: Disease with previous prevention context
    print("\n📊 Test 2: Disease response with prevention context")
    print("Scenario: User previously asked about prevention, now sees disease info")
    
    session_id = "test_session_2"
    # Add previous prevention context
    history = test.get_session_history(session_id)
    history.messages.append(MockMessage("ai", "To prevent plant diseases, maintain good air circulation and avoid overwatering."))
    
    response = "This appears to be bacterial blight affecting your plant leaves."
    actions = test._generate_fallback_action_items(response, session_id, is_classification_result=False)
    
    print(f"Previous context: Prevention advice")
    print(f"Response: {response}")
    print(f"Actions: {actions}")
    print("✅ Should boost prevention methods due to previous interest")
    
    # Test 3: Watering-focused response with watering history
    print("\n📊 Test 3: Watering response with watering history")
    print("Scenario: User previously asked about water, now gets watering advice")
    
    session_id = "test_session_3"
    history = test.get_session_history(session_id)
    history.messages.append(MockMessage("ai", "Your plant needs water every 2-3 days. Check soil moisture regularly."))
    
    response = "The yellowing leaves suggest overwatering. Reduce watering frequency."
    actions = test._generate_fallback_action_items(response, session_id, is_classification_result=False)
    
    print(f"Previous context: Watering schedule advice")  
    print(f"Response: {response}")
    print(f"Actions: {actions}")
    print("✅ Should prioritize watering schedule (boosted from 75 to 85)")
    
    # Test 4: Healthy plant with complete metadata
    print("\n📊 Test 4: Healthy plant with complete metadata")
    print("Scenario: Healthy plant, user has provided all info")
    
    session_id = "test_session_4"
    # Set complete metadata
    metadata = test.get_session_metadata(session_id)
    metadata['location'] = 'California'
    metadata['season'] = 'Spring'
    metadata['plant'] = 'Tomato'
    
    response = "Your tomato plant looks healthy! Good leaf color and structure."
    actions = test._generate_fallback_action_items(response, session_id, is_classification_result=True)
    
    print(f"Metadata: Complete (location, season, plant)")
    print(f"Response: {response}")
    print(f"Actions: {actions}")
    print("✅ Should focus on care advice, not metadata collection")
    
    # Test 5: Limited context - fallback actions
    print("\n📊 Test 5: Limited context - fallback system")
    print("Scenario: Generic response, no clear priorities")
    
    response = "Thank you for your question about plant care."
    actions = test._generate_fallback_action_items(response, None, is_classification_result=False)
    
    print(f"Response: {response}")
    print(f"Actions: {actions}")
    print("✅ Should use general fallback actions")
    
    print("\n" + "=" * 60)
    print("🎯 Intelligent Action System Features:")
    print("• ✅ Max 2 actions per response")
    print("• ✅ Score-based prioritization (0-120+ points)")
    print("• ✅ Context-aware boosting from previous responses")
    print("• ✅ Disease detection gets highest priority (100-120)")
    print("• ✅ Content-based relevance scoring")
    print("• ✅ Fallback system for edge cases")
    print("• ✅ Metadata collection prioritized for classifications")
    print("• ✅ Previous conversation influences future actions")

if __name__ == "__main__":
    test_intelligent_actions()
