# Retrieval-Augmented Generation (RAG)

This repository contains notebooks for creating embeddings, building a vector database, and running RAG (Retrieval-Augmented Generation) using both **Groq API** and **Hugging Face**.  

---

## 📂 Files in this Repository  

### 1. `Embedding_creation.ipynb`  
- Handles preprocessing of cleaned data.  
- Creates embeddings.  
- Inserts chunks into the vector database for retrieval.  

---

### 2. `Rag_with_groq.ipynb`  
- Runs the RAG pipeline using the **Groq API**.  
- Requires a **Groq API key**:  
  - You can create one by signing up at [Groq](https://groq.com).  
  - An existing API key is already placed in the **Amit** folder of the shared drive inside the `.env` file.  
- Requires the **`chroma_capstone_db_new`** vector database.  
- ✅ To run this notebook:  
  1. Place the `.env` file in the same folder.  
  2. Ensure the vector database is available.  
  3. Execute the notebook cells.  

---

### 3. `Rag_huggingface.ipynb`  
- Similar to `Rag_with_groq.ipynb`.  
- Does **not** require a Groq API key.  
- Simply run the notebook to start the RAG pipeline.  

---

## ⚙️ Requirements  
- Python 3.10+  
- Install dependencies:  
  ```bash
  pip install -r requirements.txt
