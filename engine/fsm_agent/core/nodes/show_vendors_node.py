"""
Show Vendors Node for FSM Agent workflow
Displays vendor options and pricing
"""

import logging
from typing import Dict, Any, List

from .base_node import BaseNode

try:
    from ..workflow_state import WorkflowState, add_message_to_state, set_error
    from ...tools.vendor_tool import VendorTool
except ImportError:
    from engine.fsm_agent.core.workflow_state import WorkflowState, add_message_to_state, set_error
    from engine.fsm_agent.tools.vendor_tool import VendorTool

logger = logging.getLogger(__name__)


class ShowVendorsNode(BaseNode):
    """Show vendors node - displays vendor options and pricing"""
    
    @property
    def node_name(self) -> str:
        return "show_vendors"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute show vendors node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        
        try:
            if not state.get("treatment_recommendations"):
                set_error(state, "No treatment recommendations available for vendor search")
                state["next_action"] = "error"
                return state
            
            add_message_to_state(
                state,
                "assistant",
                "🔍 Searching for local vendors and current pricing..."
            )
            
            # Run vendor tool
            vendor_tool = self.tools["vendor"]
            
            # Debug logging to verify context flow
            logger.info(f"Vendor context - location: {state.get('location', '')}")
            logger.info(f"User preferences for vendor: {state.get('user_context', {})}")
            
            vendor_input = {
                "treatments": state["treatment_recommendations"],
                "location": state.get("location", ""),
                "user_preferences": state.get("user_context", {})
            }
            
            result = await vendor_tool.arun(vendor_input)
            
            if result and not result.get("error"):
                self._process_successful_vendor_search(state, result)
            else:
                self._process_failed_vendor_search(state, result)
        
        except Exception as e:
            logger.error(f"Error in show vendors node: {str(e)}", exc_info=True)
            self._handle_vendor_search_exception(state, e)
        
        return state
    
    def _process_successful_vendor_search(self, state: WorkflowState, result: Dict[str, Any]) -> None:
        """Process successful vendor search results"""
        state["vendor_options"] = result.get("vendors", [])
        
        # Format vendor response
        response = self._format_vendor_response(result.get("vendors", []))
        
        if state["vendor_options"]:
            response += "\n\n💡 Would you like to proceed with ordering from any of these vendors? Please let me know which option interests you, or say 'no' if you'd prefer not to order right now."
        
        # Store response for streaming and add to messages
        state["assistant_response"] = response
        
        # GENERIC ARCHITECTURAL FIX: Set streaming metadata for modular duplicate prevention
        state["response_status"] = "final"  # This is the enhanced, final version ready for streaming
        state["stream_immediately"] = True  # Node indicates immediate streaming needed
        state["stream_in_state_update"] = False  # Don't include in state_update events
        
        add_message_to_state(state, "assistant", response)
        
        if state["vendor_options"]:
            state["requires_user_input"] = True
            state["next_action"] = "await_vendor_selection"
        else:
            state["next_action"] = "complete"
    
    def _process_failed_vendor_search(self, state: WorkflowState, result: Dict[str, Any]) -> None:
        """Process failed vendor search"""
        error_msg = result.get("error", "Vendor search failed") if result else "Vendor tool returned no result"
        add_message_to_state(
            state,
            "assistant",
            f"⚠️ Unable to fetch vendor information: {error_msg}. You can still proceed with the treatment recommendations using local suppliers."
        )
        state["next_action"] = "complete"
    
    def _handle_vendor_search_exception(self, state: WorkflowState, exception: Exception) -> None:
        """Handle exceptions during vendor search"""
        add_message_to_state(
            state,
            "assistant",
            f"⚠️ Error searching for vendors: {str(exception)}. You can still proceed with the treatment recommendations using local suppliers."
        )
        state["next_action"] = "complete"
    
    def _format_vendor_response(self, vendors: List[Dict[str, Any]]) -> str:
        """Format vendor data into a readable response"""
        if not vendors:
            return "🔍 **No vendors found** in your area for the recommended treatments. Please check with local agricultural suppliers."
        
        response = "🛒 **Vendor Options**\n\n"
        
        for i, vendor in enumerate(vendors, 1):
            response += f"**{i}. {vendor.get('name', 'Unknown Vendor')}**\n"
            response += f"   • Location: {vendor.get('location', 'N/A')}\n"
            response += f"   • Contact: {vendor.get('contact', 'N/A')}\n"
            response += f"   • Delivery: {vendor.get('delivery_options', 'N/A')}\n"
            response += f"   • Total Price: ₹{vendor.get('total_price', 'N/A')}\n"
            
            items = vendor.get('items', [])
            if items:
                response += "   • Available Items:\n"
                for item in items:
                    response += f"     - {item.get('name', 'N/A')}: ₹{item.get('price', 'N/A')}\n"
            
            response += "\n"
        
        return response
