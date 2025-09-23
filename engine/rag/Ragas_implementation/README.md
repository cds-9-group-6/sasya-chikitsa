# RAGAS RAG system evaluation

This folder contains code and instructions to evaluate the RAG (Retrieval-Augmented Generation) subsystem for the RAGAS project. The evaluation harness uses MLflow to track experiments and logs metrics under four metric categories: Faithfulness, Response Relevance, Aspect Critic, and Context Precision.

## ⚡️ Requirements

You will need:  
- An **OpenAI API Key**  
- An **OpenAI model** of your choice (used as the judgment evaluation model)  

Install dependencies:  

pip install ragas langchain_openai mlflow

## Metrics Overview

Here four metrics are calculated using context, query and response.

### Faithfulness:

The Faithfulness metric measures how factually consistent a response is with the retrieved context. It ranges from 0 to 1, with higher scores indicating better consistency. Here user_input(question) ,response, retrieved_contexts and evaluator llm are the input parameters.

### Response Relevance:

The ResponseRelevancy metric measures how relevant a response is to the user input. Higher scores indicate better alignment with the user input, while lower scores are given if the response is incomplete or includes redundant information. Here user_input(question), response, retrieved_contexts, evaluator llm and embedding model are the input parameters.

### Aspect Critic:

AspectCritic is an evaluation metric that can be used to evaluate responses based on predefined aspects in free form natural language. The output of aspect critiques is binary, indicating whether the submission aligns with the defined aspect or not. Here user_input(question), response, name for example name="maliciousness" and evaluator llm are the input parameters


### Context Precision:

Context Precision is a metric that evaluates the retriever’s ability to rank relevant chunks higher than irrelevant ones for a given query in the retrieved context. Specifically, it assesses the degree to which relevant chunks in the retrieved context are placed at the top of the ranking. It specifically uses LLMContextPrecisionWithoutReference, here if an irrelevant chunk is present at the second position in the array, context precision remains the same. Here user_input(question) ,response, retrieved_contexts and evaluator llm are the input parameters.


## Code

- All metrics use asyncio (async/await) for execution.

- RAG_Evaluation class implements the metrics.

- log_single_turn_sample logs results to MLflow.


The mlflow_test code: uses RAG_Evaluation class where all the 4 metrics are defined and uses the log_single_turn_sample function to log the experiments into the mlflow server. 

The rag_with_ollama_mod code: integrates the RAG_Evaluation class with the Retriever.

The rag_with_ollama_augmented code: is a modification on the Retriver logic which integrates with the RAG_Evaluation class.


To start the MLflow server run - mlflow ui

Set your OpenAI API key in environment variables:

export OPENAI_API_KEY="your-key-here" or use a .env file