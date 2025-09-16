"""
System Evaluation Module

Provides functions to evaluate the overall performance of a RAG system.
"""

import os
import json
import time


def log_metrics(metrics, log_dir, timestamp, evaluation_type):
    """Log evaluation metrics to a JSON file."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{evaluation_type}_metrics_{timestamp}.json")
    with open(log_file, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"✅ Metrics logged to: {log_file}")


def evaluate_latency(start_time, end_time, log_dir, timestamp):
    """Evaluate system latency and log results."""
    latency = end_time - start_time
    metrics = {"latency": latency}
    log_metrics(metrics, log_dir, timestamp, evaluation_type="system_latency")
    return metrics


def evaluate_user_satisfaction(survey_results, log_dir, timestamp):
    """
    Evaluate user satisfaction based on survey results and log results.
    Survey results should be a list of scores (e.g., 1-5).
    """
    if not survey_results:
        raise ValueError("Survey results cannot be empty.")
    average_satisfaction = sum(survey_results) / len(survey_results)
    metrics = {"user_satisfaction": average_satisfaction}
    log_metrics(metrics, log_dir, timestamp, evaluation_type="user_satisfaction")
    return metrics


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Run system evaluation.")
    parser.add_argument("--log-dir", type=str, required=True, help="Directory to save evaluation logs.")
    parser.add_argument("--timestamp", type=str, required=True, help="Timestamp for log files.")
    args = parser.parse_args()

    # Simulate latency evaluation
    print("🔍 Evaluating system latency...")
    start_time = time.time()
    time.sleep(1.5)  # Simulate some processing delay
    end_time = time.time()
    evaluate_latency(start_time, end_time, args.log_dir, args.timestamp)

    # Simulate user satisfaction evaluation
    print("🔍 Evaluating user satisfaction...")
    survey_results = [4, 5, 3, 4, 5]  # Example survey results
    evaluate_user_satisfaction(survey_results, args.log_dir, args.timestamp)

    print("🎉 System evaluation completed!")