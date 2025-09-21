"""
Session Manager for FSM Agent Workflow
Handles state persistence between LangGraph invocations
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .workflow_state import WorkflowState, create_initial_state

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session state persistence for the FSM Agent workflow"""
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize session manager
        
        Args:
            storage_dir: Directory to store session files (defaults to env var or /tmp/fsm_sessions)
        """
        if storage_dir is None:
            storage_dir = os.getenv("SESSION_STORAGE_DIR", "/tmp/fsm_sessions")
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        logger.info(f"SessionManager initialized with storage: {storage_dir}")
    
    def _get_session_file(self, session_id: str) -> str:
        """Get the file path for a session"""
        return os.path.join(self.storage_dir, f"{session_id}.json")
    
    def save_state(self, state: WorkflowState) -> None:
        """
        Save workflow state to disk
        
        Args:
            state: Current workflow state
        """
        try:
            # CRITICAL: Validate state integrity before saving
            if not self._validate_state_integrity(state):
                logger.error(f"❌ Refusing to save corrupted state for session {state.get('session_id', 'unknown')}")
                return
            
            session_file = self._get_session_file(state["session_id"])
            
            # Convert state to JSON-serializable format
            serializable_state = self._serialize_state(state)
            
            # Log key state information for debugging
            messages_count = len(state.get("messages", []))
            has_classification = bool(state.get("classification_results"))
            has_prescription = bool(state.get("prescription_data"))
            current_node = state.get("current_node", "unknown")
            
            logger.info(f"💾 Saving state for session {state['session_id']}")
            logger.info(f"   - Messages: {messages_count}")
            logger.info(f"   - Has classification: {has_classification}")
            logger.info(f"   - Has prescription: {has_prescription}")
            logger.info(f"   - Current node: {current_node}")
            
            with open(session_file, 'w') as f:
                json.dump(serializable_state, f, indent=2, default=str)
            
            logger.info(f"✅ Successfully saved state for session {state['session_id']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save state for session {state['session_id']}: {str(e)}")
    
    def load_state(self, session_id: str) -> Optional[WorkflowState]:
        """
        Load workflow state from disk
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Loaded state or None if not found/expired
        """
        try:
            session_file = self._get_session_file(session_id)
            
            if not os.path.exists(session_file):
                logger.info(f"📭 No saved state found for session {session_id}")
                return None
            
            # Check if session is expired (24 hours)
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(session_file))
            if file_age > timedelta(hours=24):
                logger.info(f"⏰ Session {session_id} expired, removing old state")
                os.remove(session_file)
                return None
            
            with open(session_file, 'r') as f:
                serialized_state = json.load(f)
            
            # Convert back to WorkflowState
            state = self._deserialize_state(serialized_state)
            
            logger.info(f"📂 Loaded state for session {session_id} with node: {state.get('current_node')}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Failed to load state for session {session_id}: {str(e)}")
            return None
    
    def get_or_create_state(self, session_id: str, user_message: str, 
                           user_image: Optional[str] = None, 
                           context: Optional[Dict[str, Any]] = None) -> WorkflowState:
        """
        Get existing state or create new one
        
        Args:
            session_id: Session ID
            user_message: Current user message
            user_image: Optional image
            context: Optional context
            
        Returns:
            WorkflowState (existing or new)
        """
        # Try to load existing state
        existing_state = self.load_state(session_id)
        
        if existing_state:
            logger.info(f"🔄 Continuing conversation for session {session_id}")
            # Update with new user message
            existing_state["user_message"] = user_message
            existing_state["last_update_time"] = datetime.now()
            
            # Add new user image if provided (but don't overwrite existing)
            if user_image and not existing_state.get("user_image"):
                existing_state["user_image"] = user_image
                logger.info(f"📸 Added new image to existing session {session_id}")
            
            # Preserve existing image if no new one provided
            elif user_image:
                logger.info(f"📸 Updating image for session {session_id}")
                existing_state["user_image"] = user_image
            
            # FIXED: Update context fields for existing sessions  
            if context:
                logger.info(f"🔄 Updating context for existing session {session_id}: {context}")
                
                # Update individual context fields (preserve existing if new context doesn't have them)
                existing_state["plant_type"] = context.get("plant_type") or existing_state.get("plant_type")
                existing_state["location"] = context.get("location") or existing_state.get("location") 
                existing_state["season"] = context.get("season") or existing_state.get("season")
                existing_state["growth_stage"] = context.get("growth_stage") or existing_state.get("growth_stage")
                
                # Update full context for tools (merge with existing)
                existing_context = existing_state.get("user_context", {})
                merged_context = {**existing_context, **context}
                existing_state["user_context"] = merged_context
                
                logger.info(f"✅ Updated context - location: {existing_state.get('location')}, season: {existing_state.get('season')}")
            else:
                logger.info(f"⚠️ No context provided for session {session_id}")
            
            # CRITICAL FIX: Check for message duplication before adding
            existing_messages = existing_state.get("messages", [])
            recent_user_messages = [msg for msg in existing_messages[-3:] if msg.get("role") == "user"]
            
            # Check if this exact message was already added recently (duplicate detection)
            duplicate_found = any(
                msg.get("content") == user_message 
                for msg in recent_user_messages
            )
            
            if not duplicate_found:
                # CRITICAL FIX: Clear old assistant_response ONLY if workflow is completed
                # This prevents old completed responses from being streamed with new requests
                current_node = existing_state.get("current_node", "")
                if "assistant_response" in existing_state and current_node == "completed":
                    logger.info(f"🧹 Clearing old completed assistant_response for session {session_id}")
                    existing_state["assistant_response"] = ""
                
                # Add user message to conversation history
                existing_state["messages"].append({
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat(),
                    "node": existing_state.get("current_node", "unknown"),
                    "image": user_image
                })
                logger.info(f"➕ Added new user message to session {session_id}")
            else:
                logger.warning(f"⚠️ Duplicate user message detected for session {session_id}, skipping addition")
                logger.warning(f"   Message: '{user_message[:50]}...'")
                
                # For duplicates, only clear if in completed state
                current_node = existing_state.get("current_node", "")
                if "assistant_response" in existing_state and current_node == "completed":
                    existing_state["assistant_response"] = ""
            
            return existing_state
        
        else:
            logger.info(f"🆕 Creating new session {session_id}")
            new_state = create_initial_state(session_id, user_message, user_image, context)
            # Save the new state immediately so session existence checks work
            self.save_state(new_state)
            return new_state
    
    def deduplicate_messages(self, state: WorkflowState) -> WorkflowState:
        """
        Remove duplicate messages from session state
        
        Args:
            state: Workflow state to clean
            
        Returns:
            Cleaned state with duplicates removed
        """
        if "messages" not in state or not state["messages"]:
            return state
        
        messages = state["messages"]
        if len(messages) <= 1:
            return state
        
        # Track unique messages by content + role + timestamp to avoid duplicates
        seen_messages = set()
        deduplicated_messages = []
        
        for message in messages:
            # Create a unique key for each message
            message_key = (
                message.get("role", ""),
                message.get("content", ""),
                message.get("timestamp", "")
            )
            
            if message_key not in seen_messages:
                seen_messages.add(message_key)
                deduplicated_messages.append(message)
            else:
                logger.debug(f"🗑️ Removed duplicate message: {message.get('content', '')[:50]}...")
        
        # Update state with deduplicated messages
        original_count = len(messages)
        deduplicated_count = len(deduplicated_messages)
        
        if original_count != deduplicated_count:
            state["messages"] = deduplicated_messages
            logger.info(f"✅ Deduplication complete: {original_count} → {deduplicated_count} messages")
        else:
            logger.info("✅ No duplicate messages found")
        
        return state
    
    def _serialize_state(self, state: WorkflowState) -> Dict[str, Any]:
        """Convert WorkflowState to JSON-serializable format"""
        serialized = {}
        
        for key, value in state.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
                
        return serialized
    
    def _deserialize_state(self, data: Dict[str, Any]) -> WorkflowState:
        """Convert JSON data back to WorkflowState"""
        state = data.copy()
        
        # Convert datetime strings back to datetime objects
        for key in ["workflow_start_time", "last_update_time"]:
            if key in state and isinstance(state[key], str):
                try:
                    state[key] = datetime.fromisoformat(state[key])
                except ValueError:
                    state[key] = datetime.now()
        
        return state
    
    def cleanup_expired_sessions(self) -> None:
        """Remove expired session files"""
        try:
            current_time = datetime.now()
            removed_count = 0
            
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.storage_dir, filename)
                    file_age = current_time - datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_age > timedelta(hours=24):
                        os.remove(file_path)
                        removed_count += 1
            
            if removed_count > 0:
                logger.info(f"🧹 Cleaned up {removed_count} expired sessions")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired sessions: {str(e)}")
    
    def _validate_state_integrity(self, state: WorkflowState) -> bool:
        """
        Validate that the state hasn't been corrupted
        
        Args:
            state: WorkflowState to validate
            
        Returns:
            True if state is valid, False if corrupted
        """
        try:
            # Check required fields
            required_fields = ["session_id", "messages", "current_node"]
            for field in required_fields:
                if field not in state:
                    logger.error(f"❌ State corruption: Missing required field '{field}'")
                    return False
            
            # Check messages structure
            messages = state.get("messages", [])
            if not isinstance(messages, list):
                logger.error(f"❌ State corruption: messages field is not a list")
                return False
            
            # Check for message structure integrity
            for i, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    logger.error(f"❌ State corruption: Message {i} is not a dict")
                    return False
                if "role" not in msg or "content" not in msg:
                    logger.error(f"❌ State corruption: Message {i} missing required fields")
                    return False
            
            # Check for excessive message duplication (sign of bug)
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if len(user_messages) > 1:
                content_counts = {}
                for msg in user_messages:
                    content = msg.get("content", "")
                    content_counts[content] = content_counts.get(content, 0) + 1
                
                # Check for duplicates
                duplicates = {content: count for content, count in content_counts.items() if count > 1}
                if duplicates:
                    logger.warning(f"⚠️ State validation: Message duplicates found in session {state.get('session_id')}")
                    for content, count in duplicates.items():
                        logger.warning(f"   - '{content[:50]}...' appears {count} times")
                        # Don't fail validation for duplicates, just warn (we'll fix them)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ State validation error: {str(e)}")
            return False
