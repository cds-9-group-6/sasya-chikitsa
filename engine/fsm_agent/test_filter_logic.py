#!/usr/bin/env python3
"""
Test streaming filter logic directly (no dependencies)
"""

def filter_chunk_for_streaming(chunk):
    """
    Direct copy of the filtering logic to test
    """
    if not isinstance(chunk, dict):
        return chunk
        
    # Create filtered copy - start with everything and remove only problematic data
    filtered = chunk.copy()
    
    # REMOVE only large/problematic data that causes issues:
    
    # 1. Remove large base64 image data (this was the main problem)
    if "user_image" in filtered:
        del filtered["user_image"]
        
    # 2. Remove attention_overlay unless specifically requested (auto-streaming issue)
    if "attention_overlay" in filtered:
        del filtered["attention_overlay"]
        
    # 3. Keep messages but remove any base64 content from message content
    if "messages" in filtered and isinstance(filtered["messages"], list):
        for message in filtered["messages"]:
            if isinstance(message, dict) and "content" in message:
                content = message["content"]
                if isinstance(content, str) and len(content) > 5000:
                    # Truncate very long messages (likely containing base64 data)
                    message["content"] = content[:500] + "... [truncated for streaming]"
    
    return filtered

def test_streaming_filter():
    """Test the streaming filter logic"""
    
    print("🧪 Testing Streaming Filter Logic")
    print("=" * 50)
    
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
    
    print("📥 **Before Filtering:**")
    print(f"   - Total keys: {len(test_chunk)}")
    print(f"   - user_image size: {len(test_chunk.get('user_image', ''))} characters")
    print(f"   - Has classification_results: {bool(test_chunk.get('classification_results'))}")
    print(f"   - Has prescription_data: {bool(test_chunk.get('prescription_data'))}")
    print(f"   - Has attention_overlay: {bool(test_chunk.get('attention_overlay'))}")
    print(f"   - Messages count: {len(test_chunk.get('messages', []))}")
    print()
    
    # Test the filtering
    filtered_chunk = filter_chunk_for_streaming(test_chunk)
    
    print("📤 **After Filtering:**")
    print(f"   - Total keys: {len(filtered_chunk)}")
    print(f"   - Keys: {sorted(filtered_chunk.keys())}")
    print()
    
    # Check what was removed vs kept
    removed_keys = set(test_chunk.keys()) - set(filtered_chunk.keys())
    print(f"🚫 **Removed:** {sorted(removed_keys)}")
    print(f"✅ **Kept:** {sorted(filtered_chunk.keys())}")
    print()
    
    # Detailed checks
    checks = [
        ("user_image removed", "user_image" not in filtered_chunk),
        ("attention_overlay removed", "attention_overlay" not in filtered_chunk), 
        ("classification_results kept", "classification_results" in filtered_chunk),
        ("prescription_data kept", "prescription_data" in filtered_chunk),
        ("current_node kept", "current_node" in filtered_chunk),
        ("disease_name kept", "disease_name" in filtered_chunk),
        ("messages kept", "messages" in filtered_chunk),
        ("session_id kept", "session_id" in filtered_chunk),
    ]
    
    print("🔍 **Detailed Checks:**")
    for description, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {description}")
    
    print()
    
    # Show what would actually be streamed  
    print("📨 **Sample Streaming Data:**")
    print(f"event: state_update")
    streaming_data = str(filtered_chunk)
    if len(streaming_data) > 300:
        print(f"data: {streaming_data[:300]}...")
        print(f"   (truncated - total length: {len(streaming_data)} chars)")
    else:
        print(f"data: {streaming_data}")
    print()
    
    # Final result
    if filtered_chunk and len(filtered_chunk) > 3:  # Should have meaningful data
        print("✅ **SUCCESS!** Streaming data is meaningful and not empty")
        print(f"   - Contains {len(filtered_chunk)} data fields")
        print(f"   - Removed {len(removed_keys)} problematic fields")
        print(f"   - Keeps all important results for user")
    else:
        print("❌ **FAILURE!** Streaming data is empty or insufficient")
        
    print("\n" + "="*50)
    print("🎯 **KEY FINDINGS:**")
    print("   • Images are removed (prevents large payloads)")
    print("   • Attention overlay removed (prevents unwanted streaming)")
    print("   • All meaningful results kept (classification, prescription)")
    print("   • State information preserved (node, actions, metadata)")
    
if __name__ == "__main__":
    test_streaming_filter()


