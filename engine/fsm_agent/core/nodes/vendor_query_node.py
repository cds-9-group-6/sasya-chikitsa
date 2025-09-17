"""
Vendor Query Node for FSM Agent workflow
Asks user if they want vendor information
"""

import logging
from typing import Dict, Any

from .base_node import BaseNode

try:
    from ..workflow_state import WorkflowState, add_message_to_state, set_error
except ImportError:
    from engine.fsm_agent.core.workflow_state import WorkflowState, add_message_to_state, set_error

logger = logging.getLogger(__name__)


class VendorQueryNode(BaseNode):
    """Vendor query node - asks user if they want vendor information"""
    
    @property
    def node_name(self) -> str:
        return "vendor_query"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute vendor query node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        
        try:
            vendor_query_msg = """🛒 **Would you like to see local vendor options?**

I can help you find:
• Local suppliers with current pricing
• Online vendors with delivery options
• Organic/chemical treatment alternatives

Would you like me to show you vendor options for the recommended treatments? (Yes/No)"""
            
            add_message_to_state(state, "assistant", vendor_query_msg)
            state["requires_user_input"] = True
            state["next_action"] = "await_vendor_response"
            
        except Exception as e:
            logger.error(f"Error in vendor query node: {str(e)}", exc_info=True)
            set_error(state, f"Vendor query error: {str(e)}")
            state["next_action"] = "error"
        
        return state
