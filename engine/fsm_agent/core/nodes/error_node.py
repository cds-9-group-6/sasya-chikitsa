"""
Error Node for FSM Agent workflow
Handles errors
"""

import logging

from .base_node import BaseNode

try:
    from ..workflow_state import WorkflowState, add_message_to_state, mark_complete
except ImportError:
    from engine.fsm_agent.core.workflow_state import WorkflowState, add_message_to_state, mark_complete

logger = logging.getLogger(__name__)


class ErrorNode(BaseNode):
    """Error node - handles errors"""
    
    @property
    def node_name(self) -> str:
        return "error"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute error node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        
        error_msg = state.get("error_message", "An unknown error occurred")
        add_message_to_state(
            state,
            "assistant",
            f"❌ **Error:** {error_msg}\n\nPlease try again or contact support if the issue persists."
        )
        
        mark_complete(state)
        return state
