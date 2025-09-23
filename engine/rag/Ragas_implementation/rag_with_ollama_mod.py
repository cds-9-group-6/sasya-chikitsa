# import pandas as pd
import chromadb
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from fastapi import FastAPI
from pydantic import BaseModel
from mlflow_test import RAG_Evaluation
# import uvicorn
import os
import logging
from typing import Dict, List, Optional
import asyncio


# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
# logging.getLogger("ragas").setLevel(logging.WARNING)

class OllamaRag:
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

    # Default available collections to initialize (most common plant types)
    DEFAULT_COLLECTIONS = ['Apple', 'Coconut', 'Paddy_Dhan', 'Potato', 'Tomato']

    State_name = ['JAMMU AND KASHMIR', 'HIMACHAL PRADESH', 'ODISHA',
                  'ANDHRA PRADESH', 'UTTARAKHAND', 'RAJASTHAN', 'HARYANA',
                  'MAHARASHTRA', 'ASSAM', 'WEST BENGAL', 'UTTAR PRADESH', 'BIHAR',
                  'SIKKIM', 'MANIPUR', 'MADHYA PRADESH', 'DELHI', 'KERALA',
                  'TAMILNADU', 'TRIPURA', 'KARNATAKA', 'GUJARAT', 'MEGHALAYA',
                  'CHHATTISGARH', 'PUDUCHERRY', 'JHARKAND', 'TELANGANA', 'NAGALAND',
                  'ARUNACHAL PRADESH', 'A AND N ISLANDS', 'PUNJAB', 'MIZORAM']
    
    
    disease_names = ['Alternaria leaf blotch', 'Blossom thrips', 'Codling moth',
                    'Collar rot', 'Crown gall', 'European red mite', 'Fire blight',
                    'Leaf miner', 'leaf roller', 'Marssonina leaf blotch',
                    'mosaic virus', 'Powdery mildew', 'root borer', 'Rust',
                    'San Jose scale', 'scab', 'stem borer', 'White root rot',
                    'Woolly aphid', 'Bud rot', 'caterpillar', 'Crown rot',
                    'eriophyid mite', 'Ganoderma wilt', 'Grey leaf blight',
                    'Leaf blight', 'Red palm weevil', 'Rhinoceros beetle',
                    'Root wilt disease', 'Scale insects', 'Stem bleeding disease',
                    'Termites', 'White grub', 'Dhan Armyworm', 'Dhan Bacterial blight',
                    'Dhan Bakanae', 'Dhan Blast', 'Dhan Brown planthopper',
                    'Dhan Brown spot', 'Dhan ear cutting caterpillar',
                    'Dhan False smut', 'Dhan Grain discoloration',
                    'Dhan Green leafhopper', 'Dhan hispa', 'Dhan Leaf folder',
                    'Dhan Leaf scald', 'Dhan mealy bug', 'Dhan root weevil',
                    'Dhan Sheath blight', 'Dhan Sheath rot', 'Dhan stem borer',
                    'Dhan Tungro virus', 'Aphids', 'Bacterial wilt', 'Black scurf',
                    'Brown rot', 'Common scab', 'Cutworms', 'Early blight', 'Jassids',
                    'Late blight', 'Leaf roll virus', 'Red spider mite', 'Thrips',
                    'tuber moth', 'Fruit borer', 'Septoria leaf spot',
                    'Tobacco caterpillar','Whiteflies']
    
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
                 embedding_model: str = "multi-qa-MiniLM-L6-cos-v1",
                 max_tokens: int = 700,
                 top_p: float = 0.9,
                #  intfloat/multilingual-e5-large-instruct
                 # embedding_model: str = "multi-qa-MiniLM-L6-cos-v1",
                 collections_to_init: Optional[List[str]] = None,
                #  persist_directory: str = "./chroma_capstone_db_new"
                 persist_directory: str = "./chroma_capstone_db_new_small2"):
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
        self._initialize_llm(llm_name, temperature,max_tokens=max_tokens,top_p = top_p)
        
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

    def _initialize_llm(self, llm_name: str, temperature: float,max_tokens:int,top_p:float):
        """Initialize the LLM with proper configuration."""
        logger.debug("Initializing LLM...")
        # ollama_host = os.getenv("OLLAMA_HOST")
        # logger.debug(f"OLLAMA_HOST={ollama_host}")

        # if ollama_host:
        self.llm = ChatOllama(
            # model=os.getenv("OLLAMA_MODEL", llm_name),
            model = llm_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p = top_p
            # base_url=ollama_host,
            # reasoning=False  # Disable reasoning for performance
        )
        logger.info(f"✅ Using Ollama model: {self.llm.model}")
        # else:
        #     logger.error("OLLAMA_HOST not set.")
        #     raise RuntimeError(
        #         "No chat model configured. Set OLLAMA_HOST (and optionally OLLAMA_MODEL) or run Ollama and set OLLAMA_MODEL."
        #     )

    def _initialize_all_collections(self):
        """Pre-initialize ChromaDB and retrievers for all specified collections."""
        successful_collections = []

        # if using the docker container, client must be considered if you are running container in port 8000
        # chroma_client = chromadb.HttpClient(host="localhost", port=8000)

        for collection_name in self.collections_to_init:
            try:
                logger.info(f"🔧 Initializing collection: {collection_name}")

                # IF USING DOCKER PULL THE IMAGE amit1994/chromadb_small:latest
                # USING PERSIST DIRECTORY THEN TAKE FROM GOOGLE DRIVE https://drive.google.com/drive/u/0/folders/1vM6zUKWw-AhbEef4_KbRSJwc80vloXcf. The name is chroma_capstone_db_new_small.zip
                # Initialize ChromaDB for this collection
                chroma_db = Chroma(
                    # client = chroma_client,
                    persist_directory=self.persist_directory,
                    embedding_function=self.embedding,
                    collection_name=collection_name,

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
    
    # season: Optional[str]
    def _build_metadata_filter(self, location: Optional[str], disease: Optional[str]) -> Optional[Dict]:
        """
        Build metadata filter dictionary for ChromaDB search.
        ChromaDB requires exactly one top-level operator, so multiple conditions must be wrapped in $and.
        
        Args:
            season: Season filter (Summer, Winter, Kharif, Rabi, etc.)
            location: Location filter (State/District name)
            disease: Disease name filter
            
        Returns:
            Metadata filter dictionary or None if no filters
        """
        conditions = []
        
        # if season:
        #     # Handle common season variations
        #     season_lower = season.lower()
        #     if season_lower in ['summer', 'kharif', 'monsoon']:
        #         season_variations = ['Summer', 'Kharif', 'KHARIF', 'summer', 'Monsoon']
        #     elif season_lower in ['winter', 'rabi', 'cold']:
        #         season_variations = ['Winter', 'Rabi', 'RABI', 'winter', 'Cold']
        #     else:
        #         season_variations = [season, season.capitalize(), season.upper()]
            
        #     conditions.append({"Season_English": {"$in": season_variations}})
        #     logger.debug(f"🌱 Season filter: {season_variations}")
        
        if location:
            # Create flexible location matching (try StateName first, most common)
            location_variations = [
                location, 
                location.capitalize(), 
                location.upper(),
                location.title()
            ]
            # For simplicity, filter by StateName (can be extended later for DistrictName)
            conditions.append({"StateName": {"$in": location_variations}})
            logger.debug(f"📍 Location filter (StateName): {location_variations}")
        
        if disease:
            # Handle disease name variations
            disease_variations = [
                disease,
                disease.capitalize(), 
                disease.upper(),
                disease.title(),
                disease.lower().replace('_', ' ').title(),  # Handle Black_rot -> Black Rot
                disease.lower().replace(' ', '_')           # Handle Black Rot -> black_rot
            ]
            conditions.append({"disease_name": {"$in": disease_variations}})
            logger.debug(f"🦠 Disease filter: {disease_variations}")
        
        # Return None if no conditions
        if not conditions:
            return None
        
        # If only one condition, return it directly (no need for $and)
        if len(conditions) == 1:
            return conditions[0]
        
        # Multiple conditions: wrap in $and operator
        return {"$and": conditions}

    def run_query(self, 
                  query_request: str, 
                  plant_type: Optional[str] = None,
                #   season: Optional[str] = None,
                  location: Optional[str] = None, 
                  disease: Optional[str] = None) -> str:
        """
        Run a query against the appropriate plant-specific collection with metadata filtering.
        
        Args:
            query_request: The query to search for
            plant_type: Optional explicit plant type (overrides auto-detection)
            season: Optional season filter (Summer, Winter, Kharif, Rabi, etc.)
            location: Optional location filter (State/District name)
            disease: Optional disease name filter
            
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
            
            # Get the appropriate ChromaDB instance (not retriever)
            if collection_name not in self.chroma_databases:
                logger.warning(f"⚠️  Collection {collection_name} not available, falling back to {self.default_collection}")
                collection_name = self.default_collection
            
            chroma_db = self.chroma_databases[collection_name]
            retrieval_qa = self.retrievers[collection_name]

            logger.debug(f"🔍 Querying collection: {collection_name}")
            
            # Build metadata filter
            metadata_filter = self._build_metadata_filter(location, disease)
            if metadata_filter:
                logger.info(f"🎯 Using metadata filters: {metadata_filter}")

            logger.info("Please check this part of code")
            # Execute query using RetrievalQA chain with metadata filtering support
            if metadata_filter:
                logger.info("🎯 Using metadata-filtered RetrievalQA")
                
                # Create a temporary retriever with metadata filter for this query
                filtered_retriever = chroma_db.as_retriever(
                    search_type="mmr",
                    search_kwargs={
                        "k": 6, 
                        "fetch_k": 12,
                        "filter": metadata_filter
                    }
                )
                
                # Create a temporary RetrievalQA with the filtered retriever
                filtered_retrieval_qa = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff", 
                    retriever=filtered_retriever,
                    input_key="query",
                    return_source_documents=True,
                    chain_type_kwargs=self.chain_type_kwargs,
                )
                
                # Execute the query with metadata filtering
                result = filtered_retrieval_qa.invoke({"query": query_request})

                print("the result here",result)
                answer = result
                
                # Check if we got meaningful results
                if not result.get("source_documents"):
                    logger.warning("⚠️  No documents found with metadata filters, trying without filters...")
                    # Fallback to standard RetrievalQA chain
                    result = retrieval_qa.invoke({"query": query_request})
                    answer = result["result"]
                else:
                    logger.info(f"✅ Found {len(result['source_documents'])} documents with metadata filter")
                    
            else:
                # Use RetrievalQA chain for standard queries
                logger.info("🔍 Using RetrievalQA chain for similarity search")
                result = retrieval_qa.invoke({"query": query_request})
                answer = result["result"]
            
            if metadata_filter and 'result' in locals() and result.get("source_documents"):
                logger.info(f"✅ Query completed successfully using collection: {collection_name} with {len(result['source_documents'])} filtered documents")
            else:
                logger.info(f"✅ Query completed successfully using collection: {collection_name} via RetrievalQA chain")
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Error during query execution: {e}")
            # Try fallback to default collection using RetrievalQA
            logger.info(f"🔄 Attempting fallback to default collection using RetrievalQA...")
            try:
                fallback_retrieval_qa = self.retrievers[self.default_collection]
                result = fallback_retrieval_qa.invoke({"query": query_request})
                answer = result["result"]
                logger.info("✅ Fallback RetrievalQA query completed successfully")
                return answer
                    
            except Exception as fallback_error:
                logger.error(f"❌ Fallback query also failed: {fallback_error}")
            
            raise RuntimeError(f"RAG query failed: {e}")

    def get_available_collections(self) -> List[str]:
        """Get list of successfully initialized collections."""
        return list(self.chroma_databases.keys())
    
    def test_metadata_filtering(self, query_request: str, 
                               plant_type: Optional[str] = None,
                            #    season: Optional[str] = None,
                               location: Optional[str] = None,
                               disease: Optional[str] = None) -> Dict[str, any]:
        """
        Test metadata filtering by returning filtered documents and metadata filter used.
        Useful for debugging and verifying filter functionality.
        
        Args:
            query_request: The query to search for
            plant_type: Optional explicit plant type
            season: Optional season filter
            location: Optional location filter
            disease: Optional disease name filter
            
        Returns:
            Dictionary containing filtered documents, metadata filter, and collection info
        """
        try:
            # Determine collection
            if plant_type and plant_type in self.chroma_databases:
                collection_name = plant_type
            else:
                collection_name = self._detect_plant_type(query_request)
            
            if collection_name not in self.chroma_databases:
                collection_name = self.default_collection
                
            chroma_db = self.chroma_databases[collection_name]
            
            # Build metadata filter 
            # season
            metadata_filter = self._build_metadata_filter(location, disease)
            
            # Test with and without filtering for comparison
            docs_unfiltered = chroma_db.similarity_search(query_request, k=6)
            
            docs_filtered = []
            if metadata_filter:
                docs_filtered = chroma_db.similarity_search(
                    query_request, 
                    k=6, 
                    filter=metadata_filter
                )
            
            return {
                "collection_used": collection_name,
                "metadata_filter": metadata_filter,
                "docs_unfiltered_count": len(docs_unfiltered),
                "docs_filtered_count": len(docs_filtered) if metadata_filter else 0,
                "docs_unfiltered": [{"content": doc.page_content[:200], "metadata": doc.metadata} for doc in docs_unfiltered],
                "docs_filtered": [{"content": doc.page_content[:200], "metadata": doc.metadata} for doc in docs_filtered] if metadata_filter else [],
                "query": query_request
            }
            
        except Exception as e:
            logger.error(f"❌ Error during metadata filter testing: {e}")
            raise RuntimeError(f"Metadata filter test failed: {e}")
    
    def query_with_sources(self, query_request: str, 
                          plant_type: Optional[str] = None,
                        #   season: Optional[str] = None,
                          location: Optional[str] = None,
                          disease: Optional[str] = None) -> Dict[str, any]:
        """
        Run a query and return both answer and source documents with metadata filtering support.
        
        Args:
            query_request: The query to search for
            plant_type: Optional explicit plant type
            season: Optional season filter
            location: Optional location filter
            disease: Optional disease name filter
            
        Returns:
            Dictionary containing 'result' and 'source_documents'
        """
        try:
            # Determine which collection to use
            if plant_type and plant_type in self.chroma_databases:
                collection_name = plant_type
                logger.debug(f"🎯 Using explicit plant type: {plant_type}")
            else:
                collection_name = self._detect_plant_type(query_request)
            
            if collection_name not in self.retrievers:
                logger.warning(f"⚠️  Collection {collection_name} not available, falling back to {self.default_collection}")
                collection_name = self.default_collection
            
            chroma_db = self.chroma_databases[collection_name]
            retrieval_qa = self.retrievers[collection_name]
            
            # Build metadata filter season
            metadata_filter = self._build_metadata_filter(location, disease)
            
            logger.debug(f"🔍 Querying collection: {collection_name} with source documents")
            
            # Use RetrievalQA chain with metadata filtering if applicable
            if metadata_filter:
                logger.info("🎯 Using metadata-filtered RetrievalQA for sources")
                
                # Create filtered retriever
                filtered_retriever = chroma_db.as_retriever(
                    search_type="mmr",
                    search_kwargs={
                        "k": 6,
                        "fetch_k": 12,
                        "filter": metadata_filter
                    }
                )
                
                # Create temporary filtered RetrievalQA
                filtered_retrieval_qa = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=filtered_retriever,
                    input_key="query",
                    return_source_documents=True,
                    chain_type_kwargs=self.chain_type_kwargs,
                )
                
                result = filtered_retrieval_qa.invoke({"query": query_request})
            else:
                # Use standard RetrievalQA chain
                result = retrieval_qa.invoke({"query": query_request})
            
            logger.info(f"✅ Query with sources completed successfully using collection: {collection_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error during query with sources: {e}")
            raise RuntimeError(f"RAG query with sources failed: {e}")

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
    

# ollama_object = OllamaRag(llm_name="llama3.1:8b")

ollama_object = OllamaRag("llama3.1:8b",max_tokens=600,top_p=0.9)

question = "give me the cure for Tomato plant for Aphids disease"

response = ollama_object.run_query(query_request="give me the cure for Tomato plant for Aphids disease",plant_type="Tomato",location="ASSAM",disease="Aphids")


context = [output.page_content for output in response["source_documents"]]

async def main():

    rag_eval = RAG_Evaluation(question=question,response=response["result"],retrieved_contexts=context,llm="gpt-4.1-nano")

    await rag_eval.evaluate_faithfulness()
    await rag_eval.evaluate_response_relevance()
    await rag_eval.evaluate_aspect_critic()
    await rag_eval.context_precision()

    rag_eval.log_single_turn_sample()

asyncio.run(main())

# print("the response",response)

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
