
```bash
podman pull --arch=arm64  ghcr.io/mlflow/mlflow:latest
podman tag ghcr.io/mlflow/mlflow:latest mlflow:arm64-latest
podman pull --arch=amd64  ghcr.io/mlflow/mlflow:latest
podman tag ghcr.io/mlflow/mlflow:latest mlflow:amd64-latest
```

```bash
podman images
REPOSITORY               TAG           IMAGE ID      CREATED         SIZE
localhost/mlflow-server  arm64-v1      0c340f7e530f  10 minutes ago  896 MB
localhost/mlflow         arm64-latest  66da5010a45d  3 days ago      896 MB
localhost/mlflow         amd64-latest  61bcc4c8fa4b  3 days ago      910 MB
ghcr.io/mlflow/mlflow    latest        61bcc4c8fa4b  3 days ago      910 MB
```



```bash
podman build --platform linux/arm64 --build-arg BASE_TAG=arm64-latest -t mlflow-server:arm64-v1 -f Containerfile.mlflow .
podman build --platform linux/amd64 --build-arg BASE_TAG=amd64-latest -t mlflow-server:amd64-v1 -f Containerfile.mlflow .
```

```bash
podman tag localhost/mlflow-server:amd64-v1 quay.io/rajivranjan/mlflow-server:amd64-v1
podman push quay.io/rajivranjan/mlflow-server:amd64-v1
```


```bash
podman run -it --rm \
    --name mlflow-server \
    --platform linux/arm64 \
    -p 5001:5001 \
    -v ./mlflow-data:/mlruns \
    mlflow-server:arm64-v1
```

```bash
mlflow server --help
Usage: mlflow server [OPTIONS]

  Run the MLflow tracking server.

  The server listens on http://localhost:5000 by default and only accepts
  connections from the local machine. To let the server accept connections
  from other machines, you will need to pass ``--host 0.0.0.0`` to listen on
  all network interfaces (or a specific interface address).

Options:
  --backend-store-uri PATH        URI to which to persist experiment and run
                                  data. Acceptable URIs are SQLAlchemy-
                                  compatible database connection strings (e.g.
                                  'sqlite:///path/to/file.db') or local
                                  filesystem URIs (e.g.
                                  'file:///absolute/path/to/directory'). By
                                  default, data will be logged to the ./mlruns
                                  directory.
  --registry-store-uri URI        URI to which to persist registered models.
                                  Acceptable URIs are SQLAlchemy-compatible
                                  database connection strings (e.g.
                                  'sqlite:///path/to/file.db'). If not
                                  specified, `backend-store-uri` is used.
  --default-artifact-root URI     Directory in which to store artifacts for
                                  any new experiments created. For tracking
                                  server backends that rely on SQL, this
                                  option is required in order to store
                                  artifacts. Note that this flag does not
                                  impact already-created experiments with any
                                  previous configuration of an MLflow server
                                  instance. By default, data will be logged to
                                  the mlflow-artifacts:/ uri proxy if the
                                  --serve-artifacts option is enabled.
                                  Otherwise, the default location will be
                                  ./mlruns.
  --serve-artifacts / --no-serve-artifacts
                                  Enables serving of artifact uploads,
                                  downloads, and list requests by routing
                                  these requests to the storage location that
                                  is specified by '--artifacts-destination'
                                  directly through a proxy. The default
                                  location that these requests are served from
                                  is a local './mlartifacts' directory which
                                  can be overridden via the '--artifacts-
                                  destination' argument. To disable artifact
                                  serving, specify `--no-serve-artifacts`.
                                  Default: True
  --artifacts-only                If specified, configures the mlflow server
                                  to be used only for proxied artifact
                                  serving. With this mode enabled,
                                  functionality of the mlflow tracking service
                                  (e.g. run creation, metric logging, and
                                  parameter logging) is disabled. The server
                                  will only expose endpoints for uploading,
                                  downloading, and listing artifacts. Default:
                                  False
  --artifacts-destination URI     The base artifact location from which to
                                  resolve artifact upload/download/list
                                  requests (e.g. 's3://my-bucket'). Defaults
                                  to a local './mlartifacts' directory. This
                                  option only applies when the tracking server
                                  is configured to stream artifacts and the
                                  experiment's artifact root location is http
                                  or mlflow-artifacts URI.
  -h, --host HOST                 The network address to listen on (default:
                                  127.0.0.1). Use 0.0.0.0 to bind to all
                                  addresses if you want to access the tracking
                                  server from other machines.
  -p, --port INTEGER              The port to listen on (default: 5000).
  -w, --workers TEXT              Number of worker processes to handle
                                  requests (default: 4).
  --static-prefix TEXT            A prefix which will be prepended to the path
                                  of all static paths.
  --gunicorn-opts TEXT            Additional command line options forwarded to
                                  gunicorn processes.
  --waitress-opts TEXT            Additional command line options for
                                  waitress-serve.
  --uvicorn-opts TEXT             Additional command line options forwarded to
                                  uvicorn processes (used by default).
  --expose-prometheus TEXT        Path to the directory where metrics will be
                                  stored. If the directory doesn't exist, it
                                  will be created. Activate prometheus
                                  exporter to expose metrics on /metrics
                                  endpoint.
  --app-name [basic-auth]         Application name to be used for the tracking
                                  server. If not specified,
                                  'mlflow.server:app' will be used.
  --dev                           If enabled, run the server with debug
                                  logging and auto-reload. Should only be used
                                  for development purposes. Cannot be used
                                  with '--gunicorn-opts' or '--uvicorn-opts'.
                                  Unsupported on Windows.
  --help                          Show this message and exit.

```

### Metrics that we want to capture for all incoming requests
There are multiple metrics that we can track and capture.
MLflow's `mlflow.evaluate` function for RAG-plus-LLM generative AI responses allows for capturing a variety of metrics, which can be broadly categorized into two types:
1. `Heuristic-based Metrics`: These are traditional, statistical or rule-based metrics that assess specific aspects of the generated text. Examples include:
    1. **Rouge (Recall-Oriented Understudy for Gisting Evaluation)**: Measures the overlap of n-grams between the generated text and a reference text, often used to assess summarization quality. MLflow provides `mlflow.metrics.rougeL()`.
    1. **BLEU (Bilingual Evaluation Understudy)**: Measures the similarity between a candidate translation and a set of reference translations, useful for evaluating machine translation or text generation where a clear reference exists. MLflow provides `mlflow.metrics.bleu()`.
    1. **Flesch Kincaid Grade Level**: Estimates the readability of text, indicating the approximate grade level required to understand it. MLflow provides `mlflow.metrics.flesch_kincaid_grade_level()`.
    1. **Perplexity**: Measures how well a language model predicts a sample of text, indicating its fluency and coherence.
    1. **Embedding Similarity**: Measures the semantic similarity between the generated response and the ground truth or source documents using embedding models.
2. `LLM-as-a-Judge Metrics`: These leverage the capabilities of other LLMs to evaluate the quality of the generated responses, offering a more nuanced and human-like assessment. MLflow provides built-in LLM-as-a-Judge metrics and also allows for creating custom ones. These can evaluate aspects like: 
Coherence: How well the generated text flows and makes sense as a whole.
Relevance: How well the generated response addresses the user's query and the provided context.
Factuality/Grounding: Whether the generated information is accurate and supported by the retrieval augmented generation (RAG) context.
Completeness: Whether the response provides sufficient information to answer the query.
Conciseness: Whether the response is free of unnecessary verbosity.
Safety/Harmfulness: Assessing for any potentially harmful, biased, or inappropriate content.
Custom Metrics: You can define custom LLM-as-a-Judge metrics with specific prompts, grading criteria, and reference examples to evaluate unique aspects relevant to your application.


MLflow's evaluation framework for RAG (Retrieval-Augmented Generation) and LLM-based (Large Language Model) GenAI responses supports a wide variety of metrics. These include both built-in and custom options, such as heuristic-based metrics (e.g., ROUGE, BLEU, Flesch Kincaid), LLM-as-a-judge scoring (e.g., Relevance, Groundedness), as well as system and performance metrics like latency and cost. The following provides an overview of the main metrics you can capture and how to use them in Python code.

### Built-in Metrics for LLM & RAG Evaluation

- **Heuristic-based metrics**: These classic NLP metrics do not require an LLM as judge. Supported out-of-the-box:
  - ROUGE scores (`rougeL`, etc.)
  - BLEU scores (`bleu`)
  - Flesch Kincaid (`flesch_kincaid_grade_level`)
- **LLM-as-a-Judge metrics**: LLM generates a judgment, often using a chain-of-thought rationale.
  - Answer Relevance
  - Groundedness (for RAG)
  - Chunk Relevance (for RAG)
  - Guideline Adherence (checklist-based)
  - Safety (checks for toxicity, refusal, etc.)
  - Correctness (requires ground truth)
- **System metrics**:
  - Latency (response time)
  - Cost (usage/cost metrics)
- **Custom metrics**: You can define custom metric functions, including invoking external scoring scripts or specialized logic[1][2][3].

### Python Example: Evaluating GenAI with All Metrics

Here's an example using MLflow's newer APIs to evaluate a RAG or LLM app across the major metric types:

```python
import mlflow
from mlflow.genai.scorers import (
    RelevanceToQuery, 
    Groundedness, 
    ChunkRelevance, 
    Safety, 
    GuidelineAdherence
)
from mlflow.genai.heuristics import (
    RougeL, 
    Bleu, 
    FleschKincaidGradeLevel
)

# Define your GenAI app
@mlflow.trace
def my_chatbot_app(question: str) -> dict:
    # Implement the GenAI logic (your LLM, RAG system, etc)
    response = ... # obtain response
    return {"response": response}

# Evaluation dataset (list of dicts, or DataFrame, etc)
data = [
    {"inputs": {"question": "What is MLflow?"}},
    {"inputs": {"question": "Explain RAG."}}
    # add more records
]

# Define scorers (metrics)
scorers = [
    RelevanceToQuery(),        # LLM as judge - relevance
    Groundedness(),            # For RAG - groundedness
    ChunkRelevance(),          # RAG: passage relevance
    Safety(),                  # Safety metric
    GuidelineAdherence(),      # Customizable
    RougeL(),                  # Heuristic
    Bleu(),                    # Heuristic
    FleschKincaidGradeLevel()  # Readability
]

# Run evaluation
results = mlflow.genai.evaluate(
    data=data,
    predict_fn=my_chatbot_app,
    scorers=scorers,
)

# Optional: Extract system metrics
latency = results.metrics.get("latency/mean", None)      # mean latency
cost = results.metrics.get("cost/total", None)           # total cost

# Access detailed per-question results
per_question_results = results.tables['eval_results']
```
This code runs all key metrics available out-of-the-box on a typical RAG or GenAI app using MLflow's evaluate functions. You can expand or swap out scorers as desired, combine both string-based metric names and scorer classes, and add custom scorers[3][2][1].

### Supported Metrics Overview

| Metric Category         | Example Metrics          | Requires LLM-Judge | Notes                                |
|------------------------|-------------------------|--------------------|--------------------------------------|
| Heuristic/NLP Metrics  | ROUGE, BLEU, FK Grade   | No                 | For summarization, translation, etc. |
| LLM Judge Metrics      | Relevance, Groundedness | Yes                | Evaluates unstructured outputs       |
| Agent/RAG-Specific     | Chunk Relevance         | Yes                | Assesses source retrieval matches    |
| Guideline/Checklist    | Guideline Adherence     | Yes/No             | Customizable template checks         |
| System                 | Latency, Cost           | No                 | Automatically captured               |
| Safety/Correctness     | Safety, Correctness     | Yes/No             | Toxicity, truthful answers           |

You can find official scorer class names and new metric documentation in MLflow 2.8/3.0+ docs for Databricks, Azure, and other providers[2][3][1].

### Summary

- MLflow supports a rich set of **heuristic**, **LLM-as-a-judge**, and **system** metrics for GenAI and RAG evaluation[1][2][3].
- Metrics are extensible; you may mix built-in scorers with custom Python logic.
- Direct integration as shown above provides actionable insights for LLM response evaluation and benchmarking[1][2][3].

Sources
[1] Evaluating LLM with MLFlow https://docs.cloudera.com/machine-learning/cloud/experiments/topics/ml-mlflow-evaluate-llm.html
[2] Run an evaluation and view the results (MLflow 2) https://docs.databricks.com/aws/en/generative-ai/agent-evaluation/evaluate-agent
[3] Evaluation harness - Azure Databricks https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/concepts/eval-harness
[4] Announcing MLflow 2.8: LLM Judge Metrics https://www.databricks.com/blog/announcing-mlflow-28-llm-judge-metrics-and-best-practices-llm-evaluation-rag-applications-part
[5] Evaluating RAG with LLM-as-a-Judge: A Guide to ... https://www.nb-data.com/p/evaluating-rag-with-llm-as-a-judge
[6] Mosaic AI Agent Evaluation (MLflow 2) - Azure Databricks https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-evaluation/
[7] Custom Metrics Comprehensive Example(Python) https://www.databricks.com/wp-content/uploads/notebooks/custom-metrics-comprehensive-example.html
[8] MLflow 3 for GenAI | Databricks on AWS https://docs.databricks.com/aws/en/mlflow3/genai/
[9] Log metrics, parameters, and files with MLflow https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-view-metrics?view=azureml-api-2
