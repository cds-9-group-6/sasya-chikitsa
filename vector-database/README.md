# Use vector database

We are using Chromadb as vector database. There are two different flavours of it:
* Chromadb with data preloaded
* Empty Chromadb where the user needs to mount the suitable data.

## How to run the vector database in the local 

* based on the chip arch pull one of the available image:
  * for macbook
  
  ```bash 
  podman pull quay.io/rajivranjan/chromadb-with-data-arm64:v1
  ```

  * for non-macbook
  ```bash
  podman pull quay.io/rajivranjan/chromadb-with-data-amd64:v1
  ```

  * for Docker 
  ```bash
  docker pull amit1994/chromadb_small
  ```

  ```bash
  docker run -p 8000:8000 amit1994/chromadb_small
  ```

  ```bash
  python test_chromadb.py
  ```

* test the connectivity and data collection

```bash
podman run -p 8000:8000 quay.io/rajivranjan/chromadb-with-data-arm64:v1

python test_chromadb.py
```


## Explore what other options are there instead of large E5 multilingual model
Options are:
|embedding model |langauge support |Disk Size|dimensions|Retrieval Accuracy (1)|Domain Specificity|Context Length (2)|Normalization|Build Vs Buy|Inference Speed|Throughput|GPU/CPU/RAM (3)|Embedding data size|Container Image Size|
|--|--|--|--|--|--|--|--|--|--|--|--|--|--|
|intfloat/multilingual-e5-large-instruct|100+|2.3 Gb|1024|||||||||973M|1.6G|
|BAAI/bge-large-en-v1.5|English only|1.3Gb|1024|||||||||1.5G|2.2G|
|all-mpnet-base-v2|English only|438Mb|768||||||||||
|text-embedding-3-small|TBD|API call|1536||||||||||
|text-embedding-3-large|TBD|API call|3072||||||||||

(1) MTEB (Massive Text Embedding Benchmark): 
  * https://huggingface.co/spaces/mteb/leaderboard
  * https://www.anyscale.com/blog/choosing-your-embedding-model
  * https://www.pinecone.io/learn/sentence-embeddings/
  * https://www.google.com/search?q=https://txt.cohere.com/embedding-models/

(2) Max Sequence Length

(3) Optimizations like ONNX or quantizing the model
## Which LLM models will support multi lingual

* AI4Bharat's Ganga Model Family
  * Why it's a good choice: Developed by an Indian research lab, AI4Bharat, these models are built specifically for the Indian context. They are trained and fine-tuned on vast amounts of Indian language data, making them exceptionally good at understanding cultural nuances, regional terms, and code-mixing (e.g., "Hinglish").
  * Best for: The most culturally and linguistically nuanced understanding, full data privacy, and control, with no API costs. It's the top choice for an India-centric, self-hosted solution.
  * Type: Open-Source

* Google Gemini 1.5 Pro
  * Why it's a good choice: As the latest model from Google, Gemini 1.5 Pro has state-of-the-art multilingual capabilities. Google has a long history of investing in and supporting Indian languages across its products (Search, Translate, etc.), and this expertise is reflected in the model. It also features a massive 1 million token context window, which is extremely useful for RAG systems that might retrieve many documents.
  * Best for: Cutting-edge performance, handling massive amounts of retrieved context, and benefiting from Google's deep expertise in Indian languages.
  * Type: Proprietary API

* OpenAI GPT-4o
  * Why it's a good choice: GPT-4o is OpenAI's flagship model and the industry benchmark for quality. It has incredibly strong reasoning and generation capabilities across dozens of languages, including all the major Indian languages. Its "omni" capabilities mean it's particularly adept at understanding and producing natural, human-like text.
  * Best for: Overall high-quality, reliable, and fluent responses with a massive developer ecosystem for support.
  * Type: Proprietary API
