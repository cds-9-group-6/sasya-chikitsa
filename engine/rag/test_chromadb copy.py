import chromadb
import os
from chromadb.config import Settings

# import chromadb.utils.embedding_functions as embedding_functions
# from langchain_huggingface import HuggingFaceEmbeddings



# chroma_client = chromadb.HttpClient(host='0.0.0.0', port=8000)
# chroma_client = chromadb.HttpClient(host="localhost", port=8000)
# chroma_client = chromadb.HttpClient(host="http://chromadb-with-data-amd64-sasya-chikitsa.apps.cluster-mx6z7.mx6z7.sandbox5315.opentlc.com", port=80)

chroma_client = chromadb.HttpClient(
    host="localhost",
    port=8000,
    settings=Settings(allow_reset=True, anonymized_telemetry=False)
)

print("ChromaDB heartbeat:", chroma_client.heartbeat())
print("Available collections:", chroma_client.list_collections())
chroma_client.heartbeat()
print("ChromaDB client connected successfully.")

print("Available collections:", chroma_client.list_collections())

collection = chroma_client.get_collection(name="Apple")

# Run a query (this will use whatever embeddings were stored in that collection)
results = collection.query(
    query_texts=["How to treat apple diseases?"],  # list of query strings
    n_results=3  # number of most similar results
)

print("Query results:", results)

# embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
#     model_name="intfloat/multilingual-e5-large-instruct",
#     # If you have a GPU, you can specify the device, otherwise it defaults to CPU
#     # device="mps" 
# )

# embedding = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large-instruct",model_kwargs={"device": "mps"})
# embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
#     model_name="intfloat/multilingual-e5-large-instruct"
# )

# Expected Collections in the database:
# Paddy_Dhan
# Tomato
# try:
#     collection_name = "Tomato"
#     collection = chroma_client.get_collection(name=collection_name, embedding_function=embedding_func)
#     collection.count()
#     print(f"Collection '{collection_name}' accessed successfully.")
#     print(f"Number of items in the collection: {collection.count()}")

#     # 4. Perform a query.
#     results = collection.query(query_texts=["tomato diseases"], n_results=5)

#     print("\nQuery Results:")
#     print(results)

# except ValueError as e:
#     print(f"\nError getting collection: {e}")
#     print(
#         "Please make sure the collection name is correct and it exists in the database."
#     )
#     print("Check the 'Available collections' list printed above.")
