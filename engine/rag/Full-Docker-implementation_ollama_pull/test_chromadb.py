import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Create the FastAPI app instance
app = FastAPI()

# chroma_client = chromadb.HttpClient(host='0.0.0.0', port=8000)
chroma_client = chromadb.HttpClient(host="chroma-small", port=8000)

print("ChromaDB heartbeat:", chroma_client.heartbeat())
print("Available collections:", chroma_client.list_collections())

print("ChromaDB client connected successfully.")

# using a small embedding here
embedding = HuggingFaceEmbeddings(model_name="multi-qa-MiniLM-L6-cos-v1")

# Define LLM 
                #   host="ollama-app", port=11434)

# llm = ChatGroq(
#             temperature=1, 
#             groq_api_key = os.environ["GROQ_API_KEY"], 
#             model_name="llama-3.1-8b-instant",
#             max_tokens=600,
#             top_p=0.90,
#         #     frequency_penalty=1,
#         #     presence_penalty=1,
#     )

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

class Queryrequest(BaseModel):

    question:str
    collections:str

@app.post("/ask")
def run_query(request:Queryrequest):

    collection = chroma_client.get_collection(name=request.collections)

    print("collections:", collection)


    chroma_db = Chroma(
        client=chroma_client,          # use the running client
        collection_name="Apple",       # choose which collection to query
        embedding_function=embedding
    )

    retriever = chroma_db.as_retriever(search_type="mmr", search_kwargs={"k": 5, "fetch_k": 10})

    llm = ChatOllama(model="llama3.1:8b", temperature=0.7, max_tokens=512, base_url="http://ollama-app:11434")

    PROMPT = PromptTemplate(input_variables=["context", "question"], template=prompt_template)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True
    )


    print("using llm",llm)


    answer = qa_chain.invoke({"query": request.question})["result"]

    return answer


# if __name__ == "__main__":

#     uvicorn.run("test_chromadb:app", host="0.0.0.0", port=5000, reload=True)
 
# Run query
# query = "How do I control Alternaria leaf blotch in apple?"
# result = qa_chain.invoke({"query": query})

# print("Answer:", result["result"])
# print("Sources:", result["source_documents"])