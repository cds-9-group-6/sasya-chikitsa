"""
Order Booking Node for FSM Agent workflow
Simulates order booking with selected vendor
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .base_node import BaseNode

try:
    from ..workflow_state import WorkflowState, add_message_to_state, set_error
except ImportError:
    from engine.fsm_agent.core.workflow_state import WorkflowState, add_message_to_state, set_error

logger = logging.getLogger(__name__)


class OrderBookingNode(BaseNode):
    """Order booking node - simulates order booking with selected vendor"""
    
    @property
    def node_name(self) -> str:
        return "order_booking"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute order booking node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        
        try:
            selected_vendor = state.get("selected_vendor")
            if not selected_vendor:
                set_error(state, "No vendor selected for order booking")
                state["next_action"] = "error"
                return state
            
            # Simulate order booking (this would integrate with actual vendor APIs)
            order_id = f"ORD-{state['session_id'][:8]}-{datetime.now().strftime('%Y%m%d%H%M')}"
            
            order_details = {
                "order_id": order_id,
                "vendor": selected_vendor,
                "items": state.get("treatment_recommendations", []),
                "total_amount": selected_vendor.get("total_price", 0),
                "status": "confirmed",
                "estimated_delivery": "3-5 business days"
            }
            
            state["order_details"] = order_details
            state["order_status"] = "confirmed"
            
            order_confirmation = f"""✅ **Order Confirmed!**

**Order ID:** {order_id}
**Vendor:** {selected_vendor.get('name', 'N/A')}
**Total Amount:** ₹{selected_vendor.get('total_price', 0)}
**Estimated Delivery:** 3-5 business days

Your order has been successfully placed! You should receive a confirmation email shortly with tracking details.

Is there anything else I can help you with regarding your plant care?"""
            
            add_message_to_state(state, "assistant", order_confirmation)
            state["requires_user_input"] = True
            state["next_action"] = "await_final_input"
            
        except Exception as e:
            logger.error(f"Error in order booking node: {str(e)}", exc_info=True)
            set_error(state, f"Order booking error: {str(e)}")
            state["next_action"] = "error"
        
        return state
