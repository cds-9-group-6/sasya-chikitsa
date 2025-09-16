import os
import json
from sklearn.metrics import precision_score, recall_score, f1_score

def log_metrics(metrics, log_dir, timestamp, evaluation_type):
    """Log evaluation metrics to a JSON file."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{evaluation_type}_metrics_{timestamp}.json")
    with open(log_file, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"✅ Metrics logged to: {log_file}")

def evaluate_retrieval(y_true, y_pred, log_dir, timestamp, evaluation_type="retrieval"):
    """Evaluate retrieval metrics and log results."""
    precision = precision_score(y_true, y_pred, average="binary")
    recall = recall_score(y_true, y_pred, average="binary")
    f1 = f1_score(y_true, y_pred, average="binary")

    metrics = {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
    }

    log_metrics(metrics, log_dir, timestamp, evaluation_type)
    return metrics

def evaluate_retrieval_by_crop(data, crop, log_dir, timestamp):
    """Evaluate retrieval for a specific crop."""
    filtered_data = [d for d in data if d["crop"] == crop]
    y_true = [d["relevant"] for d in filtered_data]
    y_pred = [d["retrieved"] for d in filtered_data]
    return evaluate_retrieval(y_true, y_pred, log_dir, timestamp, evaluation_type=f"retrieval_{crop}")

def evaluate_retrieval_by_crop_disease(data, crop, disease, log_dir, timestamp):
    """Evaluate retrieval for a specific crop+disease combination."""
    filtered_data = [d for d in data if d["crop"] == crop and d["disease"] == disease]
    y_true = [d["relevant"] for d in filtered_data]
    y_pred = [d["retrieved"] for d in filtered_data]
    return evaluate_retrieval(y_true, y_pred, log_dir, timestamp, evaluation_type=f"retrieval_{crop}_{disease}")