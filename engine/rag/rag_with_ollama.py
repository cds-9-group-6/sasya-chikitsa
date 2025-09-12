# import pandas as pd
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from fastapi import FastAPI
from pydantic import BaseModel
# import uvicorn
import os
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ollama_rag:
    """
    Enhanced RAG system with pre-initialized ChromaDB collections for multiple plant types.
    
    Features:
    - Pre-initialized embeddings and retrievers for all supported plant types
    - Automatic plant type detection and collection routing
    - Fallback to general collection if specific plant type not found
    - Performance optimization through startup initialization
    """
    
    # Supported plant types and their ChromaDB collection mappings
    SUPPORTED_PLANT_TYPES = {
        'tomato': 'Tomato',
        'tomatoes': 'Tomato', 
        'potato': 'Potato',
        'potatoes': 'Potato',
        'rice': 'Rice',
        'wheat': 'Wheat',
        'corn': 'Corn',
        'maize': 'Corn',
        'cotton': 'Cotton',
        'sugarcane': 'Sugarcane',
        'onion': 'Onion',
        'onions': 'Onion',
        'garlic': 'Garlic'
    }
    
    # Default collections to initialize (most common plant types)
    DEFAULT_COLLECTIONS = ['Tomato', 'Potato', 'Rice', 'Wheat', 'Corn']
    
    # Creating the Prompt Template
    prompt_template = """
        You are an agricultural assistant specialized in answering questions about plant diseases.  
        Your task is to provide answers strictly based on the provided context when possible.  

        Each document contains the following fields:  
        - DistrictName  
        - StateName  
        - Season_English  
        - Month  
        - Disease  
        - QueryText  
        - KccAns (this is the official response section from source documents)

        Guidelines for answering:
        1. If a relevant answer is available in KccAns, use that with minimal changes.
        2. Use DistrictName, StateName, Season_English, Month, and Disease only to help interpret the question and select the correct KccAns, but **do not include these details in the final answer unless the question explicitly asks for them**.  
        3. If the answer is not available in the context, then rely on your own agricultural knowledge to provide the best possible answer.  
        4. Do not invent or assume information when KccAns is present; only fall back to your own knowledge when the context has no suitable answer.  

        CONTEXT:
        {context}

        QUESTION:
        {question}

        OUTPUT:
        """

    def __init__(self, 
                 llm_name: str, 
                 temperature: float = 0.1, 
                #  embedding_model: str = "intfloat/multilingual-e5-large-instruct",
                 embedding_model: str = "multi-qa-MiniLM-L6-cos-v1",
                 collections_to_init: Optional[List[str]] = None,
                #  persist_directory: str = "./chroma_capstone_db_new"
                 persist_directory: str = "./chroma_capstone_db_new_small"):
        """
        Initialize RAG system with pre-loaded embeddings and retrievers for multiple plant collections.
        
        Args:
            llm_name: Name of the LLM model to use
            temperature: Temperature setting for LLM
            embedding_model: HuggingFace embedding model name
            collections_to_init: List of collections to initialize (defaults to DEFAULT_COLLECTIONS)
            persist_directory: ChromaDB persistence directory
        """
        logger.info("🌱 Initializing Enhanced Multi-Plant RAG System...")
        
        # Initialize LLM
        self._initialize_llm(llm_name, temperature)
        
        # Initialize prompt template
        self.PROMPT = PromptTemplate(
            template=self.prompt_template, input_variables=["context", "question"]
        )
        self.chain_type_kwargs = {"prompt": self.PROMPT}
        
        # Initialize embeddings (shared across all collections)
        logger.info(f"📚 Initializing embeddings with model: {embedding_model}")
        self.embedding = HuggingFaceEmbeddings(model_name=embedding_model)
        self.persist_directory = persist_directory
        
        # Determine which collections to initialize
        self.collections_to_init = collections_to_init or self.DEFAULT_COLLECTIONS
        logger.info(f"🗂️  Initializing collections: {self.collections_to_init}")
        
        # Pre-initialize all ChromaDB collections and retrievers
        self.chroma_databases: Dict[str, Chroma] = {}
        self.retrievers: Dict[str, RetrievalQA] = {}
        self._initialize_all_collections()
        
        # Set default collection (fallback)
        self.default_collection = self.collections_to_init[0] if self.collections_to_init else 'Tomato'
        
        logger.info("✅ Enhanced RAG system initialization completed!")
        logger.info(f"   📊 Loaded {len(self.chroma_databases)} collections")
        logger.info(f"   🔍 Configured {len(self.retrievers)} retrievers")
        logger.info(f"   🎯 Default collection: {self.default_collection}")

    def _initialize_llm(self, llm_name: str, temperature: float):
        """Initialize the LLM with proper configuration."""
        logger.debug("Initializing LLM...")
        ollama_host = os.getenv("OLLAMA_HOST")
        logger.debug(f"OLLAMA_HOST={ollama_host}")

        if ollama_host:
            self.llm = ChatOllama(
                model=os.getenv("OLLAMA_MODEL", llm_name),
                temperature=temperature,
                base_url=ollama_host,
                reasoning=False  # Disable reasoning for performance
            )
            logger.info(f"✅ Using Ollama model: {self.llm.model}")
        else:
            logger.error("OLLAMA_HOST not set.")
            raise RuntimeError(
                "No chat model configured. Set OLLAMA_HOST (and optionally OLLAMA_MODEL) or run Ollama and set OLLAMA_MODEL."
            )

    def _initialize_all_collections(self):
        """Pre-initialize ChromaDB and retrievers for all specified collections."""
        successful_collections = []
        
        for collection_name in self.collections_to_init:
            try:
                logger.info(f"🔧 Initializing collection: {collection_name}")
                
                # Initialize ChromaDB for this collection
                chroma_db = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embedding,
                    collection_name=collection_name
                )
                
                # Create retriever for this collection
                chroma_retriever = chroma_db.as_retriever(
                    search_type="mmr", 
                    search_kwargs={"k": 6, "fetch_k": 12}
                )
                
                # Create RetrievalQA chain for this collection
                retrieval_qa = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=chroma_retriever,
                    input_key="query",
                    return_source_documents=True,
                    chain_type_kwargs=self.chain_type_kwargs,
                )
                
                # Store in dictionaries
                self.chroma_databases[collection_name] = chroma_db
                self.retrievers[collection_name] = retrieval_qa
                successful_collections.append(collection_name)
                
                logger.info(f"✅ Successfully initialized collection: {collection_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize collection {collection_name}: {e}")
                continue
        
        if not successful_collections:
            raise RuntimeError("Failed to initialize any ChromaDB collections!")
        
        logger.info(f"🎉 Successfully initialized {len(successful_collections)} collections")
        
    def _detect_plant_type(self, query: str) -> str:
        """
        Detect plant type from query text and return the appropriate collection name.
        
        Args:
            query: The user query text
            
        Returns:
            ChromaDB collection name for the detected plant type
        """
        query_lower = query.lower()
        
        # Check for plant type keywords in query
        for plant_keyword, collection_name in self.SUPPORTED_PLANT_TYPES.items():
            if plant_keyword in query_lower:
                if collection_name in self.chroma_databases:
                    logger.debug(f"🎯 Detected plant type: {plant_keyword} → collection: {collection_name}")
                    return collection_name
                else:
                    logger.debug(f"⚠️  Plant type detected ({plant_keyword}) but collection not available: {collection_name}")
        
        # Fallback to default collection
        logger.debug(f"🔄 No specific plant type detected, using default: {self.default_collection}")
        return self.default_collection

    def run_query(self, query_request: str, plant_type: Optional[str] = None) -> str:
        """
        Run a query against the appropriate plant-specific collection.
        
        Args:
            query_request: The query to search for
            plant_type: Optional explicit plant type (overrides auto-detection)
            
        Returns:
            Answer from the RAG system
        """
        try:
            # Determine which collection to use
            if plant_type and plant_type in self.chroma_databases:
                collection_name = plant_type
                logger.debug(f"🎯 Using explicit plant type: {plant_type}")
            else:
                collection_name = self._detect_plant_type(query_request)
            
            # Get the appropriate retriever
            if collection_name not in self.retrievers:
                logger.warning(f"⚠️  Collection {collection_name} not available, falling back to {self.default_collection}")
                collection_name = self.default_collection
            
            retriever = self.retrievers[collection_name]
            logger.debug(f"🔍 Querying collection: {collection_name}")
            
            # Execute the query
            answer = retriever.invoke({"query": query_request})["result"]
            logger.info(f"✅ Query completed successfully using collection: {collection_name}")
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Error during query execution: {e}")
            # Try fallback to default collection if not already using it
            if collection_name != self.default_collection:
                logger.info(f"🔄 Attempting fallback to default collection: {self.default_collection}")
                try:
                    retriever = self.retrievers[self.default_collection]
                    answer = retriever.invoke({"query": query_request})["result"]
                    logger.info("✅ Fallback query completed successfully")
                    return answer
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback query also failed: {fallback_error}")
            
            raise RuntimeError(f"RAG query failed: {e}")

    def get_available_collections(self) -> List[str]:
        """Get list of successfully initialized collections."""
        return list(self.chroma_databases.keys())
    
    def get_collection_info(self) -> Dict[str, Dict]:
        """Get information about all initialized collections."""
        info = {}
        for collection_name, chroma_db in self.chroma_databases.items():
            try:
                # Try to get basic collection info
                info[collection_name] = {
                    "collection_name": collection_name,
                    "persist_directory": self.persist_directory,
                    "status": "initialized",
                    "has_retriever": collection_name in self.retrievers
                }
            except Exception as e:
                info[collection_name] = {
                    "collection_name": collection_name,
                    "status": "error",
                    "error": str(e)
                }
        return info

# Example usage:
# if __name__ == "__main__":
#     # Initialize with default collections
#     rag_system = ollama_rag(llm_name="llama-3.1:8b", temperature=0.1)
#     
#     # Query with automatic plant type detection
#     response = rag_system.run_query("What are common diseases in tomatoes?")
#     print(response)
#     
#     # Query with explicit plant type
#     response = rag_system.run_query("Treatment for blight", plant_type="Tomato")
#     print(response)
#     
#     # Check available collections
#     print("Available collections:", rag_system.get_available_collections())
