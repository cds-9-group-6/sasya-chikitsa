"""
Prescription Tool for LangGraph Workflow

This tool generates treatment prescriptions using RAG-based recommendations.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import sys
import os

# Add the parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

logger = logging.getLogger(__name__)


class PrescriptionInput(BaseModel):
    """Input schema for prescription tool"""
    disease_name: str = Field(description="Name of the diagnosed disease")
    plant_type: Optional[str] = Field(default=None, description="Type of plant")
    location: Optional[str] = Field(default=None, description="Location for regional recommendations")
    season: Optional[str] = Field(default=None, description="Current season")
    severity: Optional[str] = Field(default="Medium", description="Disease severity level")
    user_context: Optional[Dict[str, Any]] = Field(default={}, description="Additional user context")


class PrescriptionTool(BaseTool):
    """
    Tool for generating treatment prescriptions using RAG
    """
    name: str = "prescription_generator"
    description: str = "Generates treatment prescriptions and recommendations for plant diseases using RAG"
    args_schema: type[BaseModel] = PrescriptionInput
    
    # Declare the rag_system field properly
    rag_system: Optional[Any] = Field(default=None, exclude=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._load_rag_system()
    
    def _load_rag_system(self):
        """Load the RAG system"""
        try:
            # Import the RAG system
            from engine.rag.rag_with_ollama import OllamaRag
            
            # Initialize RAG system with default settings
            self.rag_system = OllamaRag(llm_name="llama3.1:8b", temperature=0.1)
            logger.info("RAG system loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load RAG system: {str(e)}")
            self.rag_system = None
    
    async def _arun(self, **kwargs) -> Dict[str, Any]:
        """Async implementation"""
        return await asyncio.to_thread(self._run, **kwargs)
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the prescription tool
        
        Returns:
            Dictionary containing prescription data or error
        """
        try:
            # Validate input
            disease_name = kwargs.get("disease_name")
            if not disease_name:
                return {"error": "No disease name provided"}
            
            if not self.rag_system:
                # Fallback to rule-based recommendations
                return self._generate_fallback_prescription(**kwargs)
            
            # Build query for RAG system
            plant_type = kwargs.get("plant_type", "general")
            location = kwargs.get("location", "")
            season = kwargs.get("season", "")
            severity = kwargs.get("severity", "medium")
            
            query = f"""
            Disease: {disease_name}
            Plant: {plant_type}
            Location: {location}
            Season: {season}
            Severity: {severity}
            
            Provide comprehensive treatment recommendations including:
            1. Chemical treatments with dosages and application methods
            2. Organic/natural treatment alternatives
            3. Preventive measures
            4. Application timing and frequency
            5. Safety precautions
            6. Expected recovery timeline
            """
            
            # Query RAG system
            try:
                # Use RAG system with metadata filtering for better context-aware results
                if self.rag_system:
                    logger.info(f"🔍 Querying RAG with metadata - plant: {plant_type}, season: {season}, location: {location}, disease: {disease_name}")
                    rag_response = self.rag_system.run_query(
                        query_request=query,
                        plant_type=plant_type,
                        season=season,
                        location=location,
                        disease=disease_name
                    )
                else:
                    raise Exception("RAG system not initialized")
                
                # Parse RAG response into structured format
                prescription_data = self._parse_rag_response(rag_response, **kwargs)
                
                logger.info(f"Prescription generated for {disease_name}")
                return prescription_data
                
            except Exception as e:
                logger.warning(f"RAG query failed: {str(e)}. Using fallback prescription.")
                return self._generate_fallback_prescription(**kwargs)
                
        except Exception as e:
            error_msg = f"Prescription generation error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}
    
    def _parse_rag_response(self, rag_response: str, **kwargs) -> Dict[str, Any]:
        """
        Parse RAG response into structured prescription data
        
        Args:
            rag_response: Raw response from RAG system
            **kwargs: Original input parameters
        
        Returns:
            Structured prescription data
        """
        try:
            # Basic parsing - in production, use more sophisticated NLP parsing
            lines = rag_response.split('\n')
            
            treatments = []
            preventive_measures = []
            notes = ""
            
            current_section = None
            current_treatment = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identify sections
                if "treatment" in line.lower() and ("chemical" in line.lower() or "organic" in line.lower()):
                    current_section = "treatment"
                    if current_treatment:
                        treatments.append(current_treatment)
                        current_treatment = {}
                elif "preventive" in line.lower() or "prevention" in line.lower():
                    current_section = "prevention"
                    if current_treatment:
                        treatments.append(current_treatment)
                        current_treatment = {}
                elif "note" in line.lower() or "important" in line.lower():
                    current_section = "notes"
                
                # Parse content
                if current_section == "treatment":
                    if line.startswith(('•', '-', '*')) or line[0].isdigit():
                        # Treatment item
                        treatment_text = line.lstrip('•-*0123456789. ')
                        if not current_treatment:
                            current_treatment = {
                                "name": treatment_text,
                                "type": "Chemical" if "chemical" in line.lower() else "Organic",
                                "application": "Spray application",
                                "dosage": "As per label instructions",
                                "frequency": "Weekly until recovery"
                            }
                        else:
                            # Additional details
                            if "dosage" in line.lower() or "dose" in line.lower():
                                current_treatment["dosage"] = treatment_text
                            elif "application" in line.lower() or "apply" in line.lower():
                                current_treatment["application"] = treatment_text
                            elif "frequency" in line.lower() or "repeat" in line.lower():
                                current_treatment["frequency"] = treatment_text
                
                elif current_section == "prevention":
                    if line.startswith(('•', '-', '*')) or line[0].isdigit():
                        preventive_measures.append(line.lstrip('•-*0123456789. '))
                
                elif current_section == "notes":
                    notes += line + " "
            
            # Add final treatment if exists
            if current_treatment:
                treatments.append(current_treatment)
            
            # Ensure we have at least some treatments
            if not treatments:
                treatments = self._get_default_treatments(kwargs.get("disease_name", ""))
            
            if not preventive_measures:
                preventive_measures = self._get_default_preventive_measures()
            
            return {
                "treatments": treatments,
                "preventive_measures": preventive_measures,
                "notes": notes.strip(),
                "disease_name": kwargs.get("disease_name"),
                "plant_type": kwargs.get("plant_type"),
                "severity": kwargs.get("severity", "Medium"),
                "location": kwargs.get("location"),
                "season": kwargs.get("season"),
                "rag_response": rag_response  # Include raw response for debugging
            }
            
        except Exception as e:
            logger.error(f"Error parsing RAG response: {str(e)}")
            return self._generate_fallback_prescription(**kwargs)
    
    def _generate_fallback_prescription(self, **kwargs) -> Dict[str, Any]:
        """
        Generate fallback prescription when RAG is not available
        
        Returns:
            Basic prescription data
        """
        disease_name = kwargs.get("disease_name", "Unknown Disease")
        plant_type = kwargs.get("plant_type", "plant")
        severity = kwargs.get("severity", "Medium")
        
        # Basic treatments based on common patterns
        treatments = self._get_default_treatments(disease_name)
        preventive_measures = self._get_default_preventive_measures()
        
        notes = f"These are general recommendations for {disease_name}. Consult with a local agricultural expert for specific guidance based on your location and conditions."
        
        return {
            "treatments": treatments,
            "preventive_measures": preventive_measures,
            "notes": notes,
            "disease_name": disease_name,
            "plant_type": plant_type,
            "severity": severity,
            "location": kwargs.get("location"),
            "season": kwargs.get("season"),
            "fallback": True
        }
    
    def _get_default_treatments(self, disease_name: str) -> List[Dict[str, str]]:
        """Get default treatments based on disease type"""
        disease_lower = disease_name.lower()
        
        if "bacterial" in disease_lower:
            return [
                {
                    "name": "Copper-based Bactericide",
                    "type": "Chemical",
                    "application": "Foliar spray",
                    "dosage": "2-3 ml per liter of water",
                    "frequency": "Every 7-10 days until symptoms reduce"
                },
                {
                    "name": "Streptomycin Solution",
                    "type": "Antibiotic",
                    "application": "Spray on affected areas",
                    "dosage": "1g per liter of water", 
                    "frequency": "Weekly for 3-4 weeks"
                }
            ]
        
        elif "fungal" in disease_lower or "blight" in disease_lower:
            return [
                {
                    "name": "Copper Sulfate Fungicide",
                    "type": "Chemical",
                    "application": "Foliar spray",
                    "dosage": "3-5 ml per liter of water",
                    "frequency": "Every 5-7 days until recovery"
                },
                {
                    "name": "Neem Oil Solution",
                    "type": "Organic",
                    "application": "Spray on leaves and stems",
                    "dosage": "5-10 ml per liter of water",
                    "frequency": "Twice weekly"
                }
            ]
        
        elif "viral" in disease_lower:
            return [
                {
                    "name": "Remove Infected Parts",
                    "type": "Cultural",
                    "application": "Manual removal and disposal",
                    "dosage": "Remove all affected leaves and stems",
                    "frequency": "Immediately and monitor regularly"
                },
                {
                    "name": "Imidacloprid Insecticide",
                    "type": "Chemical", 
                    "application": "Soil drench or spray",
                    "dosage": "1-2 ml per liter of water",
                    "frequency": "Monthly to control vectors"
                }
            ]
        
        else:
            # General treatment
            return [
                {
                    "name": "Broad Spectrum Fungicide",
                    "type": "Chemical",
                    "application": "Foliar spray",
                    "dosage": "As per manufacturer instructions",
                    "frequency": "Weekly until improvement"
                },
                {
                    "name": "Organic Compost Tea",
                    "type": "Organic",
                    "application": "Soil application and foliar spray",
                    "dosage": "Dilute 1:10 with water",
                    "frequency": "Bi-weekly"
                }
            ]
    
    def _get_default_preventive_measures(self) -> List[str]:
        """Get default preventive measures"""
        return [
            "Ensure proper drainage to avoid waterlogging",
            "Maintain adequate spacing between plants for air circulation",
            "Remove and dispose of infected plant debris properly",
            "Avoid overhead watering; water at the base of plants",
            "Apply balanced fertilizer to maintain plant health",
            "Inspect plants regularly for early detection of diseases",
            "Use disease-resistant plant varieties when available",
            "Practice crop rotation to break disease cycles",
            "Sanitize gardening tools between plants",
            "Avoid working with plants when they are wet"
        ]


# Async wrapper for compatibility
async def run_prescription_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async wrapper for the prescription tool
    
    Args:
        input_data: Dictionary containing disease info and context
    
    Returns:
        Prescription data or error
    """
    tool = PrescriptionTool()
    return await tool._arun(**input_data)
