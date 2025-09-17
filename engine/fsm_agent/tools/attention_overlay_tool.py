"""
Attention Overlay Tool for retrieving stored attention visualizations from session state.

This tool allows users to request and view the attention overlay from previous classifications
without needing to re-run the classification process.
"""

import logging
from typing import Any, Dict, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AttentionOverlayInput(BaseModel):
    """Input schema for attention overlay requests."""
    
    request_type: str = Field(
        default="show_overlay",
        description="Type of attention overlay request (show_overlay, overlay_info)"
    )
    format_preference: str = Field(
        default="base64",
        description="Preferred format for the overlay (base64, description)"
    )


class AttentionOverlayTool(BaseTool):
    """
    Tool for retrieving stored attention overlays from session state.
    
    This tool provides access to previously generated attention visualizations
    without requiring re-classification of the plant image.
    """
    
    name: str = "attention_overlay_retriever"
    description: str = """
    Retrieve and display the attention overlay from the current session's classification results.
    
    Use this tool when users ask to:
    - "Show me the attention overlay"
    - "Can I see the attention map?"
    - "Display the attention visualization" 
    - "Show where the AI was looking"
    - "What parts of the image were important?"
    
    The tool will return the stored base64 attention overlay if available,
    or inform the user if no overlay exists (no previous classification).
    
    Input should include:
    - request_type: Type of request (show_overlay, overlay_info)
    - format_preference: Preferred format (base64, description)
    """
    
    args_schema: type[BaseModel] = AttentionOverlayInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_state: Optional[Dict[str, Any]] = None
    
    def set_state(self, state: Dict[str, Any]) -> None:
        """Set the current workflow state for this tool."""
        self._current_state = state
    
    def _run(self, 
             request_type: str = "show_overlay",
             format_preference: str = "base64") -> str:
        """
        Retrieve attention overlay from session state.
        
        Args:
            request_type: Type of overlay request
            format_preference: Format for the response
            
        Returns:
            Formatted response with overlay data or error message
        """
        try:
            # Check if we have access to current state
            if not self._current_state:
                logger.warning("No current state available for attention overlay retrieval")
                return self._format_no_state_response()
            
            # Extract classification results from state
            classification_results = self._current_state.get("classification_results", {})
            attention_overlay = self._current_state.get("attention_overlay")
            
            # Check if we have classification results
            if not classification_results:
                logger.info("No classification results found in session state")
                return self._format_no_classification_response()
            
            # Check if attention overlay exists
            if not attention_overlay:
                logger.info("No attention overlay found in classification results")
                return self._format_no_overlay_response(classification_results)
            
            # Handle different request types
            if request_type == "overlay_info":
                return self._format_overlay_info_response(classification_results, attention_overlay)
            
            # Default: return the overlay data
            return self._format_overlay_response(classification_results, attention_overlay, format_preference)
            
        except Exception as e:
            logger.error(f"Error retrieving attention overlay: {str(e)}")
            return self._format_error_response(str(e))
    
    async def _arun(self, 
                    request_type: str = "show_overlay",
                    format_preference: str = "base64") -> str:
        """Async version of the tool execution."""
        return self._run(request_type, format_preference)
    
    def _format_overlay_response(self, 
                               classification_results: Dict[str, Any],
                               attention_overlay: str,
                               format_preference: str) -> str:
        """Format the main overlay response."""
        
        disease_name = classification_results.get("disease_name", "Unknown")
        confidence = classification_results.get("confidence", 0.0)
        
        if format_preference == "description":
            return f"""
🎯 **Attention Overlay Available**

**Classification:** {disease_name}
**Confidence:** {confidence:.2%}

📋 **About the Attention Overlay:**
The attention overlay shows which parts of your plant image were most important for the AI's disease classification decision. Brighter/highlighted areas indicate regions that contributed more to the diagnosis.

💡 **How to View:**
The attention overlay is available as image data. Your app should display this as an overlay on the original plant image to show the AI's focus areas.

**Status:** ✅ Attention overlay ready for display
            """.strip()
        
        # Default: return base64 data with context
        return f"""
🎯 **Attention Overlay for {disease_name}**

**Confidence:** {confidence:.2%}
**Overlay Format:** Base64 encoded image

**Attention Overlay Data:**
{attention_overlay}

💡 **Usage:** This base64 string represents the attention heatmap showing which parts of your plant image were most important for the disease classification. Display this as an overlay on your original image to see where the AI focused its attention.
        """.strip()
    
    def _format_overlay_info_response(self, 
                                    classification_results: Dict[str, Any],
                                    attention_overlay: str) -> str:
        """Format response with overlay information."""
        
        disease_name = classification_results.get("disease_name", "Unknown")
        confidence = classification_results.get("confidence", 0.0)
        
        return f"""
📊 **Attention Overlay Information**

**Disease Detected:** {disease_name}
**Classification Confidence:** {confidence:.2%}
**Overlay Status:** ✅ Available

🔍 **What is an Attention Overlay?**
The attention overlay is a heatmap that visualizes which parts of your plant image the AI model focused on when making its disease classification decision. It helps you understand:

• **Symptom Location:** Where the disease symptoms are most visible
• **AI Focus Areas:** Which regions influenced the diagnosis most
• **Diagnostic Confidence:** How certain the model was about different image areas

💡 **Interpretation Tips:**
- Brighter areas = Higher attention/importance
- These areas likely contain key disease symptoms
- Multiple bright spots may indicate widespread infection
- Attention patterns can help validate the diagnosis

**Ready to Display:** The overlay data is stored and ready for visualization.
        """.strip()
    
    def _format_no_classification_response(self) -> str:
        """Format response when no classification exists."""
        return """
❌ **No Classification Available**

I don't see any plant disease classification results in your current session. To generate an attention overlay, you'll need to:

1. **Upload a plant image** 📸
2. **Request disease classification** 🔬
3. **Then ask for the attention overlay** 🎯

The attention overlay shows which parts of your image were important for the AI's diagnosis, but it's only available after a successful classification.

**Would you like to start by uploading a plant image for analysis?**
        """.strip()
    
    def _format_no_overlay_response(self, classification_results: Dict[str, Any]) -> str:
        """Format response when classification exists but no overlay."""
        
        disease_name = classification_results.get("disease_name", "Unknown")
        confidence = classification_results.get("confidence", 0.0)
        
        return f"""
⚠️ **Attention Overlay Not Available**

**Current Classification:**
- **Disease:** {disease_name}
- **Confidence:** {confidence:.2%}

**Issue:** While I have your classification results, the attention overlay wasn't generated or stored during the analysis process.

**Possible Reasons:**
• Classification was performed without attention visualization
• Overlay generation failed during processing
• Data wasn't properly stored in the session

**Solution:** Try re-running the classification with a new image to generate a fresh attention overlay, or contact support if this issue persists.
        """.strip()
    
    def _format_no_state_response(self) -> str:
        """Format response when no session state is available."""
        return """
❌ **Session State Not Available**

I'm unable to access your current session data to retrieve the attention overlay. This might happen if:

• Session has expired or been reset
• No active classification session exists
• System error accessing session storage

**Next Steps:**
1. Start a new classification session
2. Upload your plant image
3. Request disease analysis
4. Then ask for the attention overlay

**Would you like to begin a new plant disease analysis?**
        """.strip()
    
    def _format_error_response(self, error_message: str) -> str:
        """Format error response."""
        return f"""
❌ **Error Retrieving Attention Overlay**

An error occurred while trying to access your attention overlay:

**Error:** {error_message}

**Troubleshooting:**
• Try refreshing your session
• Re-run the plant classification
• Contact support if the issue persists

**Alternative:** Upload a new plant image for fresh analysis and attention overlay generation.
        """.strip()


def create_attention_overlay_tool() -> AttentionOverlayTool:
    """
    Factory function to create an AttentionOverlayTool instance.
    
    Returns:
        Configured AttentionOverlayTool instance
    """
    logger.info("Creating AttentionOverlayTool")
    
    return AttentionOverlayTool()


# Example usage and testing
if __name__ == "__main__":
    # Test the tool with sample data
    tool = create_attention_overlay_tool()
    
    # Test with no state
    result1 = tool._run()
    print("Test 1 - No State:")
    print(result1)
    print("\n" + "="*50 + "\n")
    
    # Test with state but no classification
    test_state1 = {"session_id": "test-123", "messages": []}
    tool.set_state(test_state1)
    result2 = tool._run()
    print("Test 2 - No Classification:")
    print(result2)
    print("\n" + "="*50 + "\n")
    
    # Test with classification but no overlay
    test_state2 = {
        "session_id": "test-123",
        "classification_results": {
            "disease_name": "Tomato Late Blight",
            "confidence": 0.92
        }
    }
    tool.set_state(test_state2)
    result3 = tool._run()
    print("Test 3 - No Overlay:")
    print(result3)
    print("\n" + "="*50 + "\n")
    
    # Test with full data
    test_state3 = {
        "session_id": "test-123",
        "classification_results": {
            "disease_name": "Tomato Late Blight",
            "confidence": 0.92
        },
        "attention_overlay": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    }
    tool.set_state(test_state3)
    result4 = tool._run()
    print("Test 4 - Full Data:")
    print(result4)
    print("\n" + "="*50 + "\n")
    
    # Test info request
    result5 = tool._run(request_type="overlay_info")
    print("Test 5 - Overlay Info:")
    print(result5)


