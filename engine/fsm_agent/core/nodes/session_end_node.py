"""
Session End Node - Handles session termination when user wants to end conversation
"""

import logging
from typing import Dict, Any

try:
    from ..workflow_state import WorkflowState, add_message_to_state, mark_complete, update_state_node
    from .base_node import BaseNode
except ImportError:
    # Fallback to absolute imports if relative imports fail
    from engine.fsm_agent.core.workflow_state import WorkflowState, add_message_to_state, mark_complete, update_state_node
    from engine.fsm_agent.core.nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class SessionEndNode(BaseNode):
    """Session End node - handles session termination and cleanup"""
    
    @property
    def node_name(self) -> str:
        return "session_end"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute session end logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state with session ended
        """
        self.update_node_state(state)
        
        try:
            # Create farewell message based on conversation context
            farewell_message = self._create_farewell_message(state)
            
            # Store the farewell response for streaming
            state["assistant_response"] = farewell_message
            
            # GENERIC ARCHITECTURAL FIX: Set streaming metadata for modular duplicate prevention
            state["response_status"] = "final"  # This is the enhanced, final version ready for streaming
            state["stream_immediately"] = True  # Node indicates immediate streaming needed
            state["stream_in_state_update"] = False  # Don't include in state_update events
            
            # Add to messages for conversation history
            add_message_to_state(state, "assistant", farewell_message)
            
            # Mark session as ended (different from task completed)
            state["is_complete"] = True
            state["session_ended"] = True
            state["session_end_time"] = state.get("last_update_time")
            state["requires_user_input"] = False
            
            # Clear sensitive data for security
            if "user_image" in state:
                del state["user_image"]
            if "attention_overlay" in state:
                del state["attention_overlay"]
                
            logger.info(f"Session {state['session_id']} ended gracefully")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in session end node: {str(e)}", exc_info=True)
            
            # Even if there's an error, mark session as ended
            state["is_complete"] = True
            state["session_ended"] = True
            state["assistant_response"] = "Thank you for using our plant care service. Take care! 🌱"
            
            # GENERIC ARCHITECTURAL FIX: Set streaming metadata for modular duplicate prevention
            state["response_status"] = "final"  # This is the enhanced, final version ready for streaming
            state["stream_immediately"] = True  # Node indicates immediate streaming needed
            state["stream_in_state_update"] = False  # Don't include in state_update events
            
            add_message_to_state(state, "assistant", state["assistant_response"])
            
            return state
    
    def _create_farewell_message(self, state: WorkflowState) -> str:
        """Create a personalized farewell message based on conversation context"""
        
        # Check what services were provided
        had_diagnosis = bool(state.get("classification_results"))
        had_treatment = bool(state.get("prescription_data"))
        had_vendors = bool(state.get("vendor_options"))
        plant_type = state.get("plant_type", "plant")
        disease_name = state.get("disease_name", "")
        
        # Create context-aware farewell
        if had_diagnosis and had_treatment:
            if disease_name:
                farewell_base = f"🌱 **TAKE CARE OF YOUR {plant_type.upper()}!**\n\n✅ We've helped diagnose your {disease_name} and provided treatment recommendations."
            else:
                farewell_base = f"🌱 **TAKE CARE OF YOUR {plant_type.upper()}!**\n\n✅ We've provided diagnosis and treatment recommendations for your plant."
        elif had_diagnosis:
            farewell_base = f"🌱 **TAKE CARE OF YOUR {plant_type.upper()}!**\n\n✅ We've helped diagnose your plant's condition."
        else:
            farewell_base = "🌱 **THANK YOU FOR USING OUR PLANT CARE SERVICE!**"
        
        # Add follow-up care tips
        care_tips = "\n\n💚 **REMEMBER:**\n"
        care_tips += "• Monitor your plant daily for changes\n"
        care_tips += "• Follow treatment instructions carefully\n"
        care_tips += "• Don't hesitate to ask local agricultural experts\n"
        care_tips += "• Take photos to track your plant's recovery\n"
        
        # Add return invitation
        return_message = "\n\n🚀 **COME BACK ANYTIME!**\n"
        return_message += "We're here 24/7 to help with any plant health questions.\n\n"
        return_message += "Wishing you a healthy and productive growing season! 🌾✨"
        
        return farewell_base + care_tips + return_message
    
    async def _detect_goodbye_intent(self, state: WorkflowState) -> bool:
        """
        Detect if user wants to end the session using LLM
        
        Args:
            state: Current workflow state
            
        Returns:
            True if user wants to end session, False otherwise
        """
        try:
            user_message = state.get("user_message", "").lower()
            
            # Simple keyword detection for goodbye intent
            goodbye_keywords = [
                "bye", "goodbye", "farewell", "thanks", "thank you",
                "done", "finished", "complete", "exit", "quit", 
                "end", "stop", "that's all", "no more", "see you"
            ]
            
            return any(keyword in user_message for keyword in goodbye_keywords)
            
        except Exception as e:
            logger.error(f"Error detecting goodbye intent: {str(e)}")
            return False
