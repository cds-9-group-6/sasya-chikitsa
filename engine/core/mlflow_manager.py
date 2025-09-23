"""
MLflow Manager for Classification System

This module handles MLflow initialization, experiment setup, and metric tracking
for the plant disease classification system.
"""

import os
import logging
from typing import Dict, Any, Optional
import mlflow
from mlflow import MlflowClient
from dotenv import load_dotenv
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class MLflowManager:
    """
    Manages MLflow integration for classification metrics tracking
    Uses a single persistent run for the agent lifetime
    """
    
    def __init__(self):
        self.client: Optional[MlflowClient] = None
        self.experiment_id: Optional[str] = None
        self.experiment_name: Optional[str] = None
        self.persistent_run_id: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Load MLflow configuration from environment variables"""
        try:
            # Load .env file
            env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
            load_dotenv(env_path)
            
            # Get MLflow configuration
            self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
            self.experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "plant_disease_classification")
            self.artifact_location = os.getenv("MLFLOW_ARTIFACT_LOCATION", "./mlflow_artifacts")
            self.registry_uri = os.getenv("MLFLOW_REGISTRY_URI", "http://localhost:5000")
            
            logger.info(f"MLflow configuration loaded: URI={self.tracking_uri}, Experiment={self.experiment_name}")
            
        except Exception as e:
            logger.error(f"Failed to load MLflow configuration: {e}")
            # Use defaults
            self.tracking_uri = "http://localhost:5000"
            self.experiment_name = "plant_disease_classification"
            self.artifact_location = "./mlflow_artifacts"
            self.registry_uri = "http://localhost:5000"
    
    def initialize(self) -> bool:
        """
        Initialize MLflow connection and setup experiment
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Set MLflow configuration
            mlflow.set_tracking_uri(self.tracking_uri)
            if self.registry_uri:
                mlflow.set_registry_uri(self.registry_uri)
            
            # Test connection first with a short timeout
            try:
                # Initialize client with connection test
                self.client = MlflowClient(tracking_uri=self.tracking_uri)
                
                # Test connection by trying to list experiments with timeout
                import requests
                
                # Quick connectivity test
                test_url = f"{self.tracking_uri.rstrip('/')}/health" if "//" in self.tracking_uri else None
                if test_url:
                    response = requests.get(test_url, timeout=2)
                
            except Exception as connection_error:
                logger.warning(f"MLflow server not accessible at {self.tracking_uri}: {connection_error}")
                logger.info("MLflow will be disabled - classification will continue without metrics tracking")
                return False
            
            # Create or get experiment
            try:
                experiment = mlflow.get_experiment_by_name(self.experiment_name)
                if experiment is None:
                    self.experiment_id = mlflow.create_experiment(
                        name=self.experiment_name,
                        artifact_location=self.artifact_location
                    )
                    logger.info(f"Created new MLflow experiment: {self.experiment_name} (ID: {self.experiment_id})")
                else:
                    self.experiment_id = experiment.experiment_id
                    logger.info(f"Using existing MLflow experiment: {self.experiment_name} (ID: {self.experiment_id})")
                
                # Set the experiment
                mlflow.set_experiment(self.experiment_name)
                
                # Start persistent run for the agent
                self._start_persistent_run()
                
                # Enable automatic LangChain tracing to the persistent run
                self._enable_langchain_autolog()
                
                logger.info("MLflow manager initialized successfully with persistent run and LangChain autolog")
                return True
                
            except Exception as e:
                logger.warning(f"Failed to setup MLflow experiment: {e}")
                logger.info("MLflow will be disabled - classification will continue without metrics tracking")
                return False
                
        except Exception as e:
            logger.warning(f"Failed to initialize MLflow manager: {e}")
            logger.info("MLflow will be disabled - classification will continue without metrics tracking")
            return False
    
    def _start_persistent_run(self) -> Optional[str]:
        """
        Start a persistent MLflow run for the agent lifetime
        
        Returns:
            Run ID if successful, None otherwise
        """
        try:
            import datetime
            
            run_name = f"agent_run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            run = mlflow.start_run(
                run_name=run_name,
                experiment_id=self.experiment_id
            )
            
            # Log agent metadata
            mlflow.set_tag("run_type", "agent_persistent")
            mlflow.set_tag("agent_start_time", datetime.datetime.now().isoformat())
            
            self.persistent_run_id = run.info.run_id
            logger.info(f"Started persistent MLflow run: {self.persistent_run_id}")
            return self.persistent_run_id
            
        except Exception as e:
            logger.error(f"Failed to start persistent MLflow run: {e}")
            return None
    
    def _enable_langchain_autolog(self):
        """
        Enable MLflow LangChain autologging to capture traces automatically
        """
        try:
            # Enable LangChain autologging to capture all LangChain operations
            # Use simplest call for maximum compatibility
            mlflow.langchain.autolog()
            
            logger.info("✅ MLflow LangChain autolog enabled - will capture workflow traces")
            
        except Exception as e:
            logger.warning(f"Failed to enable LangChain autolog: {e}")
            logger.info("Continuing without automatic trace logging")
    
    def ensure_active_run(self) -> bool:
        """
        Ensure we have an active persistent run
        
        Returns:
            True if active run exists, False otherwise
        """
        try:
            active_run = mlflow.get_run(self.persistent_run_id)
            if active_run is None:
                logger.warning("No active MLflow run, restarting persistent run")
                return self._start_persistent_run() is not None
            return True
        except Exception as e:
            logger.error(f"Failed to ensure active run: {e}")
            return False
    
    def log_classification_metrics(self, 
                                 session_id: str,
                                 cnn_result: Dict[str, Any], 
                                 llava_result: Dict[str, Any],
                                 final_result: Dict[str, Any],
                                 similarity_score: Optional[float] = None):
        """
        Log comprehensive classification metrics
        
        Args:
            session_id: Session identifier
            cnn_result: CNN classification results
            llava_result: LLaVA classification results
            final_result: Final classification decision
            similarity_score: Disease name similarity score
        """
        try:
            # Ensure we have an active persistent run
            if not self.ensure_active_run():
                logger.error("No active MLflow run available")
                return
            
            import time
            step = int(time.time())  # Use timestamp as step for time-series metrics
            # Log session context - this helps identify which session the metrics belong to
            mlflow.set_tag(f"session_{session_id}_processed", "true")
            
            # Log final result metrics with session context
            mlflow.log_metric("final_confidence",
                              final_result.get("confidence", 0.0),
                              run_id=self.persistent_run_id,
                              step=step)
            mlflow.log_metric("classification_count",
                              1.0,
                              run_id=self.persistent_run_id,
                              step=step)  # Count of classifications
            
            # Log categorical data as tags/params (not time-series)
            mlflow.set_tag(f"session_{session_id}_disease", final_result.get("disease_name", "unknown"))
            mlflow.set_tag(f"session_{session_id}_source", final_result.get("source", "unknown"))
            
            # Log CNN metrics
            if not cnn_result.get("error"):
                cnn_confidence = cnn_result.get("confidence", 0.0)
                mlflow.log_metric("cnn_confidence",
                                  cnn_confidence,
                                  run_id=self.persistent_run_id,
                                  step=step)
                mlflow.set_tag(f"session_{session_id}_cnn_disease", cnn_result.get("disease_name", "unknown"))
                
                # Calculate and log CNN entropy
                cnn_entropy = self._calculate_entropy(cnn_confidence)
                mlflow.log_metric("cnn_entropy",
                                  cnn_entropy,
                                  run_id=self.persistent_run_id,
                                  step=step)
                mlflow.log_metric("cnn_uncertainty",
                                  1.0 - cnn_confidence,
                                  run_id=self.persistent_run_id,
                                  step=step)
            
            # Log LLaVA metrics
            if not llava_result.get("error"):
                llava_confidence = llava_result.get("confidence", 0.0)
                mlflow.log_metric("llava_confidence",
                                  llava_confidence,
                                  run_id=self.persistent_run_id,
                                  step=step)
                mlflow.set_tag(f"session_{session_id}_llava_disease", llava_result.get("disease_name", "unknown"))
                mlflow.set_tag(f"session_{session_id}_llava_severity", llava_result.get("severity", "unknown"))
                
                # Calculate prediction margin (difference between CNN and LLaVA confidences)
                if not cnn_result.get("error"):
                    prediction_margin = abs(cnn_confidence - llava_confidence)
                    mlflow.log_metric("prediction_margin",
                                      prediction_margin,
                                      run_id=self.persistent_run_id,
                                      step=step)
                    
                    # Log confidence ratio
                    if llava_confidence > 0:
                        confidence_ratio = cnn_confidence / llava_confidence
                        mlflow.log_metric("confidence_ratio",
                                          confidence_ratio,
                                          run_id=self.persistent_run_id,
                                          step=step)
            
            # Log similarity metrics
            if similarity_score is not None:
                mlflow.log_metric("disease_name_similarity",
                                  similarity_score,
                                  run_id=self.persistent_run_id,
                                  step=step)
                mlflow.log_metric("similarity_binary",
                                  1.0 if similarity_score >= 0.6 else 0.0,
                                  run_id=self.persistent_run_id,
                                  step=step)
            
            # Log decision logic
            is_unknown = final_result.get("source") == "sme"
            mlflow.log_metric("cnn_unknown_trigger",
                              1.0 if is_unknown else 0.0,
                              run_id=self.persistent_run_id,
                              step=step)
            
            # Log system availability
            mlflow.log_metric("llava_available",
                              1.0 if not llava_result.get("error") else 0.0,
                              run_id=self.persistent_run_id,
                              step=step)
            mlflow.log_metric("cnn_available",
                              1.0 if not cnn_result.get("error") else 0.0,
                              run_id=self.persistent_run_id,
                              step=step)
            
            logger.info(f"Logged classification metrics for session: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to log classification metrics: {e}")
    
    def _calculate_entropy(self, confidence: float) -> float:
        """
        Calculate entropy from confidence score
        
        Args:
            confidence: Confidence score between 0 and 1
            
        Returns:
            Entropy value
        """
        try:
            # Convert confidence to probability distribution
            # Assuming binary classification: [confidence, 1-confidence]
            if confidence <= 0 or confidence >= 1:
                return 0.0
            
            probs = np.array([confidence, 1.0 - confidence])
            # Calculate entropy: -sum(p * log2(p))
            entropy = stats.entropy(probs, base=2)
            return float(entropy)
            
        except Exception as e:
            logger.error(f"Error calculating entropy: {e}")
            return 0.0
    
    def log_error(self, session_id: str, error_type: str, error_message: str):
        """
        Log error information to the persistent run
        
        Args:
            session_id: Session identifier
            error_type: Type of error (cnn_error, llava_error, etc.)
            error_message: Error description
        """
        try:
            # Ensure we have an active persistent run
            if not self.ensure_active_run():
                logger.error("No active MLflow run available for error logging")
                return
            
            import time
            step = int(time.time())
            
            mlflow.set_tag(f"session_{session_id}_error_{error_type}", error_message)
            mlflow.log_metric(f"{error_type}_count", 1.0, step=step)
            mlflow.log_metric("error_count", 1.0, step=step)  # General error counter
            
            logger.info(f"Logged error for session {session_id}: {error_type}")
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    def end_persistent_run(self):
        """
        End the persistent MLflow run (called when agent shuts down)
        """
        try:
            # Disable LangChain autolog
            try:
                mlflow.langchain.autolog(disable=True)
                logger.info("Disabled MLflow LangChain autolog")
            except Exception as e:
                logger.warning(f"Failed to disable LangChain autolog: {e}")
            
            if mlflow.active_run():
                import datetime
                mlflow.set_tag("agent_end_time", datetime.datetime.now().isoformat())
                mlflow.end_run()
                logger.info("Ended persistent MLflow run")
                self.persistent_run_id = None
        except Exception as e:
            logger.error(f"Failed to end persistent MLflow run: {e}")
    
    def end_run(self):
        """
        DEPRECATED: Use end_persistent_run() instead
        Kept for backward compatibility
        """
        logger.warning("end_run() is deprecated - use end_persistent_run() for agent shutdown")
        # Don't end the persistent run for individual operations
    
    def is_available(self) -> bool:
        """Check if MLflow is available and properly initialized"""
        try:
            return (
                self.client is not None and 
                self.experiment_id is not None and
                self.tracking_uri is not None
            )
        except:
            return False


# Global MLflow manager instance
_mlflow_manager: Optional[MLflowManager] = None


def get_mlflow_manager() -> MLflowManager:
    """
    Get the global MLflow manager instance
    
    Returns:
        MLflowManager instance
    """
    global _mlflow_manager
    if _mlflow_manager is None:
        _mlflow_manager = MLflowManager()
        _mlflow_manager.initialize()
    return _mlflow_manager


def initialize_mlflow() -> bool:
    """
    Initialize MLflow for the application
    
    Returns:
        bool: True if initialization successful
    """
    try:
        manager = get_mlflow_manager()
        return manager.is_available()
    except Exception as e:
        logger.error(f"Failed to initialize MLflow: {e}")
        return False
