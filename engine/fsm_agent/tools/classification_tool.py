"""
Classification Tool for LangGraph Workflow

This tool wraps the CNN classification functionality for use in the LangGraph workflow.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional
import requests
import json
import re
from difflib import SequenceMatcher

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# Add the parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from ml.cnn_attn_classifier_improved import CNNWithAttentionClassifier

# MLflow components will be passed by nodes - no need to import or initialize here

logger = logging.getLogger(__name__)


class ClassificationInput(BaseModel):
    """Input schema for classification tool"""
    image_b64: str = Field(description="Base64 encoded image of the plant leaf")
    plant_type: Optional[str] = Field(default=None, description="Type of plant (optional)")
    location: Optional[str] = Field(default=None, description="Location for context (optional)")
    season: Optional[str] = Field(default=None, description="Season for context (optional)")
    growth_stage: Optional[str] = Field(default=None, description="Growth stage (optional)")
    session_id: Optional[str] = Field(default="unknown", description="Session ID for MLflow tracking")


class ClassificationTool(BaseTool):
    """
    Tool for classifying plant diseases from leaf images
    """
    name: str = "plant_disease_classifier"
    description: str = "Classifies plant diseases from leaf images using CNN with attention mechanism"
    args_schema: type[BaseModel] = ClassificationInput
    
    # Declare the classifier field properly
    classifier: Optional[Any] = Field(default=None, exclude=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._load_classifier()
    
    def _load_classifier(self):
        """Load the CNN classifier"""
        try:
            # Initialize classifier (no parameters needed - uses hardcoded paths)
            self.classifier = CNNWithAttentionClassifier()
            logger.info("CNN classifier loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load CNN classifier: {str(e)}")
            self.classifier = None
    
    def _get_llava_evaluation(self, image_b64: str) -> Dict[str, Any]:
        """
        Get disease classification from LLaVA model via Ollama API
        
        Args:
            image_b64: Base64 encoded image
            
        Returns:
            Dictionary with LLaVA evaluation results
        """
        try:
            # Clean base64 string if needed
            clean_image_b64 = image_b64.strip()
            if clean_image_b64.startswith('data:'):
                clean_image_b64 = clean_image_b64.split(',', 1)[1]
            clean_image_b64 = ''.join(clean_image_b64.split())
            
            # Prepare prompt for structured output
            prompt = """Analyze this leaf image for plant diseases. Please provide your analysis in EXACTLY this JSON format:

{
    "disease_name": "specific disease name or 'healthy'",
    "confidence": 0.85,
    "severity": "severe | moderate | low",
    "description": "brief description of what you see"
}

Important:
- If the plant appears healthy, use "healthy" as disease_name
- Confidence should be a decimal between 0.0 and 1.0
- Severity should be one of: severe, moderate, low
- Return ONLY the JSON object, no additional text"""

            # Prepare request to Ollama
            payload = {
                "model": "llava",
                "prompt": prompt,
                "images": [clean_image_b64],
                "stream": False
            }
            
            ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            llava_timeout = int(os.getenv("LLAVA_TIMEOUT", "120"))
            response = requests.post(
                f"{ollama_url}/api/generate",
                json=payload,
                timeout=llava_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get('response', '')
                
                # Try to extract JSON from the response
                json_match = re.search(r'\{[^}]*\}', raw_response.strip(), re.DOTALL)
                if json_match:
                    try:
                        llava_result = json.loads(json_match.group())
                        
                        # Validate and normalize the result
                        normalized_result = {
                            "disease_name": llava_result.get("disease_name", "unknown"),
                            "confidence": float(llava_result.get("confidence", 0.5)),
                            "severity": llava_result.get("severity", "moderate"),
                            "description": llava_result.get("description", "LLaVA analysis completed")
                        }
                        
                        logger.info(f"LLaVA evaluation successful: {normalized_result['disease_name']} ({normalized_result['confidence']:.2f})")
                        return normalized_result
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse LLaVA JSON response: {raw_response}")
                        return {"error": f"Invalid JSON response from LLaVA: {raw_response[:200]}"}
                else:
                    logger.warning(f"No JSON found in LLaVA response: {raw_response}")
                    return {"error": f"No structured response from LLaVA: {raw_response[:200]}"}
            else:
                return {"error": f"LLaVA API error: HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"LLaVA connection error: {str(e)}")
            return {"error": f"LLaVA connection failed: {str(e)}"}
        except Exception as e:
            logger.error(f"LLaVA evaluation error: {str(e)}")
            return {"error": f"LLaVA evaluation failed: {str(e)}"}
    
    def _calculate_disease_similarity(self, disease1: str, disease2: str) -> float:
        """
        Calculate similarity between two disease names
        
        Args:
            disease1: First disease name
            disease2: Second disease name
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not disease1 or not disease2:
            return 0.0
        
        # Normalize names for comparison
        name1 = disease1.lower().strip()
        name2 = disease2.lower().strip()
        
        # Exact match
        if name1 == name2:
            return 1.0
        
        # Check if one contains the other
        if name1 in name2 or name2 in name1:
            return 0.8
        
        # Use sequence matcher for fuzzy matching
        similarity = SequenceMatcher(None, name1, name2).ratio()
        
        # Check for common disease keywords
        common_keywords = ['blight', 'spot', 'rust', 'rot', 'mold', 'virus', 'healthy']
        name1_keywords = [kw for kw in common_keywords if kw in name1]
        name2_keywords = [kw for kw in common_keywords if kw in name2]
        
        if name1_keywords and name2_keywords:
            keyword_overlap = len(set(name1_keywords) & set(name2_keywords)) / max(len(name1_keywords), len(name2_keywords))
            similarity = max(similarity, keyword_overlap * 0.7)
        
        return similarity
    
    def _run_cnn_evaluation(self, image_b64: str, plant_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run CNN classification evaluation
        
        Args:
            image_b64: Base64 encoded image
            plant_context: Plant context information
            
        Returns:
            CNN evaluation results or error
        """
        try:
            input_context = f"Plant: {plant_context.get('plant_type', 'unknown')}, Location: {plant_context.get('location', 'unknown')}, Season: {plant_context.get('season', 'unknown')}"
            
            # Use the complete method that returns all results at once
            cnn_result = self.classifier.predict_leaf_classification_complete(
                image_bytes=image_b64,
                input_text=input_context
            )
            
            # Check for errors from the CNN classifier
            if cnn_result.get("error"):
                return {"error": f"CNN classification failed: {cnn_result['error']}"}
            
            if not cnn_result.get("success"):
                return {"error": "CNN classification failed - unexpected result format"}
                
            return cnn_result
            
        except Exception as e:
            return {"error": f"CNN classification failed: {str(e)}"}
    
    def _compare_and_decide(self, cnn_result: Dict[str, Any], llava_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare CNN and LLaVA results and decide which to use
        
        Args:
            cnn_result: CNN evaluation results
            llava_result: LLaVA evaluation results
            
        Returns:
            Final decision results with source attribution
        """
        # Check if CNN classification is unknown
        cnn_disease_name = cnn_result.get("disease_name", "").lower()
        is_unknown = cnn_disease_name in ["unknown", "uncertain", "unidentified", "not_identified"]
        
        # Check if LLaVA is available
        llava_available = not llava_result.get("error")
        
        # Initialize decision variables
        decision_data = {
            "final_disease_name": None,
            "final_confidence": None,
            "final_severity": None,
            "final_description": None,
            "result_source": None,
            "similarity": None,
            "is_unknown": is_unknown,
            "llava_available": llava_available
        }
        
        # Always calculate similarity for logging if both results available
        if llava_available:
            cnn_disease = cnn_result.get("disease_name", "").lower()
            llava_disease = llava_result.get("disease_name", "").lower()
            decision_data["similarity"] = self._calculate_disease_similarity(cnn_disease, llava_disease)
            
            logger.info(f"Disease comparison - CNN: {cnn_disease}, LLaVA: {llava_disease}, Similarity: {decision_data['similarity']:.2f}")
        
        # Decision logic: Use LLaVA only if CNN is unknown
        if is_unknown and llava_available:
            # CNN returned unknown and LLaVA is available - use LLaVA
            decision_data.update({
                "final_disease_name": llava_result.get("disease_name"),
                "final_confidence": llava_result.get("confidence", 0),
                "final_severity": llava_result.get("severity", "moderate"),
                "final_description": llava_result.get("description", f"Detected {llava_result.get('disease_name')} with {llava_result.get('confidence', 0):.2%} confidence via expert evaluation"),
                "result_source": "sme"
            })
            
            logger.info(f"CNN returned unknown - using LLaVA classification: {decision_data['final_disease_name']} ({decision_data['final_confidence']:.2f})")
            
        elif is_unknown and not llava_available:
            # CNN returned unknown but LLaVA failed - use CNN unknown result
            decision_data.update({
                "final_disease_name": cnn_result.get("disease_name"),
                "final_confidence": cnn_result.get("confidence", 0),
                "final_severity": "moderate",
                "final_description": f"Classification uncertain - CNN confidence: {cnn_result.get('confidence', 0):.2%}. Expert system unavailable.",
                "result_source": "cnn"
            })
            
            logger.warning(f"CNN returned unknown and LLaVA unavailable: {llava_result.get('error', 'Unknown error')}")
            
        else:
            # CNN provided a known classification - use it (regardless of LLaVA availability)
            decision_data.update({
                "final_disease_name": cnn_result.get("disease_name"),
                "final_confidence": cnn_result.get("confidence", 0),
                "final_severity": llava_result.get("severity", "moderate") if llava_available else "moderate",
                "final_description": f"Detected {cnn_result.get('disease_name')} with {cnn_result.get('confidence', 0):.2%} confidence",
                "result_source": "cnn"
            })
            
            if llava_available:
                logger.info(f"Using CNN classification: {decision_data['final_disease_name']} ({decision_data['final_confidence']:.2f}). LLaVA comparison available.")
            else:
                logger.info(f"Using CNN classification: {decision_data['final_disease_name']} ({decision_data['final_confidence']:.2f}). LLaVA unavailable.")
        
        return decision_data
    
    def _format_final_result(self, decision_data: Dict[str, Any], cnn_result: Dict[str, Any], 
                           llava_result: Dict[str, Any], plant_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the final classification result
        
        Args:
            decision_data: Decision data from comparison
            cnn_result: Original CNN results
            llava_result: Original LLaVA results
            plant_context: Plant context information
            
        Returns:
            Formatted final result
        """
        # Determine decision reason
        if decision_data["is_unknown"] and decision_data["llava_available"]:
            decision_reason = "CNN returned unknown - using LLaVA"
        elif decision_data["is_unknown"] and not decision_data["llava_available"]:
            decision_reason = "CNN returned unknown - LLaVA unavailable"
        else:
            decision_reason = "CNN provided valid classification"
        
        formatted_result = {
            "disease_name": decision_data["final_disease_name"],
            "confidence": decision_data["final_confidence"],
            "severity": decision_data["final_severity"],
            "description": decision_data["final_description"],
            "source": decision_data["result_source"],
            "attention_overlay": cnn_result.get("attention_overlay"),  # Always from CNN
            "raw_class_label": cnn_result.get("raw_class_label"),
            "plant_context": plant_context,
            "evaluation_details": {
                "cnn_result": {
                    "disease_name": cnn_result.get("disease_name"),
                    "confidence": cnn_result.get("confidence")
                },
                "llava_result": llava_result if decision_data["llava_available"] else {"error": "LLaVA evaluation failed"},
                "similarity_score": decision_data["similarity"],
                "decision_reason": decision_reason
            }
        }
        
        return formatted_result
    
    async def _arun(self, mlflow_manager=None, **kwargs) -> Dict[str, Any]:
        """Async implementation"""
        return await asyncio.to_thread(self._run, mlflow_manager=mlflow_manager, **kwargs)
    
    def _run(self, mlflow_manager=None, **kwargs) -> Dict[str, Any]:
        """
        Run dual evaluation with both CNN and LLaVA using clean separated logic with MLflow tracking
        
        Args:
            mlflow_manager: MLflow manager instance (passed by node)
            **kwargs: Tool input parameters
        
        Returns:
            Dictionary containing classification results or error
        """
        session_id = kwargs.get("session_id", "unknown")
        
        try:
            # Verify MLflow manager is available (but don't start/end runs)
            if mlflow_manager and not mlflow_manager.is_available():
                logger.warning("MLflow manager not available for metrics logging")
                mlflow_manager = None
            
            # Validate input
            if not kwargs.get("image_b64"):
                error_msg = "No image provided"
                if mlflow_manager:
                    mlflow_manager.log_error(session_id, "validation_error", error_msg)
                return {"error": error_msg}
            
            if not self.classifier:
                error_msg = "CNN classifier not available"
                if mlflow_manager:
                    mlflow_manager.log_error(session_id, "cnn_unavailable", error_msg)
                return {"error": error_msg}
            
            # Prepare plant context
            plant_context = {
                            "plant_type": kwargs.get("plant_type"),
                            "location": kwargs.get("location"),
                            "season": kwargs.get("season"),
                            "growth_stage": kwargs.get("growth_stage")
                        }
            
            # Log plant context to MLflow
            if mlflow_manager:
                try:
                    import mlflow
                    for key, value in plant_context.items():
                        if value:
                            mlflow.log_param(f"plant_{key}", value)
                except Exception as e:
                    logger.warning(f"Failed to log plant context: {e}")
            
            # Run CNN evaluation
            cnn_result = self._run_cnn_evaluation(kwargs["image_b64"], plant_context)
            if cnn_result.get("error"):
                if mlflow_manager:
                    mlflow_manager.log_error(session_id, "cnn_error", cnn_result["error"])
                return cnn_result  # Return CNN error directly
            
            # Run LLaVA evaluation (always for comparison)
            llava_result = self._get_llava_evaluation(kwargs["image_b64"])
            
            # Compare results and make decision
            decision_data = self._compare_and_decide(cnn_result, llava_result)
            
            # Format final result
            final_result = self._format_final_result(decision_data, cnn_result, llava_result, plant_context)
            
            # Log comprehensive metrics to MLflow
            if mlflow_manager:
                try:
                    # Log classification metrics (includes entropy calculation)
                    mlflow_manager.log_classification_metrics(
                        session_id=session_id,
                        cnn_result=cnn_result,
                        llava_result=llava_result,
                        final_result=final_result,
                        similarity_score=decision_data.get("similarity")
                    )
                    
                    # Calculate and log additional metrics
                    try:
                        from engine.core.classification_metrics import ClassificationMetrics
                        import mlflow
                        additional_metrics = ClassificationMetrics.calculate_decision_metrics(
                            cnn_result, llava_result, final_result, decision_data.get("similarity")
                        )
                        

                        for metric_name, metric_value in additional_metrics.items():
                            if isinstance(metric_value, (int, float)):
                                mlflow.log_metric(f"custom_{metric_name}", metric_value)
                            elif isinstance(metric_value, str):
                                mlflow.log_param(f"custom_{metric_name}", metric_value)
                        
                        # Log metric summary
                        summary = ClassificationMetrics.get_metric_summary(additional_metrics)
                        mlflow.log_param("metrics_summary", summary)
                        logger.info(f"MLflow metrics summary: {summary}")
                        
                    except ImportError:
                        logger.warning("ClassificationMetrics not available for additional metrics")
                
                except Exception as e:
                    logger.warning(f"Failed to log metrics to MLflow: {e}")
            
            # Log completion
            logger.info(f"Classification completed: {decision_data['final_disease_name']} ({decision_data['final_confidence']:.2f}) from {decision_data['result_source']}")
            
            return final_result
                
        except Exception as e:
            error_msg = f"Classification error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Log error to MLflow if available
            if mlflow_manager:
                try:
                    mlflow_manager.log_error(session_id, "classification_error", error_msg)
                except:
                    pass
            
            return {"error": error_msg}


# Async wrapper for compatibility
async def run_classification_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async wrapper for the classification tool
    
    Args:
        input_data: Dictionary containing image_b64 and optional context
    
    Returns:
        Classification results or error
    """
    tool = ClassificationTool()
    return await tool._arun(**input_data)
