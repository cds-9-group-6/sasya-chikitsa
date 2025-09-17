import pandas as pd
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate,PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os

print("Pointing to Ollama server...")

ollama_host = os.getenv("OLLAMA_HOST")
print(f"DEBUG: in rag_with_ollama_fastapi.py file OLLAMA_HOST={ollama_host}")

if ollama_host:
    llm = ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"), temperature=0.1, base_url=ollama_host, reasoning=False)
else:
    print("OLLAMA_HOST not set, using default local settings")
    # llm = ChatOllama(model="llama3.1:8b", temperature=0.1)
    raise RuntimeError(
        "No chat model configured. Set OPENAI_API_KEY (and optionally OPENAI_MODEL) or run Ollama and set OLLAMA_MODEL."
    )

# print(f"Using model: {llm.model_name}")

# llm = ChatOllama(
#             temperature=1, 
#             model_name="llama-3.1-8b",
#             max_tokens=600,
#             top_p=0.90,
#         #     frequency_penalty=1,
#         #     presence_penalty=1,
#     )

print("Creating prompt template...")
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
PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)
chain_type_kwargs = {"prompt": PROMPT}

print("Loading ChromaDB and setting up retriever...")
embedding = HuggingFaceEmbeddings( #model_name="intfloat/multilingual-e5-large-instruct",
                                  model_name = "multi-qa-MiniLM-L6-cos-v1",
                                #   model_kwargs={"device": "mps"}
                                  )
chroma_db = Chroma(
    # persist_directory="./chroma_capstone_db_new",
    persist_directory= "./chroma_capstone_db_new_small",
    embedding_function=embedding,
    collection_name="Tomato"  # Specify which collection to load
)

chroma_retriever = chroma_db.as_retriever(search_type="mmr", search_kwargs={"k": 6, "fetch_k":12})

# chroma_retriever.get_relevant_documents(question)

print("Setting up RetrievalQA chain...")
h_retrieval_QA1 = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=chroma_retriever,
    input_key="query",
    return_source_documents=True,
    chain_type_kwargs=chain_type_kwargs
)

app = FastAPI()


class Queryrequest(BaseModel):
    query:str

@app.get("/")
def root():
    return {"message": "Hello, World"}


@app.post("/ask")
def run_query(request:Queryrequest):
    answer = h_retrieval_QA1.invoke({"query": request.query})["result"]
    return answer

if __name__ == "__main__":
    uvicorn.run("rag_with_ollama_fastapi:app", host="0.0.0.0", port=5050, reload=True)