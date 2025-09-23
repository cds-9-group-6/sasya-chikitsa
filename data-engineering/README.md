# 🌾 Crop Disease Q&A Dataset Processing

This project processes **agricultural question-answer datasets** collected across different crops.  
It prepares a **clean, deduplicated, and high-quality dataset** suitable for **Retrieval-Augmented Generation (RAG)** pipelines and **LLM fine-tuning**.

---

## ✨ Features
- 📂 Load multiple crop-specific CSVs from structured folders.
- 🧹 Clean and preprocess dataset:
  - Remove missing/empty answers
  - Convert numeric months → month names
  - Remove duplicates (exact & semantic)
  - Filter rows with only numeric answers
  - Ensure minimum word count for queries/answers
- 🔎 Apply **TF-IDF + cosine similarity** filtering to remove >65% similar Q&A pairs.
-    Apply **Huggignface Embeddings + cosine similarity** filtering to remove >90% similar Q&A pairs.
- 💾 Save final dataset to `filtered_data.csv`.
