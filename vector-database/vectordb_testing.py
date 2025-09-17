# All imports are done here
import time
import logging
import csv
import pandas as pd
import mlflow
import mlflow.metrics
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging  
import torch
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
import os
from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
import subprocess
import sys

# All initialization is done here
load_dotenv()
LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH")
HUB_MODEL_ID = os.getenv("HUB_MODEL_ID")
LOCAL_VECTOR_DB_PATH = os.getenv("LOCAL_VECTOR_DB_PATH")
device = os.getenv("DEVICE") if os.getenv("DEVICE") else "cpu"
embedding = None
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")


# setup the logging
logging.basicConfig(
    level=logging.INFO,  # Set the minimum level of messages to display
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# find and set the accelerator device
if torch.cuda.is_available():
    device = "cuda"
    logging.info("Found NVIDIA GPU, using 'cuda' as the device.")
    logging.info(f"CUDA device count: {torch.cuda.device_count()}")
elif torch.backends.mps.is_available():
    device = "mps"
    logging.info("Found Apple Silicon GPU, using 'mps' as the device.")
    logging.info(f"MPS device count: 1")
else:
    device = "cpu"
    logging.warning("No GPU found, falling back to 'cpu'. This will be slower.")
    logging.info(f"CPU device count: {torch.device_count()}")


# load the model from local path if available
if os.path.isdir(LOCAL_MODEL_PATH):
    logging.info(f"✅ Loading model from local path: {LOCAL_MODEL_PATH}")
    model_to_use = LOCAL_MODEL_PATH
else:
    logging.warning(
        f"⚠️ Local model not found at {LOCAL_MODEL_PATH}. Downloading from Hub: {HUB_MODEL_ID}"
    )
    

    # Install huggingface_hub if needed
    try:
        subprocess.run(
            [sys.executable, "-m", "uv", "add", "huggingface_hub[cli]"], check=True
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install huggingface_hub: {e}")

    # Download model from hub
    try:
        subprocess.run(
            ["hf", "download", HUB_MODEL_ID, "--local-dir", LOCAL_MODEL_PATH],
            check=True,
        )
        logging.info(f"Successfully downloaded model to {LOCAL_MODEL_PATH}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to download model: {e}")

    model_to_use = LOCAL_MODEL_PATH


try:
    embedding = HuggingFaceEmbeddings(
        model_name=model_to_use, model_kwargs={"device": device}
    )
    logging.info("Embedding model loaded successfully.")
except Exception as e:
    logging.error(f"Failed to load embedding model: {e}")
    embedding = None
logging.info(f"embedding: {embedding}")


chroma_db = Chroma(
    persist_directory=LOCAL_VECTOR_DB_PATH,
    embedding_function=embedding,
    collection_name="Tomato",  # Specify which collection to load
)


retriever = chroma_db.as_retriever(
    search_type="mmr", search_kwargs={"k": 3, "fetch_k": 6}
)


class ChromaDBPerformanceMonitor:
    """
    Enhanced real-time performance monitoring for ChromaDB queries with logging, CSV export, and MLflow integration
    """

    def __init__(
        self,
        window_size: int = 100,
        csv_file: str = "chromadb_performance.csv",
        log_level: int = logging.INFO,
        mlflow_experiment_name: str = "ChromaDB_Performance",
    ):
        self.window_size = window_size
        self.query_times = deque(maxlen=window_size)
        self.query_history = []
        self.csv_file = Path(csv_file)

        # Setup logging
        self._setup_logging(log_level)

        # Setup CSV file
        self._setup_csv_file()

        # Setup MLflow
        self.mlflow_experiment_name = mlflow_experiment_name
        self._setup_mlflow()

        self.logger.info(f"ChromaDB Performance Monitor initialized")
        self.logger.info(f"CSV file: {self.csv_file}")
        self.logger.info(f"MLflow experiment: {self.mlflow_experiment_name}")

    def _setup_logging(self, log_level: int):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger("ChromaDBMonitor")
        self.logger.setLevel(log_level)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        # File handler
        file_handler = logging.FileHandler("chromadb_performance.log")
        file_handler.setLevel(log_level)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def _setup_csv_file(self):
        """Setup CSV file with headers if it doesn't exist"""
        if not self.csv_file.exists():
            headers = [
                "timestamp",
                "session_id",
                "query_id",
                "question",
                "query_time",
                "doc_count",
                "search_type",
                "search_kwargs",
                "metadata",
                "avg_time_window",
                "min_time_window",
                "max_time_window",
            ]

            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

            self.logger.info(f"Created new CSV file: {self.csv_file}")
        else:
            self.logger.info(f"Using existing CSV file: {self.csv_file}")

    def _setup_mlflow(self):
        """Setup MLflow experiment"""
        try:
            # Set or create experiment
            mlflow.set_experiment(self.mlflow_experiment_name)
            self.logger.info(f"MLflow experiment set: {self.mlflow_experiment_name}")

            # Generate session ID for this monitor instance
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        except Exception as e:
            self.logger.error(f"Failed to setup MLflow: {e}")
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def timed_query(
        self,
        retriever: VectorStoreRetriever,
        question: str,
        metadata: Optional[Dict] = None,
        log_query: bool = True,
    ) -> tuple:
        """
        Execute query with timing and store results
        """
        timestamp = datetime.now()
        query_id = len(self.query_history) + 1

        if log_query:
            self.logger.info(f"Executing query {query_id}: {question[:50]}...")

        start_time = time.perf_counter()

        try:
            docs = retriever.invoke(question)
            success = True
            error_msg = None
        except Exception as e:
            docs = []
            success = False
            error_msg = str(e)
            self.logger.error(f"Query {query_id} failed: {error_msg}")

        end_time = time.perf_counter()
        query_time = end_time - start_time

        # Store timing data
        self.query_times.append(query_time)

        # Extract retriever configuration
        search_type = getattr(retriever, "search_type", "similarity")
        search_kwargs = getattr(retriever, "search_kwargs", {})
        # allowed_search_types = getattr(retriever, 'allowed_search_types', [])
        metadata = getattr(retriever, "metadata", {})
        model_config = getattr(retriever, "model_config", {})
        # name=getattr(retriever, 'name', '')
        # collection_name=getattr(retriever, 'collection_name', '')
        # vectorstore=getattr(retriever, 'vectorstore', '')
        # index=getattr(retriever, 'index', '')
        # embedding=getattr(retriever, 'embedding', '')
        # distance_func=getattr(retriever, 'distance_func', '')
        # distance_func_kwargs=getattr(retriever, 'distance_func_kwargs', {})
        # search_params=getattr(retriever, 'search_params', {})
        # k=getattr(retriever, 'k', 10)
        fetch_k = getattr(retriever, "fetch_k", 20)
        # score_threshold=getattr(retriever, 'score_threshold', 0.5)
        # filter=getattr(retriever, 'filter', {})
        # filter_kwargs=getattr(retriever, 'filter_kwargs', {})

        query_record = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "query_id": query_id,
            "question": question,
            "query_time": query_time,
            "doc_count": len(docs),
            "search_type": search_type,
            "search_kwargs": search_kwargs,
            "metadata": metadata or {},
            "model_config": model_config or {},
            # "allowed_search_types": allowed_search_types or [],
            # "name": name or '',
            # "collection_name": collection_name or '',
            # "vectorstore": vectorstore or '',
            # "index": index or '',
            "embedding": embedding or "",
            # "distance_func": distance_func or '',
            # "distance_func_kwargs": distance_func_kwargs or {},
            # "search_params": search_params or {},
            # "k": k or 10,
            "fetch_k": fetch_k or 20,
            # "score_threshold": score_threshold or 0.5,
            # "filter": filter or {},
            # "filter_kwargs": filter_kwargs or {},
            "success": success,
            "error_msg": error_msg,
        }
        self.query_history.append(query_record)

        # Log results
        if success:
            self.logger.info(
                f"Query {query_id} completed: {query_time:.4f}s, {len(docs)} docs retrieved"
            )

        # Save to CSV
        self._save_to_csv(query_record)

        # Log to MLflow
        self._log_to_mlflow(query_record)

        return docs, query_record

    def _save_to_csv(self, query_record: Dict):
        """Save query record to CSV file"""
        try:
            # Calculate window statistics
            recent_times = list(self.query_times)
            window_stats = {
                "avg_time_window": sum(recent_times) / len(recent_times)
                if recent_times
                else 0,
                "min_time_window": min(recent_times) if recent_times else 0,
                "max_time_window": max(recent_times) if recent_times else 0,
            }

            with open(self.csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        query_record["timestamp"].isoformat(),
                        query_record["session_id"],
                        query_record["query_id"],
                        query_record["question"],
                        query_record["query_time"],
                        query_record["doc_count"],
                        query_record["search_type"],
                        json.dumps(query_record["search_kwargs"]),
                        json.dumps(query_record["metadata"]),
                        window_stats["avg_time_window"],
                        window_stats["min_time_window"],
                        window_stats["max_time_window"],
                    ]
                )

        except Exception as e:
            self.logger.error(f"Failed to save to CSV: {e}")

    def _log_to_mlflow(self, query_record: Dict):
        """Log query metrics to MLflow"""
        try:
            with mlflow.start_run(run_name=f"query_{query_record['query_id']}"):
                # Log parameters
                mlflow.log_param("session_id", query_record["session_id"])
                mlflow.log_param("query_id", query_record["query_id"])
                mlflow.log_param("question_length", len(query_record["question"]))
                mlflow.log_param("search_type", query_record["search_type"])
                mlflow.log_param(
                    "search_kwargs", json.dumps(query_record["search_kwargs"])
                )
                mlflow.log_param("hub_model_id", HUB_MODEL_ID)
                mlflow.log_param("local_model_path", LOCAL_MODEL_PATH)
                mlflow.log_param("local_vector_db_path", LOCAL_VECTOR_DB_PATH)
                mlflow.log_param("device", device)
                # Log metrics
                mlflow.log_metric("query_time", query_record["query_time"])
                mlflow.log_metric("doc_count", query_record["doc_count"])
                mlflow.log_metric("success", 1 if query_record["success"] else 0)

                if query_record["doc_count"] > 0:
                    mlflow.log_metric(
                        "time_per_doc",
                        query_record["query_time"] / query_record["doc_count"],
                    )

                # Log window statistics
                recent_times = list(self.query_times)
                if len(recent_times) > 1:
                    mlflow.log_metric(
                        "window_avg_time", sum(recent_times) / len(recent_times)
                    )
                    mlflow.log_metric("window_min_time", min(recent_times))
                    mlflow.log_metric("window_max_time", max(recent_times))

                # Log metadata as tags
                if query_record["metadata"]:
                    for key, value in query_record["metadata"].items():
                        mlflow.set_tag(f"metadata_{key}", str(value))

                # Log question as artifact (for longer questions)
                with open("temp_question.txt", "w") as f:
                    f.write(query_record["question"])
                mlflow.log_artifact("temp_question.txt", "questions")

        except Exception as e:
            self.logger.error(f"Failed to log to MLflow: {e}")

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get current performance statistics with timestamp"""
        if not self.query_times:
            return None

        recent_times = list(self.query_times)
        current_time = datetime.now()

        stats = {
            "timestamp": current_time,
            "session_id": self.session_id,
            "total_queries": len(self.query_history),
            "recent_queries": len(recent_times),
            "avg_time": sum(recent_times) / len(recent_times),
            "min_time": min(recent_times),
            "max_time": max(recent_times),
            "queries_per_second": 1 / (sum(recent_times) / len(recent_times)),
            "last_query_time": recent_times[-1] if recent_times else None,
            "success_rate": sum(1 for q in self.query_history if q.get("success", True))
            / len(self.query_history),
        }

        return stats

    def print_stats(self):
        """Print current performance statistics with logging"""
        stats = self.get_stats()
        if not stats:
            self.logger.warning("No queries executed yet")
            return

        # Log timestamp when stats are requested
        timestamp_str = stats["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        self.logger.info("=" * 60)
        self.logger.info(f"📈 ChromaDB Performance Stats - {timestamp_str}")
        self.logger.info(f"Session ID: {stats['session_id']}")
        self.logger.info("=" * 60)
        self.logger.info(f"Window size: {stats['recent_queries']} queries")
        self.logger.info(f"Average query time: {stats['avg_time']:.4f}s")
        self.logger.info(f"Fastest query: {stats['min_time']:.4f}s")
        self.logger.info(f"Slowest query: {stats['max_time']:.4f}s")
        self.logger.info(f"Queries per second: {stats['queries_per_second']:.2f}")
        self.logger.info(f"Total queries: {stats['total_queries']}")
        self.logger.info(f"Success rate: {stats['success_rate']:.2%}")
        self.logger.info("=" * 60)

        # Also log these stats to MLflow
        self._log_window_stats_to_mlflow(stats)

    def _log_window_stats_to_mlflow(self, stats: Dict):
        """Log window statistics to MLflow"""
        try:
            with mlflow.start_run(run_name=f"window_stats_{stats['session_id']}"):
                mlflow.log_param("stats_type", "window_summary")
                mlflow.log_param("session_id", stats["session_id"])
                mlflow.log_param("timestamp", stats["timestamp"].isoformat())

                mlflow.log_metric("total_queries", stats["total_queries"])
                mlflow.log_metric("window_avg_time", stats["avg_time"])
                mlflow.log_metric("window_min_time", stats["min_time"])
                mlflow.log_metric("window_max_time", stats["max_time"])
                mlflow.log_metric("queries_per_second", stats["queries_per_second"])
                mlflow.log_metric("success_rate", stats["success_rate"])

        except Exception as e:
            self.logger.error(f"Failed to log window stats to MLflow: {e}")

    def export_to_dataframe(self) -> pd.DataFrame:
        """Export query history to pandas DataFrame"""
        if not self.query_history:
            self.logger.warning("No query history to export")
            return pd.DataFrame()

        # Flatten the data for DataFrame
        data = []
        for record in self.query_history:
            row = {
                "timestamp": record["timestamp"],
                "session_id": record["session_id"],
                "query_id": record["query_id"],
                "question": record["question"],
                "query_time": record["query_time"],
                "doc_count": record["doc_count"],
                "search_type": record["search_type"],
                "search_kwargs": json.dumps(record["search_kwargs"]),
                "success": record.get("success", True),
                "error_msg": record.get("error_msg", ""),
            }

            # Add metadata fields
            if record["metadata"]:
                for key, value in record["metadata"].items():
                    row[f"metadata_{key}"] = value

            data.append(row)

        df = pd.DataFrame(data)
        self.logger.info(f"Exported {len(df)} records to DataFrame")
        return df

    def save_summary_report(self, filename: Optional[str] = None):
        """Save a comprehensive summary report"""
        if filename is None:
            filename = f"chromadb_summary_{self.session_id}.json"

        stats = self.get_stats()
        if not stats:
            self.logger.warning("No data to save in summary report")
            return

        summary = {
            "session_info": {
                "session_id": self.session_id,
                "start_time": self.query_history[0]["timestamp"].isoformat()
                if self.query_history
                else None,
                "end_time": stats["timestamp"].isoformat(),
                "total_queries": stats["total_queries"],
            },
            "performance_stats": {
                "avg_query_time": stats["avg_time"],
                "min_query_time": stats["min_time"],
                "max_query_time": stats["max_time"],
                "queries_per_second": stats["queries_per_second"],
                "success_rate": stats["success_rate"],
            },
            "configuration": {
                "window_size": self.window_size,
                "csv_file": str(self.csv_file),
                "mlflow_experiment": self.mlflow_experiment_name,
            },
        }

        with open(filename, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        self.logger.info(f"Summary report saved: {filename}")


def setup_mlflow_dashboard():
    """
    Setup MLflow with custom metrics for ChromaDB monitoring
    """

    # Start MLflow server (run this in terminal)
    dashboard_command = """
    # Run this in your terminal to start MLflow UI:
    mlflow ui --host 0.0.0.0 --port 5000
    
    # Then access at: http://localhost:5000
    """

    print("MLflow Dashboard Setup:")
    print(dashboard_command)
    # !uv add mlflow
    # !mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri=file:$(pwd)/mlruns

    # subprocess.run(["uv", "add", "mlflow"], check=True)
    # subprocess.run(
    #     [
    #         "mlflow",
    #         "server",
    #         "--host",
    #         "0.0.0.0",
    #         "--port",
    #         "8989",
    #         f"--backend-store-uri=file:{os.getcwd()}/mlruns",
    #     ],
    #     check=False,
    # )

    mlflow.set_tracking_uri(uri="http://0.0.0.0:8989")
    # mlflow.set_experiment("vector-database-testing")

    # Custom metrics for MLflow
    def log_custom_metrics():
        with mlflow.start_run(run_name="chromadb_custom_metrics"):
            # Log system info
            import platform
            import psutil

            mlflow.log_param("system", platform.system())
            mlflow.log_param("python_version", platform.python_version())
            mlflow.log_param("cpu_count", psutil.cpu_count())
            mlflow.log_param("memory_gb", psutil.virtual_memory().total / (1024**3))
            

    return log_custom_metrics


# Setup MLflow dashboard
setup_mlflow_dashboard()
# Usage Example


def main():
    """Example usage of the enhanced monitor"""

    # Initialize monitor
    monitor = ChromaDBPerformanceMonitor(
        window_size=50,
        csv_file="chromadb_performance_detailed.csv",
        log_level=logging.INFO,
        mlflow_experiment_name="ChromaDB_Agricultural_Queries",
    )

    # Sample questions for testing
    questions = [
        "Apple tree disease management techniques",
        "Rice paddy bacterial blight symptoms",
        "Coconut palm red weevil control methods",
        "Organic pesticide application for fruit trees",
        "Crop yield improvement strategies",
        "Fungal infection prevention in agricultural crops",
    ]

    # Execute queries with monitoring
    for i, question in enumerate(questions):
        metadata = {
            "batch_id": "test_batch_1",
            "question_category": "agricultural_disease",
            "question_number": i + 1,
        }

        docs, record = monitor.timed_query(retriever, question, metadata=metadata)

        # Print stats every 3 queries
        if (i + 1) % 3 == 0:
            monitor.print_stats()

    # Final statistics
    monitor.print_stats()

    # Export data
    df = monitor.export_to_dataframe()
    df.to_csv(f"query_history_{monitor.session_id}.csv", index=False)

    # Save summary report
    monitor.save_summary_report()

    monitor.logger.info("Monitoring session completed")


# Initialize with your retriever
# monitor = ChromaDBPerformanceMonitor(
#     csv_file="my_chromadb_performance.csv",
#     mlflow_experiment_name="My_ChromaDB_Experiment"
# )

# Execute queries
# docs, record = monitor.timed_query(retriever, "your question", metadata={"batch": "production"})

# Get stats with timestamp and logging
# monitor.print_stats()

# View results in MLflow UI at http://localhost:5000

# Run the example
if __name__ == "__main__":
    main()
