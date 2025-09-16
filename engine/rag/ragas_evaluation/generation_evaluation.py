import os
import json
from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge

def log_metrics(metrics, log_dir, timestamp, evaluation_type):
    """Log evaluation metrics to a JSON file."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{evaluation_type}_metrics_{timestamp}.json")
    with open(log_file, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"✅ Metrics logged to: {log_file}")

def evaluate_generation(reference, candidate, log_dir, timestamp):
    """Evaluate generation metrics and log results."""
    bleu = sentence_bleu([reference.split()], candidate.split())
    rouge = Rouge().get_scores(candidate, reference)[0]

    metrics = {
        "bleu_score": bleu,
        "rouge_scores": rouge,
    }

    log_metrics(metrics, log_dir, timestamp, evaluation_type="generation")
    return metrics