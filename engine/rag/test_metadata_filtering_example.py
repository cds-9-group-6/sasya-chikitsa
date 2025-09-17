#!/usr/bin/env python3
"""
Example script demonstrating the enhanced RetrievalQA with metadata filtering.

This shows how to use the improved RAG system that properly integrates
RetrievalQA.from_chain_type with metadata filtering.
"""

import os
from rag_with_ollama import OllamaRag

def test_enhanced_rag():
    """Test the enhanced RAG system with various query types."""
    
    print("🌱 Testing Enhanced RAG System with RetrievalQA + Metadata Filtering")
    print("=" * 70)
    
    # Initialize RAG system
    rag = OllamaRag(
        llm_name="llama3.1:8b",
        temperature=0.1,
        collections_to_init=['Tomato', 'Potato', 'Rice']
    )
    
    print(f"✅ Available collections: {rag.get_available_collections()}")
    print()
    
    # Test 1: Standard RetrievalQA query (no filters)
    print("🔍 Test 1: Standard RetrievalQA Query")
    print("-" * 40)
    query1 = "What are the symptoms of tomato leaf blight?"
    try:
        answer1 = rag.query(query1)
        print(f"Query: {query1}")
        print(f"Answer: {answer1[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 2: Metadata-filtered RetrievalQA query
    print("🎯 Test 2: Metadata-Filtered RetrievalQA Query")
    print("-" * 40)
    query2 = "Disease treatment recommendations"
    try:
        answer2 = rag.query(
            query2,
            plant_type="Tomato",
            season="Summer", 
            location="Maharashtra"
        )
        print(f"Query: {query2}")
        print(f"Filters: Tomato, Summer season, Maharashtra")
        print(f"Answer: {answer2[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 3: Query with source documents
    print("📚 Test 3: RetrievalQA with Source Documents")
    print("-" * 40)
    query3 = "How to prevent potato diseases?"
    try:
        result3 = rag.query_with_sources(
            query3,
            plant_type="Potato",
            season="Kharif"
        )
        print(f"Query: {query3}")
        print(f"Answer: {result3['result'][:200]}...")
        print(f"Source documents: {len(result3.get('source_documents', []))} documents")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 4: Debug metadata filtering
    print("🔬 Test 4: Debug Metadata Filtering")
    print("-" * 40)
    query4 = "pest control methods"
    try:
        debug_result = rag.test_metadata_filtering(
            query4,
            plant_type="Tomato",
            season="Summer",
            location="Punjab"
        )
        print(f"Query: {query4}")
        print(f"Collection used: {debug_result['collection_used']}")
        print(f"Metadata filter: {debug_result['metadata_filter']}")
        print(f"Unfiltered docs: {debug_result['docs_unfiltered_count']}")
        print(f"Filtered docs: {debug_result['docs_filtered_count']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    print("🎉 Testing completed!")

if __name__ == "__main__":
    # Set environment variables (adjust as needed)
    os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"
    os.environ["OLLAMA_MODEL"] = "llama3.1:8b"
    
    test_enhanced_rag()
