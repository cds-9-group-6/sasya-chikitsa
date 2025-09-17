"""
LangGraph State Schema for Dynamic Planning Agent

This module defines the state schema used by the LangGraph workflow
for plant disease diagnosis and prescription.
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from typing_extensions import NotRequired
import operator
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """
    State schema for the LangGraph workflow.
    
    This defines all the data that flows between nodes in the workflow.
    """
    
    # Session Management
    session_id: str
    current_node: str
    previous_node: NotRequired[Optional[str]]
    
    # User Input
    user_message: str
    user_image: NotRequired[Optional[str]]  # Base64 encoded image
    
    # User Context
    user_context: NotRequired[Dict[str, Any]]
    user_intent: NotRequired[Dict[str, bool]]  # Intent analysis: wants_classification, wants_prescription, etc.
    location: NotRequired[Optional[str]]
    season: NotRequired[Optional[str]]
    plant_type: NotRequired[Optional[str]]
    growth_stage: NotRequired[Optional[str]]
    
    # Classification Results
    classification_results: NotRequired[Dict[str, Any]]
    disease_name: NotRequired[Optional[str]]
    confidence: NotRequired[Optional[float]]
    attention_overlay: NotRequired[Optional[str]]
    
    # Prescription Data
    prescription_data: NotRequired[Dict[str, Any]]
    treatment_recommendations: NotRequired[List[Dict[str, Any]]]
    preventive_measures: NotRequired[List[str]]
    
    # Vendor Information
    vendor_options: NotRequired[List[Dict[str, Any]]]
    selected_vendor: NotRequired[Optional[Dict[str, Any]]]
    vendor_query_response: NotRequired[Optional[str]]
    
    # Order Information
    order_details: NotRequired[Dict[str, Any]]
    order_status: NotRequired[Optional[str]]
    
    # Conversation History (append-only list)
    messages: Annotated[List[Dict[str, Any]], operator.add]
    
    # Flow Control
    next_action: NotRequired[Optional[str]]
    requires_user_input: NotRequired[bool]
    is_complete: NotRequired[bool]
    
    # Session Lifecycle
    session_ended: NotRequired[bool]
    session_end_time: NotRequired[Optional[datetime]]
    
    # Error Handling
    error_message: NotRequired[Optional[str]]
    retry_count: NotRequired[int]
    max_retries: NotRequired[int]
    
    # Metadata
    workflow_start_time: NotRequired[datetime]
    last_update_time: NotRequired[datetime]
    
    # Tool Results
    tool_results: NotRequired[Dict[str, Any]]
    
    # LLM Responses
    llm_reasoning: NotRequired[Optional[str]]
    llm_decision: NotRequired[Optional[str]]
    
    # Assistant Responses (for streaming)
    assistant_response: NotRequired[Optional[str]]
    
    # Generic Streaming Control Metadata (Architecture-Friendly)
    response_status: NotRequired[Optional[str]]  # "final", "intermediate", "state_only"
    stream_immediately: NotRequired[Optional[bool]]  # Node-controlled immediate streaming
    stream_in_state_update: NotRequired[Optional[bool]]  # Include in state_update events


def create_initial_state(session_id: str, user_message: str, user_image: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> WorkflowState:
    """
    Create an initial workflow state
    
    Args:
        session_id: Unique session identifier
        user_message: Initial user message
        user_image: Optional base64 encoded image
        context: Optional context dict with plant_type, location, season, etc.
    
    Returns:
        Initial WorkflowState
    """
    now = datetime.now()
    
    state: WorkflowState = {
        "session_id": session_id,
        "current_node": "initial",
        "user_message": user_message,
        "messages": [],
        "retry_count": 0,
        "max_retries": 3,
        "requires_user_input": False,
        "is_complete": False,
        "workflow_start_time": now,
        "last_update_time": now,
        "user_context": {},
        "tool_results": {},
    }
    
    # Add user image if provided
    if user_image:
        state["user_image"] = user_image
    
    # Add context fields if provided
    if context:
        state["plant_type"] = context.get("plant_type")
        state["location"] = context.get("location")
        state["season"] = context.get("season")
        state["growth_stage"] = context.get("growth_stage")
        # Store full context for tools
        state["user_context"] = context
    
    # Add initial user message to conversation
    state["messages"] = [{
        "role": "user",
        "content": user_message,
        "timestamp": now.isoformat(),
        "node": "initial",
        "image": user_image
    }]
    
    return state


def add_message_to_state(state: WorkflowState, role: str, content: str, **metadata) -> None:
    """
    Add a message to the conversation history in the state with duplicate prevention
    
    Args:
        state: Current workflow state
        role: Message role (user/assistant/system)
        content: Message content
        **metadata: Additional metadata to include
    """
    # COMPREHENSIVE DUPLICATE PREVENTION: Check if this exact content was already added recently
    if "messages" not in state:
        state["messages"] = []
    
    existing_messages = state["messages"]
    
    # Check last 5 messages of the same role for duplicates
    recent_same_role_messages = [
        msg for msg in existing_messages[-5:] 
        if msg.get("role") == role
    ]
    
    # Check for exact content match (indicating duplicate)
    duplicate_found = any(
        msg.get("content") == content and 
        msg.get("node") == state.get("current_node")  # Same node context
        for msg in recent_same_role_messages
    )
    
    if duplicate_found:
        logger.warning(f"🚫 DUPLICATE PREVENTED: {role} message in {state.get('current_node')} node")
        logger.warning(f"   Content: '{content[:50]}...'")
        return  # Skip adding duplicate message
    
    # Create and add the message
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "node": state.get("current_node", "unknown"),
        **metadata
    }
    
    # Append to messages list
    state["messages"].append(message)
    logger.debug(f"✅ Added {role} message to state (node: {state.get('current_node')}, total: {len(state['messages'])})")


def update_state_node(state: WorkflowState, node_name: str) -> None:
    """
    Update the current node in the state
    
    Args:
        state: Current workflow state
        node_name: Name of the new current node
    """
    state["previous_node"] = state.get("current_node")
    state["current_node"] = node_name
    state["last_update_time"] = datetime.now()


def set_error(state: WorkflowState, error_message: str) -> None:
    """
    Set error state
    
    Args:
        state: Current workflow state
        error_message: Error message to set
    """
    state["error_message"] = error_message
    state["retry_count"] = state.get("retry_count", 0) + 1
    add_message_to_state(state, "system", f"Error: {error_message}")


def can_retry(state: WorkflowState) -> bool:
    """
    Check if operation can be retried
    
    Args:
        state: Current workflow state
    
    Returns:
        True if can retry, False otherwise
    """
    return state.get("retry_count", 0) < state.get("max_retries", 3)


def mark_complete(state: WorkflowState, final_message: Optional[str] = None) -> None:
    """
    Mark the workflow as complete
    
    Args:
        state: Current workflow state
        final_message: Optional final message to add
    """
    state["is_complete"] = True
    state["current_node"] = "completed"
    
    if final_message:
        add_message_to_state(state, "assistant", final_message)
