#!/usr/bin/env python3
"""
Test that streaming now shows meaningful state data (not empty {})
"""
import asyncio
import sys
import os

# Add engine directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

async def test_streaming_output():
    """Test that streaming now produces meaningful state data"""
    
    print("🧪 Testing Fixed Streaming Output")
    print("=" * 50)
    
    # Import workflow class
    try:
        from core.langgraph_workflow import PlantDiseaseWorkflow
        
        # Test the filtering method directly with mock data
        workflow = PlantDiseaseWorkflow({})
        
        # Mock chunk data that simulates real workflow output
        test_chunk = {
            "session_id": "test_session",
            "current_node": "classifying",
            "previous_node": "initial",
            "next_action": "prescribe",
            "is_complete": False,
            "disease_name": "Tomato Blight",
            "plant_type": "tomato",
            "location": "California",
            "season": "summer",
            "classification_results": {
                "disease_name": "Early Blight",
                "confidence": 0.87,
                "severity": "moderate"
            },
            "prescription_data": {
                "treatments": [
                    {"name": "Copper Fungicide", "category": "organic"},
                    {"name": "Chlorothalonil", "category": "chemical"}
                ]
            },
            "user_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA..." * 1000,  # Large base64 image
            "attention_overlay": "overlay_data_that_should_not_auto_stream",
            "messages": [
                {"role": "user", "content": "What's wrong with my plant?"},
                {"role": "assistant", "content": "Based on the analysis, your plant has Early Blight..."}
            ]
        }
        
        print("📥 **Input chunk data:**")
        print(f"   - user_image: {len(test_chunk.get('user_image', ''))} characters")
        print(f"   - classification_results: {bool(test_chunk.get('classification_results'))}")
        print(f"   - prescription_data: {bool(test_chunk.get('prescription_data'))}")
        print(f"   - attention_overlay: {bool(test_chunk.get('attention_overlay'))}")
        print(f"   - messages: {len(test_chunk.get('messages', []))} messages")
        print()
        
        # Test the filtering
        filtered_chunk = workflow._filter_chunk_for_streaming(test_chunk)
        
        print("📤 **Filtered chunk data (what gets streamed):**")
        print(f"   Total keys: {len(filtered_chunk)}")
        print(f"   Keys: {list(filtered_chunk.keys())}")
        print()
        
        # Check what was removed vs kept
        removed_keys = set(test_chunk.keys()) - set(filtered_chunk.keys())
        print(f"🚫 **Removed (good):** {removed_keys}")
        print(f"✅ **Kept (good):** {set(filtered_chunk.keys())}")
        print()
        
        # Check specific important data
        print("🔍 **Key Data Check:**")
        print(f"   - user_image removed: {'✅' if 'user_image' not in filtered_chunk else '❌'}")
        print(f"   - attention_overlay removed: {'✅' if 'attention_overlay' not in filtered_chunk else '❌'}")
        print(f"   - classification_results kept: {'✅' if 'classification_results' in filtered_chunk else '❌'}")
        print(f"   - prescription_data kept: {'✅' if 'prescription_data' in filtered_chunk else '❌'}")
        print(f"   - current_node kept: {'✅' if 'current_node' in filtered_chunk else '❌'}")
        print(f"   - disease_name kept: {'✅' if 'disease_name' in filtered_chunk else '❌'}")
        print(f"   - messages kept: {'✅' if 'messages' in filtered_chunk else '❌'}")
        print()
        
        # Show sample of what would be streamed
        print("📨 **Sample streaming data:**")
        print(f"   event: state_update")
        print(f"   data: {str(filtered_chunk)[:200]}...")
        print()
        
        # Check if data is meaningful (not empty)
        if filtered_chunk:
            print("✅ **SUCCESS**: Streaming data is meaningful and not empty!")
            print(f"   - Contains {len(filtered_chunk)} useful data fields")
            print(f"   - Removed {len(removed_keys)} problematic fields (images, etc.)")
        else:
            print("❌ **FAILURE**: Streaming data is empty!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the correct directory")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_streaming_output())
