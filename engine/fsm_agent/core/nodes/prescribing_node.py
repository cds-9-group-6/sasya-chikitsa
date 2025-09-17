"""
Prescribing Node for FSM Agent workflow
Generates treatment recommendations
"""

import logging
from typing import Dict, Any

from .base_node import BaseNode

try:
    from ..workflow_state import WorkflowState, add_message_to_state, set_error, can_retry
    from ...tools.prescription_tool import PrescriptionTool
except ImportError:
    from engine.fsm_agent.core.workflow_state import WorkflowState, add_message_to_state, set_error, can_retry
    from engine.fsm_agent.tools.prescription_tool import PrescriptionTool

logger = logging.getLogger(__name__)


class PrescribingNode(BaseNode):
    """Prescription node - generates treatment recommendations"""
    
    @property
    def node_name(self) -> str:
        return "prescribing"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute prescription node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        
        try:
            # Check for classification results in current state or session history
            classification_results = self._get_classification_from_session(state)
            
            if not classification_results:
                logger.info("⚠️ No classification results found in session - requesting classification")
                self._request_classification_for_prescription(state)
                return state
            
            # Update state with classification results if found in session history
            if not state.get("classification_results"):
                state["classification_results"] = classification_results
                logger.info(f"📋 Retrieved classification from session history: {classification_results.get('disease', 'Unknown')}")
            
            add_message_to_state(
                state,
                "assistant",
                "💊 Generating personalized treatment recommendations based on the diagnosis..."
            )
            
            # Run prescription tool
            prescription_tool = self.tools["prescription"]
            
            # Debug logging to verify context flow
            logger.info(f"Prescription context - plant_type: {state.get('plant_type')}, location: {state.get('location')}, season: {state.get('season')}")
            logger.info(f"Full user_context for prescription: {state.get('user_context', {})}")
            
            prescription_input = {
                "disease_name": state.get("disease_name"),
                "plant_type": state.get("plant_type"),
                "location": state.get("location"),
                "season": state.get("season"),
                "severity": state.get("classification_results", {}).get("severity"),
                "user_context": state.get("user_context", {})
            }
            
            result = await prescription_tool.arun(prescription_input)
            
            if result and not result.get("error"):
                self._process_successful_prescription(state, result)
            else:
                self._process_failed_prescription(state, result)
        
        except Exception as e:
            logger.error(f"Error in prescribing node: {str(e)}", exc_info=True)
            self._handle_prescription_exception(state, e)
        
        return state
    
    def _process_successful_prescription(self, state: WorkflowState, result: Dict[str, Any]) -> None:
        """Process successful prescription generation"""
        state["prescription_data"] = result
        state["treatment_recommendations"] = result.get("treatments", [])
        state["preventive_measures"] = result.get("preventive_measures", [])
        
        # Format prescription response
        response = self._format_prescription_response(result)
        
        # Store response for streaming and add to messages
        state["assistant_response"] = response
        
        # GENERIC ARCHITECTURAL FIX: Set streaming metadata for modular duplicate prevention
        state["response_status"] = "final"  # This is the enhanced, final version ready for streaming
        state["stream_immediately"] = True  # Node indicates immediate streaming needed
        state["stream_in_state_update"] = False  # Don't include in state_update events
        
        add_message_to_state(state, "assistant", response)
        
        # Determine next action based on user intent
        user_intent = state.get("user_intent", {})
        if user_intent.get("wants_vendors", False):
            state["next_action"] = "vendor_query"
        else:
            # Prescription complete - route back to followup for user's next choice
            state["next_action"] = "followup"
            state["requires_user_input"] = True
            
            completion_msg = "✅ **Treatment Plan Complete!** If you'd like to find vendors to purchase these treatments, just let me know!"
            
            # Add general answer if this was a hybrid request
            if state.get("general_answer"):
                completion_msg += f"\n\n🌾 **General Agricultural Advice:** {state['general_answer']}"
            
            add_message_to_state(state, "assistant", completion_msg)
    
    def _process_failed_prescription(self, state: WorkflowState, result: Dict[str, Any]) -> None:
        """Process failed prescription generation"""
        error_msg = result.get("error", "Prescription generation failed") if result else "Prescription tool returned no result"
        if can_retry(state):
            state["next_action"] = "retry"
            add_message_to_state(
                state,
                "assistant",
                f"⚠️ Prescription generation failed: {error_msg}. Retrying..."
            )
        else:
            set_error(state, error_msg)
            state["next_action"] = "error"
    
    def _handle_prescription_exception(self, state: WorkflowState, exception: Exception) -> None:
        """Handle exceptions during prescription generation"""
        if can_retry(state):
            state["next_action"] = "retry"
            add_message_to_state(
                state,
                "assistant",
                f"⚠️ Error during prescription generation: {str(exception)}. Retrying..."
            )
        else:
            set_error(state, f"Prescription error: {str(exception)}")
            state["next_action"] = "error"
    
    def _format_prescription_response(self, prescription_data: Dict[str, Any]) -> str:
        """Format prescription data into a professional treatment plan"""
        
        treatments = prescription_data.get("treatments", [])
        preventive_measures = prescription_data.get("preventive_measures", [])
        additional_notes = prescription_data.get("notes")
        
        response = f"""💊 **TREATMENT PLAN FOR YOUR PLANT**

🌿 **MEDICINES TO USE**"""
        
        for i, treatment in enumerate(treatments, 1):
            treatment_name = treatment.get('name', 'Unknown Treatment')
            treatment_type = treatment.get('type', 'N/A')
            
            response += f"""

🔹 **MEDICINE #{i}: {treatment_name}**
• **What it is:** {treatment_type}
• **How to apply:** {treatment.get('application', 'Follow bottle instructions')}
• **How much:** {treatment.get('dosage', 'As directed on package')}
• **How often:** {treatment.get('frequency', 'Check instructions')}
• **For how long:** {treatment.get('duration', 'Until plant looks better')}"""
        
        if preventive_measures:
            response += f"""

🛡️ **HOW TO PREVENT THIS DISEASE**"""
            for i, measure in enumerate(preventive_measures, 1):
                response += f"""
{i}. {measure}"""
        
        if additional_notes:
            response += f"""

⚠️ **IMPORTANT TIPS**
{additional_notes}"""
        
        response += f"""

✅ **REMEMBER**
• Always read the medicine bottle instructions
• Check your plant daily for improvement  
• Ask local experts if you need help
• Keep notes about what works

💚 **Your plant will get better with proper care!**"""
        
        return response
    
    def _get_classification_from_session(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Get classification results from current state or session history
        
        Args:
            state: Current workflow state
            
        Returns:
            Classification results if found, None otherwise
        """
        # First check current state
        classification_results = state.get("classification_results")
        if classification_results:
            logger.info("📋 Found classification results in current state")
            return classification_results
        
        # Check session history for previous classification
        messages = state.get("messages", [])
        
        # Look for assistant messages that mention disease classification
        for message in reversed(messages):  # Start from most recent
            if message.get("role") == "assistant":
                content = message.get("content", "")
                
                # Check for classification patterns in message content
                if ("diagnosis" in content.lower() or 
                    "disease detected" in content.lower() or
                    "classification result" in content.lower() or
                    "confidence" in content.lower()):
                    
                    # Try to extract classification info from the message
                    classification_info = self._extract_classification_from_message(content)
                    if classification_info:
                        logger.info(f"📋 Extracted classification from session history: {classification_info}")
                        return classification_info
        
        # Check if there are any stored results in other state keys
        disease_name = state.get("disease_name")
        if disease_name:
            logger.info(f"📋 Found disease name in state: {disease_name}")
            return {
                "disease": disease_name,
                "confidence": state.get("confidence", 0.8),
                "severity": state.get("severity", "moderate")
            }
        
        logger.info("⚠️ No classification results found in current state or session history")
        return None
    
    def _extract_classification_from_message(self, content: str) -> Dict[str, Any]:
        """
        Extract classification information from assistant message content
        
        Args:
            content: Assistant message content
            
        Returns:
            Classification results if extractable, None otherwise
        """
        import re
        
        # Common disease patterns that might appear in messages
        disease_patterns = [
            r"diagnosis[:\s]+([^\n\(]+?)(?:\s*\(|$)",  # "Diagnosis: Disease Name" 
            r"disease[:\s]+([^\n\(]+?)(?:\s*\(|$)",    # "Disease: Disease Name"
            r"detected[:\s]+([^\n\(]+?)(?:\s*\(|$)",   # "Detected: Disease Name"
            r"identified[:\s]+([^\n\(]+?)(?:\s*\(|$)", # "Identified: Disease Name"
            r"\*\*([^*\n]+)\*\*",                      # "**Disease Name**" (markdown bold)
            r"disease detected[:\s]+([^\n\(]+?)(?:\s*\(|$)",
            r"🔬[^:]*diagnosis[:\s]*([^\n\(]+?)(?:\s*\(|$)"
        ]
        
        confidence_patterns = [
            r"confidence[:\s]*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*%\s*confidence",
            r"(\d+(?:\.\d+)?)\s*confidence"
        ]
        
        extracted_disease = None
        extracted_confidence = None
        
        # Extract disease name
        for pattern in disease_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                extracted_disease = match.group(1).strip().rstrip(".,!?")
                break
        
        # Extract confidence
        for pattern in confidence_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                confidence_str = match.group(1)
                try:
                    confidence_val = float(confidence_str)
                    # Convert percentage to decimal if needed
                    if confidence_val > 1:
                        confidence_val = confidence_val / 100
                    extracted_confidence = confidence_val
                    break
                except ValueError:
                    continue
        
        if extracted_disease:
            # Clean up the disease name - remove markdown artifacts and extra spaces
            cleaned_disease = extracted_disease.strip().rstrip("*.,!?")
            return {
                "disease": cleaned_disease,
                "confidence": extracted_confidence or 0.8,
                "severity": "moderate"  # Default severity
            }
        
        return None
    
    def _request_classification_for_prescription(self, state: WorkflowState) -> None:
        """
        Request classification before prescription can be provided
        
        Args:
            state: Current workflow state
        """
        logger.info("💊 Prescription requested but no classification available - routing to classification")
        
        # Check if there's an image in the current request
        if state.get("user_image"):
            # Image available - route to classification
            state["next_action"] = "classify"
            add_message_to_state(
                state,
                "assistant", 
                "🔬 I'll first analyze your plant image to identify the disease, then provide treatment recommendations."
            )
        else:
            # No image - request image upload
            state["next_action"] = "followup"  # Go back to followup to handle image request
            add_message_to_state(
                state,
                "assistant",
                "📸 To provide treatment recommendations, I need to first identify the plant disease. Please upload a clear image of the affected leaf or plant part."
            )
        
        state["requires_user_input"] = not state.get("user_image", False)
