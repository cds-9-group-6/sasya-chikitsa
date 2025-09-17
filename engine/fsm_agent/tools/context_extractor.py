"""
Context Extractor Tool for LangGraph Workflow

This tool extracts relevant context information from user messages.
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ContextInput(BaseModel):
    """Input schema for context extraction tool"""
    user_message: str = Field(description="User message to extract context from")
    additional_context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context if available")


class ContextExtractorTool(BaseTool):
    """
    Tool for extracting context information from user messages
    """
    name: str = "context_extractor"
    description: str = "Extracts location, season, plant type, and other relevant context from user messages"
    args_schema: type[BaseModel] = ContextInput
    
    # Declare the patterns field properly
    patterns: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._load_context_patterns()
    
    def _load_context_patterns(self):
        """Load patterns for context extraction"""
        self.patterns = {
            "locations": {
                # Indian states and major cities
                "states": [
                    "tamil nadu", "tamilnadu", "tn", "karnataka", "kerala", "andhra pradesh",
                    "telangana", "maharashtra", "gujarat", "rajasthan", "punjab", "haryana",
                    "uttar pradesh", "bihar", "west bengal", "odisha", "jharkhand", "chhattisgarh",
                    "madhya pradesh", "goa", "himachal pradesh", "uttarakhand", "assam",
                    "arunachal pradesh", "nagaland", "manipur", "mizoram", "tripura", "sikkim"
                ],
                "cities": [
                    "chennai", "bangalore", "bengaluru", "hyderabad", "mumbai", "delhi",
                    "kolkata", "pune", "ahmedabad", "surat", "jaipur", "lucknow", "kanpur",
                    "nagpur", "indore", "thane", "bhopal", "visakhapatnam", "pimpri-chinchwad",
                    "patna", "vadodara", "ghaziabad", "ludhiana", "agra", "nashik", "coimbatore",
                    "madurai", "salem", "tiruchirappalli", "tiruppur", "erode", "vellore"
                ],
                "keywords": ["from", "in", "at", "located", "based", "live", "state", "city"]
            },
            "seasons": {
                "monsoon": ["monsoon", "rainy", "rain", "wet", "july", "august", "september"],
                "winter": ["winter", "cold", "december", "january", "february", "cool"],
                "summer": ["summer", "hot", "march", "april", "may", "june", "dry", "heat"],
                "post_monsoon": ["post-monsoon", "october", "november", "retreat"],
                "keywords": ["season", "weather", "climate", "during", "currently"]
            },
            "plants": {
                "vegetables": [
                    "tomato", "potato", "onion", "brinjal", "eggplant", "okra", "bhindi",
                    "carrot", "beans", "peas", "cabbage", "cauliflower", "spinach", "lettuce",
                    "cucumber", "bottle gourd", "bitter gourd", "pumpkin", "chili", "pepper",
                    "capsicum", "radish", "beetroot", "turnip", "coriander", "mint"
                ],
                "fruits": [
                    "mango", "banana", "apple", "grapes", "orange", "lime", "lemon", 
                    "papaya", "guava", "pomegranate", "coconut", "dates", "figs",
                    "watermelon", "muskmelon", "pineapple", "jackfruit", "sapota"
                ],
                "cereals": [
                    "rice", "wheat", "corn", "maize", "barley", "millet", "sorghum",
                    "finger millet", "ragi", "pearl millet", "bajra", "oats"
                ],
                "cash_crops": [
                    "cotton", "sugarcane", "tobacco", "tea", "coffee", "rubber",
                    "groundnut", "peanut", "sunflower", "mustard", "sesame"
                ],
                "pulses": [
                    "chickpea", "chana", "lentil", "masoor", "black gram", "urad",
                    "green gram", "moong", "pigeon pea", "arhar", "kidney beans", "rajma"
                ],
                "keywords": ["plant", "crop", "growing", "cultivation", "farm", "garden"]
            },
            "growth_stages": {
                "seedling": ["seedling", "sprouted", "germinated", "young", "small"],
                "vegetative": ["vegetative", "growing", "leafy", "green", "developing"],
                "flowering": ["flowering", "blooming", "flowers", "buds", "bud"],
                "fruiting": ["fruiting", "fruits", "producing", "harvest", "mature"],
                "keywords": ["stage", "phase", "growth", "development"]
            },
            "symptoms": {
                "spots": ["spots", "spotted", "patches", "marks", "lesions"],
                "yellowing": ["yellow", "yellowing", "chlorosis", "pale"],
                "wilting": ["wilting", "drooping", "sagging", "dying"],
                "browning": ["brown", "browning", "necrosis", "dead", "dried"],
                "curling": ["curling", "curled", "twisted", "deformed"],
                "holes": ["holes", "eaten", "chewed", "damaged", "perforated"]
            }
        }
    
    async def _arun(self, **kwargs) -> Dict[str, Any]:
        """Async implementation"""
        return await asyncio.to_thread(self._run, **kwargs)
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the context extraction tool
        
        Returns:
            Dictionary containing extracted context or error
        """
        try:
            user_message = kwargs.get("user_message", "")
            additional_context = kwargs.get("additional_context", {})
            
            if not user_message:
                return {"error": "No user message provided"}
            
            # Clean and normalize message
            message_lower = user_message.lower()
            
            # Extract context
            extracted_context = {
                "location": self._extract_location(message_lower),
                "season": self._extract_season(message_lower),
                "plant_type": self._extract_plant_type(message_lower),
                "growth_stage": self._extract_growth_stage(message_lower),
                "symptoms": self._extract_symptoms(message_lower),
                "urgency": self._extract_urgency(message_lower),
                "experience_level": self._extract_experience_level(message_lower),
                "additional_info": self._extract_additional_info(message_lower)
            }
            
            # Merge with additional context
            for key, value in additional_context.items():
                if value and not extracted_context.get(key):
                    extracted_context[key] = value
            
            # Remove None values
            extracted_context = {k: v for k, v in extracted_context.items() if v is not None}
            
            logger.info(f"Extracted context: {extracted_context}")
            return extracted_context
            
        except Exception as e:
            error_msg = f"Context extraction error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}
    
    def _extract_location(self, message: str) -> Optional[str]:
        """Extract location from message"""
        # Check for explicit location keywords
        location_keywords = self.patterns["locations"]["keywords"]
        
        for keyword in location_keywords:
            if keyword in message:
                # Look for location after keyword
                pattern = rf"{keyword}\s+([a-zA-Z\s]+)"
                matches = re.findall(pattern, message)
                if matches:
                    potential_location = matches[0].strip()
                    if self._is_valid_location(potential_location):
                        return potential_location.title()
        
        # Direct matching with states and cities
        all_locations = (self.patterns["locations"]["states"] + 
                        self.patterns["locations"]["cities"])
        
        for location in all_locations:
            if location in message:
                return location.title()
        
        return None
    
    def _is_valid_location(self, location: str) -> bool:
        """Check if extracted text is a valid location"""
        location_lower = location.lower()
        all_locations = (self.patterns["locations"]["states"] + 
                        self.patterns["locations"]["cities"])
        
        # Direct match
        if location_lower in all_locations:
            return True
        
        # Partial match
        for known_location in all_locations:
            if location_lower in known_location or known_location in location_lower:
                return True
        
        # Check if it looks like a place name (no common non-location words)
        non_location_words = ["plant", "disease", "help", "problem", "issue", "leaf", "growth"]
        return not any(word in location_lower for word in non_location_words)
    
    def _extract_season(self, message: str) -> Optional[str]:
        """Extract season from message"""
        seasons = self.patterns["seasons"]
        
        for season, keywords in seasons.items():
            if season == "keywords":
                continue
            for keyword in keywords:
                if keyword in message:
                    return season.replace("_", " ").title()
        
        return None
    
    def _extract_plant_type(self, message: str) -> Optional[str]:
        """Extract plant type from message"""
        plants = self.patterns["plants"]
        
        # Check each category
        for category, plant_list in plants.items():
            if category == "keywords":
                continue
            for plant in plant_list:
                if plant in message:
                    return plant.title()
        
        return None
    
    def _extract_growth_stage(self, message: str) -> Optional[str]:
        """Extract growth stage from message"""
        stages = self.patterns["growth_stages"]
        
        for stage, keywords in stages.items():
            if stage == "keywords":
                continue
            for keyword in keywords:
                if keyword in message:
                    return stage.title()
        
        return None
    
    def _extract_symptoms(self, message: str) -> Optional[List[str]]:
        """Extract symptoms from message"""
        symptoms = self.patterns["symptoms"]
        found_symptoms = []
        
        for symptom_type, keywords in symptoms.items():
            for keyword in keywords:
                if keyword in message:
                    found_symptoms.append(symptom_type)
                    break
        
        return found_symptoms if found_symptoms else None
    
    def _extract_urgency(self, message: str) -> Optional[str]:
        """Extract urgency level from message"""
        urgent_keywords = ["urgent", "emergency", "quickly", "fast", "immediate", "asap", "dying", "critical"]
        high_keywords = ["soon", "important", "serious", "bad", "worse", "spreading"]
        
        if any(keyword in message for keyword in urgent_keywords):
            return "Urgent"
        elif any(keyword in message for keyword in high_keywords):
            return "High"
        else:
            return "Normal"
    
    def _extract_experience_level(self, message: str) -> Optional[str]:
        """Extract user's experience level"""
        beginner_keywords = ["new", "beginner", "first time", "don't know", "not sure", "help me"]
        experienced_keywords = ["experienced", "always", "usually", "before", "tried"]
        
        if any(keyword in message for keyword in beginner_keywords):
            return "Beginner"
        elif any(keyword in message for keyword in experienced_keywords):
            return "Experienced"
        else:
            return "Intermediate"
    
    def _extract_additional_info(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract additional information"""
        additional_info = {}
        
        # Garden type
        if any(word in message for word in ["home", "house", "balcony", "terrace"]):
            additional_info["garden_type"] = "Home Garden"
        elif any(word in message for word in ["farm", "field", "commercial", "agriculture"]):
            additional_info["garden_type"] = "Commercial Farm"
        
        # Organic preference
        if any(word in message for word in ["organic", "natural", "chemical-free"]):
            additional_info["organic_preference"] = True
        elif any(word in message for word in ["chemical", "pesticide", "fast acting"]):
            additional_info["organic_preference"] = False
        
        # Previous treatments
        if any(word in message for word in ["tried", "used", "applied", "treatment"]):
            additional_info["previous_treatment"] = True
        
        # Time frame
        time_patterns = {
            "recent": ["today", "yesterday", "few days", "this week"],
            "medium": ["last week", "few weeks", "this month"],
            "long": ["months", "long time", "since"]
        }
        
        for timeframe, keywords in time_patterns.items():
            if any(keyword in message for keyword in keywords):
                additional_info["problem_duration"] = timeframe
                break
        
        return additional_info if additional_info else None


# Async wrapper for compatibility
async def run_context_extractor_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async wrapper for the context extractor tool
    
    Args:
        input_data: Dictionary containing user message and optional context
    
    Returns:
        Extracted context or error
    """
    tool = ContextExtractorTool()
    return await tool._arun(**input_data)
