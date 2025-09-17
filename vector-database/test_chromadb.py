# import chromadb
# import os
# # import chromadb.utils.embedding_functions as embedding_functions
# # from langchain_huggingface import HuggingFaceEmbeddings



# # chroma_client = chromadb.HttpClient(host='0.0.0.0', port=8000)
# # chroma_client = chromadb.HttpClient(host="localhost", port=8000)
# chroma_client = chromadb.HttpClient(host="http://chromadb-with-data-amd64-sasya-chikitsa.apps.cluster-mx6z7.mx6z7.sandbox5315.opentlc.com", port=80)

# chroma_client.heartbeat()
# print("ChromaDB client connected successfully.")

# print("Available collections:", chroma_client.list_collections())


import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama



# chroma_client = chromadb.HttpClient(host='0.0.0.0', port=8000)
chroma_client = chromadb.HttpClient(host="localhost", port=8000)

print("ChromaDB heartbeat:", chroma_client.heartbeat())
print("Available collections:", chroma_client.list_collections())

print("ChromaDB client connected successfully.")

collection = chroma_client.get_collection(name="Apple")

embedding = HuggingFaceEmbeddings(model_name="multi-qa-MiniLM-L6-cos-v1")

chroma_db = Chroma(
    client=chroma_client,          # use the running client
    collection_name="Apple",       # choose which collection to query
    embedding_function=embedding
)

# Create retriever
retriever = chroma_db.as_retriever(search_type="mmr", search_kwargs={"k": 5, "fetch_k": 10})

# Define LLM
llm = ChatOllama(model_name="llama-3.1-8b", temperature=0.7, max_tokens=512)

# Build RetrievalQA chain
prompt_template = """
You are an agricultural assistant specialized in plant diseases.
Use the following context to answer the user's question.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""
PROMPT = PromptTemplate(input_variables=["context", "question"], template=prompt_template)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": PROMPT},
    return_source_documents=True
)

# Run query
query = "How do I control Alternaria leaf blotch in apple?"
result = qa_chain.invoke({"query": query})

print("Answer:", result["result"])


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
