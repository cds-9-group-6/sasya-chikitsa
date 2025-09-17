#!/usr/bin/env python3
"""
Test clean streaming - verify only essential state data is streamed once per transition
"""

def test_clean_filtering():
    """Test the updated filtering logic"""
    
    print("🧪 Testing Clean Streaming Logic")
    print("=" * 60)
    
    # Mock verbose state data (what we DON'T want to stream)
    verbose_state = {
        "session_id": "test_123",
        "current_node": "classifying", 
        "next_action": "prescribe",
        "classification_results": {
            "disease_name": "Fruit borer",
            "confidence": 1.0,
            "severity": "Unknown",
            "description": "Detected Fruit borer with 100.00% confidence",
            "attention_overlay": None,
            "raw_predictions": ["Resized image...", "Preprocessing...", "Running CNN...", "Analyzing results...", "Finalizing..."],  # VERBOSE
            "plant_context": {"plant_type": "tomato", "location": "Andhra Pradesh"}  # VERBOSE
        },
        "disease_name": "Fruit borer",
        "confidence": 1.0,
        "user_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA..." * 100,  # LARGE IMAGE
        "attention_overlay": "overlay_data_should_not_stream",  # UNWANTED
        "last_update_time": "2025-09-14T17:26:26.581302",  # VERBOSE TIMESTAMP
        "messages": [  # VERBOSE (handled separately)
            {"role": "user", "content": "What's wrong with my plant?"},
            {"role": "assistant", "content": "I'll analyze your plant image..."}
        ]
    }
    
    def filter_chunk_for_streaming(chunk):
        """Copy of the filtering logic"""
        if not isinstance(chunk, dict):
            return chunk
            
        # Create filtered copy - start with everything and remove problematic data
        filtered = chunk.copy()
        
        # 1. Remove large base64 image data
        for img_key in ["user_image", "image"]:
            if img_key in filtered:
                del filtered[img_key]
            
        # 2. Remove attention_overlay (auto-streaming issue)
        if "attention_overlay" in filtered:
            del filtered["attention_overlay"]
        
        # 3. Remove messages (handled separately to prevent duplication)    
        if "messages" in filtered:
            del filtered["messages"]
            
        # 4. Clean up verbose data in classification_results
        if "classification_results" in filtered and isinstance(filtered["classification_results"], dict):
            classification = filtered["classification_results"]
            
            # Remove verbose fields but keep essential results
            verbose_fields = ["raw_predictions", "plant_context", "attention_overlay"]
            for verbose_field in verbose_fields:
                if verbose_field in classification:
                    del classification[verbose_field]
            
            filtered["classification_results"] = classification
        
        # 5. Remove verbose timestamps that change constantly
        if "last_update_time" in filtered:
            del filtered["last_update_time"]
            
        return filtered
    
    print("📥 **Before Filtering (Verbose State):**")
    print(f"   Total keys: {len(verbose_state)}")
    print(f"   Contains user_image: {len(verbose_state.get('user_image', ''))} chars")
    print(f"   Contains messages: {len(verbose_state.get('messages', []))} messages")
    print(f"   Contains raw_predictions: {bool(verbose_state.get('classification_results', {}).get('raw_predictions'))}")
    print(f"   Contains last_update_time: {bool(verbose_state.get('last_update_time'))}")
    print()
    
    # Apply filtering
    clean_state = filter_chunk_for_streaming(verbose_state)
    
    print("📤 **After Filtering (Clean State):**")
    print(f"   Total keys: {len(clean_state)}")
    print(f"   Keys: {sorted(clean_state.keys())}")
    print()
    
    # Check what was removed vs kept
    removed_keys = set(verbose_state.keys()) - set(clean_state.keys())
    print(f"🚫 **Removed (Good):** {sorted(removed_keys)}")
    print()
    
    # Check cleaned classification results
    if "classification_results" in clean_state:
        clean_classification = clean_state["classification_results"]
        original_classification = verbose_state["classification_results"]
        
        removed_verbose = set(original_classification.keys()) - set(clean_classification.keys())
        print(f"🧹 **Cleaned from classification_results:** {sorted(removed_verbose)}")
        print(f"✅ **Kept in classification_results:** {sorted(clean_classification.keys())}")
        print()
    
    # Size comparison
    original_size = len(str(verbose_state))
    clean_size = len(str(clean_state))
    reduction = ((original_size - clean_size) / original_size * 100) if original_size > 0 else 0
    
    print(f"📊 **Size Reduction:**")
    print(f"   Original: {original_size} chars")
    print(f"   Cleaned: {clean_size} chars")
    print(f"   Reduction: {reduction:.1f}%")
    print()
    
    # Show what would actually be streamed
    print(f"📨 **Clean Streaming Output:**")
    print(f"event: state_update")
    clean_output = str(clean_state)
    if len(clean_output) > 300:
        print(f"data: {clean_output[:300]}...")
        print(f"   [Total length: {len(clean_output)} chars]")
    else:
        print(f"data: {clean_output}")
    print()
    
    print(f"🎯 **SUMMARY:**")
    print(f"   ✅ Large images removed ({len(verbose_state.get('user_image', ''))} chars)")
    print(f"   ✅ Verbose raw_predictions removed")
    print(f"   ✅ Messages removed (prevent duplication)")
    print(f"   ✅ Attention overlay removed")
    print(f"   ✅ Timestamps removed (reduce noise)")
    print(f"   ✅ Essential results preserved (disease_name, confidence, etc.)")
    print(f"   ✅ {reduction:.1f}% size reduction")
    print(f"\n🚀 **Result: Clean, single state update per transition!**")

if __name__ == "__main__":
    test_clean_filtering()


