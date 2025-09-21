"""
Classifying Node for FSM Agent workflow
Runs disease classification on uploaded image
"""

import logging
import sys, os
from typing import Dict, Any

from .base_node import BaseNode

# Add the parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

try:
    from ..workflow_state import WorkflowState, add_message_to_state, set_error, can_retry
    from ...tools.classification_tool import ClassificationTool
except ImportError:
    from engine.fsm_agent.core.workflow_state import WorkflowState, add_message_to_state, set_error, can_retry
    from engine.fsm_agent.tools.classification_tool import ClassificationTool

logger = logging.getLogger(__name__)


class ClassifyingNode(BaseNode):
    """Classification node - runs disease classification on uploaded image"""
    
    @property
    def node_name(self) -> str:
        return "classifying"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute classification node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        logger.info(f"User intent in classifying node: {state.get('user_intent', 'NOT_FOUND')}")
        
        try:
            if not state.get("user_image"):
                set_error(state, "No image provided for classification")
                state["next_action"] = "error"
                return state
            
            # Run classification tool
            classification_tool = self.tools["classification"]
            
            # Debug logging to verify context flow
            logger.info(f"Classification context - plant_type: {state.get('plant_type')}, location: {state.get('location')}, season: {state.get('season')}")
            logger.info(f"Full user_context: {state.get('user_context', {})}")
            
            classification_input = {
                "image_b64": state["user_image"],
                "plant_type": state.get("plant_type"),
                "location": state.get("location"),
                "season": state.get("season"),
                "session_id": state.get("session_id", "unknown")  # ADD SESSION ID FOR MLFLOW
            }
            
            add_message_to_state(
                state,
                "assistant",
                "🔬 Analyzing the plant leaf image for disease detection..."
            )
            
            result = await classification_tool._arun(mlflow_manager=self.mlflow_manager, **classification_input)
            
            # Determine next action based on user intent FIRST (regardless of classification result)
            user_intent = state.get("user_intent", {})
            logger.info(f"Classification attempted. User intent: {user_intent}")
            
            if result and not result.get("error"):
                # Classification successful
                self._process_successful_classification(state, result, user_intent)
            else:
                # Classification failed
                self._process_failed_classification(state, result)
            
            logger.info(f"Final next_action set to: {state.get('next_action')}")
        
        except Exception as e:
            logger.error(f"Error in classifying node: {str(e)}", exc_info=True)
            self._handle_classification_exception(state, e)
        
        return state
    
    def _process_successful_classification(self, state: WorkflowState, result: Dict[str, Any], user_intent: Dict[str, Any]) -> None:
        """Process successful classification results"""
        state["classification_results"] = result
        state["disease_name"] = result.get("disease_name")
        state["confidence"] = result.get("confidence")
        # NOTE: attention_overlay is NOT stored in state - only streamed once for transparency
        
        # Format classification response professionally
        confidence_pct = (result.get("confidence", 0) * 100)
        disease_name = result.get("disease_name", "Unknown")
        severity = result.get("severity", "Unknown")
        description = result.get("description", "")
        
        # Farmer-friendly diagnostic report with simple language
        farmer_disease_name = self._get_farmer_friendly_disease_name(disease_name)
        
        # Confidence in farmer terms
        confidence_emoji, confidence_text = self._get_farmer_confidence(confidence_pct)
        
        # Check if plant is healthy - different response format
        is_healthy = disease_name.lower() in ["healthy", "healthy_plant"] or farmer_disease_name.lower() in ["healthy", "healthy plant"]
        
        if is_healthy:
            # Healthy plant response - no severity or treatment needed
            response = f"""🌿 **PLANT HEALTH ANALYSIS**

🔍 **GREAT NEWS!**
Your plant appears to be: **{farmer_disease_name}**

{confidence_emoji} **HOW SURE ARE WE?**
{confidence_text} ({confidence_pct:.0f}% match)

🎉 **WHAT THIS MEANS**
Your plant looks healthy! No signs of disease detected. Keep up the good care routine you're already following.

💚 **KEEP IT HEALTHY:** Continue regular watering, proper sunlight, and good soil drainage."""
        else:
            # Diseased plant response - include severity and treatment
            farmer_severity = self._get_farmer_severity(severity)
            
            response = f"""🌿 **PLANT DISEASE ANALYSIS**

🔍 **WHAT WE FOUND**
Your plant has: **{farmer_disease_name}**

{confidence_emoji} **HOW SURE ARE WE?**
{confidence_text} ({confidence_pct:.0f}% match)

⚠️ **HOW SERIOUS?** 
{farmer_severity}

📝 **SIMPLE EXPLANATION**
{self._simplify_description_for_farmers(description)}

✅ **NEXT STEP:** Get treatment recommendations to help your plant recover!"""
        
        # Store response for streaming and add to messages
        state["assistant_response"] = response
        
        # GENERIC ARCHITECTURAL FIX: Set streaming metadata for modular duplicate prevention
        state["response_status"] = "final"  # This is the enhanced, final version ready for streaming
        state["stream_immediately"] = True  # Node indicates immediate streaming needed
        state["stream_in_state_update"] = False  # Don't include in state_update events
        
        add_message_to_state(state, "assistant", response)
        
        # Set next action based on user intent and plant health
        self._determine_next_action_after_classification(state, user_intent, is_healthy)
    
    def _process_failed_classification(self, state: WorkflowState, result: Dict[str, Any]) -> None:
        """Process failed classification results"""
        error_msg = result.get("error", "Classification failed") if result else "Classification tool returned no result"
        logger.info(f"Classification failed: {error_msg}")
        
        if can_retry(state):
            state["next_action"] = "retry"
            add_message_to_state(
                state,
                "assistant", 
                f"⚠️ Classification attempt failed: {error_msg}. Retrying..."
            )
        else:
            set_error(state, error_msg)
            state["next_action"] = "error"
    
    def _handle_classification_exception(self, state: WorkflowState, exception: Exception) -> None:
        """Handle exceptions during classification"""
        if can_retry(state):
            state["next_action"] = "retry"
            add_message_to_state(
                state,
                "assistant",
                f"⚠️ Error during classification: {str(exception)}. Retrying..."
            )
        else:
            set_error(state, f"Classification error: {str(exception)}")
            state["next_action"] = "error"
    
    def _determine_next_action_after_classification(self, state: WorkflowState, user_intent: Dict[str, Any], is_healthy: bool = False) -> None:
        """Determine next action based on user intent and plant health after successful classification"""
        
        if is_healthy:
            # For healthy plants, skip prescriptions and go directly to follow-up
            state["next_action"] = "followup"
            state["is_complete"] = False
            logger.info("Setting next_action to 'followup' (plant is healthy, no treatment needed)")
            
            completion_msg = "🌱 **Your plant is in great shape!** Keep monitoring it and feel free to ask if you have any general plant care questions!"
            
            # Add general answer if this was a hybrid request
            if state.get("general_answer"):
                completion_msg += f"\n\n🌾 **General Agricultural Advice:** {state['general_answer']}"
            
            add_message_to_state(state, "assistant", completion_msg)
            
        elif user_intent.get("wants_prescription", False):
            state["next_action"] = "prescribe"
            logger.info("Setting next_action to 'prescribe' based on user intent")
        elif user_intent.get("wants_vendors", False):
            state["next_action"] = "prescribe"  # Need prescription first
            logger.info("Setting next_action to 'prescribe' (vendors requested, prescription needed first)")
        else:
            # User only wanted classification - FIXED: Keep session active for follow-up
            state["next_action"] = "followup"  # Changed from "completed" to keep session active
            state["is_complete"] = False  # FIXED: Don't mark as complete, wait for user intent
            logger.info("Setting next_action to 'followup' (classification complete, awaiting user input)")
            
            completion_msg = "✅ **Analysis Complete!** If you need treatment recommendations or want to find vendors, just let me know!"
            
            # Add general answer if this was a hybrid request
            if state.get("general_answer"):
                completion_msg += f"\n\n🌾 **General Agricultural Advice:** {state['general_answer']}"
            
            add_message_to_state(state, "assistant", completion_msg)
    
    def _get_farmer_friendly_disease_name(self, technical_name: str) -> str:
        """Convert technical disease names to farmer-friendly versions"""
        disease_map = {
            "Alternaria_leaf_blotch": "Leaf Spot Disease",
            "bacterial_blight": "Bacterial Leaf Burn", 
            "powdery_mildew": "White Powder Disease",
            "rust": "Orange Rust Disease",
            "black_spot": "Black Spot Disease",
            "downy_mildew": "Fuzzy Mold Disease",
            "anthracnose": "Dark Spot Disease",
            "septoria_leaf_spot": "Brown Spot Disease",
            "cercospora_leaf_spot": "Gray Spot Disease",
            "bacterial_spot": "Bacterial Spots",
            "viral_mosaic": "Leaf Pattern Disease",
            "fusarium_wilt": "Plant Wilting Disease",
            "root_rot": "Root Damage Disease",
            "healthy": "Healthy Plant",
            "healthy_plant": "Healthy Plant"
        }
        
        # Remove underscores and make title case if not in map
        friendly_name = disease_map.get(technical_name.lower(), technical_name.replace("_", " ").title())
        return friendly_name
    
    def _get_farmer_confidence(self, confidence_pct: float) -> tuple:
        """Get farmer-friendly confidence description"""
        if confidence_pct >= 85:
            return ("🟢", "**Very Sure** - The diagnosis is highly accurate")
        elif confidence_pct >= 70:
            return ("🟡", "**Fairly Sure** - Good diagnosis, worth treating")
        else:
            return ("🔴", "**Need to Check** - Consider getting expert advice")
    
    def _get_farmer_severity(self, technical_severity: str) -> str:
        """Convert technical severity to farmer-friendly terms"""
        if not technical_severity or technical_severity.lower() == "unknown":
            return "🟡 **Moderate** - Keep watching, treat if it spreads"
        
        severity_map = {
            "low": "🟢 **Mild** - Easy to treat, not urgent",
            "mild": "🟢 **Mild** - Easy to treat, not urgent", 
            "medium": "🟡 **Moderate** - Should treat soon to prevent spread",
            "moderate": "🟡 **Moderate** - Should treat soon to prevent spread",
            "high": "🔴 **Serious** - Treat immediately to save your plant",
            "severe": "🔴 **Serious** - Treat immediately to save your plant",
            "critical": "🔴 **Very Serious** - Urgent treatment needed!"
        }
        
        return severity_map.get(technical_severity.lower(), "🟡 **Moderate** - Should treat to be safe")
    
    def _simplify_description_for_farmers(self, technical_description: str) -> str:
        """Simplify technical disease descriptions for farmers"""
        if not technical_description:
            return "This disease can damage your plant's leaves and reduce crop yield. Early treatment helps recovery."
        
        # Replace technical terms with farmer-friendly language
        simplified = technical_description
        
        # Common technical to farmer translations
        replacements = {
            "pathogen": "disease",
            "fungal": "fungus",
            "bacterial": "bacteria", 
            "spores": "disease seeds",
            "lesions": "spots",
            "chlorosis": "yellowing",
            "necrosis": "dead tissue",
            "defoliation": "leaf drop",
            "photosynthesis": "plant's food making",
            "chlorophyll": "green color",
            "tissue": "plant parts",
            "infection": "disease spread",
            "symptoms": "signs",
            "manifestation": "appears as",
            "develops": "grows",
            "progresses": "gets worse"
        }
        
        for tech_term, simple_term in replacements.items():
            simplified = simplified.replace(tech_term, simple_term)
        
        # Keep it concise - max 2 sentences
        sentences = simplified.split('.')[:2]
        return '. '.join(s.strip() for s in sentences if s.strip()) + '.'
