"""
Classification Tool for LangGraph Workflow

This tool wraps the CNN classification functionality for use in the LangGraph workflow.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import base64
import io
import sys
import os

# Add the parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from engine.ml.cnn_attn_classifier_improved import CNNWithAttentionClassifier

logger = logging.getLogger(__name__)


class ClassificationInput(BaseModel):
    """Input schema for classification tool"""
    image_b64: str = Field(description="Base64 encoded image of the plant leaf")
    plant_type: Optional[str] = Field(default=None, description="Type of plant (optional)")
    location: Optional[str] = Field(default=None, description="Location for context (optional)")
    season: Optional[str] = Field(default=None, description="Season for context (optional)")
    growth_stage: Optional[str] = Field(default=None, description="Growth stage (optional)")


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
    
    async def _arun(self, **kwargs) -> Dict[str, Any]:
        """Async implementation"""
        return await asyncio.to_thread(self._run, **kwargs)
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the classification tool
        
        Returns:
            Dictionary containing classification results or error
        """
        try:
            # Validate input
            if not kwargs.get("image_b64"):
                return {"error": "No image provided"}
            
            if not self.classifier:
                return {"error": "CNN classifier not available"}
            
            # Run classification using the new complete method
            try:
                input_context = f"Plant: {kwargs.get('plant_type', 'unknown')}, Location: {kwargs.get('location', 'unknown')}, Season: {kwargs.get('season', 'unknown')}"
                
                # Use the new complete method that returns all results at once
                result = self.classifier.predict_leaf_classification_complete(
                    image_bytes=kwargs["image_b64"],
                    input_text=input_context
                )
                
                # Check for errors from the classifier
                if result.get("error"):
                    return {"error": result["error"]}
                
                # Format the results for the workflow
                if result.get("success"):
                    formatted_result = {
                        "disease_name": result.get("disease_name"),
                        "confidence": result.get("confidence"),
                        "severity": "Unknown",  # Not provided by current model
                        "description": f"Detected {result.get('disease_name')} with {result.get('confidence', 0):.2%} confidence",
                        "attention_overlay": result.get("attention_overlay"),  # Direct from classifier
                        "raw_class_label": result.get("raw_class_label"),
                        "plant_context": {
                            "plant_type": kwargs.get("plant_type"),
                            "location": kwargs.get("location"),
                            "season": kwargs.get("season"),
                            "growth_stage": kwargs.get("growth_stage")
                        }
                    }
                    
                    logger.info(f"Classification successful: {result.get('disease_name')} ({result.get('confidence', 0):.2f}) with attention overlay")
                    return formatted_result
                
                return {"error": "Classification failed - unexpected result format"}
                
            except Exception as e:
                return {"error": f"Classification failed: {str(e)}"}
                
        except Exception as e:
            error_msg = f"Classification error: {str(e)}"
            logger.error(error_msg, exc_info=True)
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
