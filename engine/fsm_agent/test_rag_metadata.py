#!/usr/bin/env python3
"""
Test script for RAG metadata filtering enhancements
"""
import sys
import os

# Add engine directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import logging
# from engine.rag.rag_with_ollama import OllamaRag
# we do not need engine part of the package here
from rag.rag_with_ollama import OllamaRag

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_metadata_filtering():
    """Test RAG metadata filtering functionality"""
    
    print("🧪 Testing RAG Metadata Filtering Enhancement")
    print("=" * 50)
    
    try:
        # Initialize RAG system
        print("📚 Initializing RAG system...")
        rag_system = OllamaRag(
            llm_name="llama3.1:8b",
            temperature=0.1,
            collections_to_init=["Tomato"]  # Just test with Tomato collection
        )
        
        print(f"✅ RAG system initialized successfully")
        print(f"   Collections available: {rag_system.get_available_collections()}")
        print()
        
        # Test queries with different metadata combinations
        test_cases = [
            # {
            #     "name": "Basic Query (No Metadata)",
            #     "query": "What is Fruit borer disease treatment?",
            #     "metadata": {}
            # },
            # {
            #     "name": "Query with Season Filter",
            #     "query": "Fruit borer treatment recommendations",
            #     "metadata": {"season": "summer"}
            # },
            # {
            #     "name": "Query with Location Filter",
            #     "query": "Treatment for Fruit borer disease",
            #     "metadata": {"location": "Maharashtra"}
            # },
            # {
            #     "name": "Query with Disease Filter",
            #     "query": "Effective treatment options",
            #     "metadata": {"disease": "Black_rot"}
            # },
            {
                "name": "Query with All Metadata",
                "query": "Comprehensive treatment for fruit borer",
                "metadata": {
                    "season": "summer",
                    "location": "Maharashtra", 
                    "disease": "Fruit borer",
                    "plant_type": "Tomato"
                }
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"🔍 Test Case {i}: {test_case['name']}")
            print(f"   Query: {test_case['query']}")
            print(f"   Metadata: {test_case['metadata']}")
            
            try:
                # Run the query with metadata
                response = rag_system.run_query(
                    query_request=test_case['query'],
                    **test_case['metadata']
                )
                
                print(f"   ✅ Success! Response length: {len(response)} characters")
                print(f"   📝 Response preview: {response[:100]}...")
                print()
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                print()
        
        # Test metadata filter building
        print("🔧 Testing Metadata Filter Building")
        print("-" * 30)
        
        filter_tests = [
            {"season": "summer", "location": "test", "disease": "Black_rot"},
            {"season": "winter", "location": None, "disease": None},
            {"season": None, "location": "Maharashtra", "disease": "Leaf_spot"},
            {}
        ]
        
        for filter_test in filter_tests:
            metadata_filter = rag_system._build_metadata_filter(
                season=filter_test.get("season"),
                location=filter_test.get("location"),
                disease=filter_test.get("disease")
            )
            print(f"   Input: {filter_test}")
            print(f"   Filter: {metadata_filter}")
            print()
        
        print("✅ All RAG metadata filtering tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_metadata_filtering()
