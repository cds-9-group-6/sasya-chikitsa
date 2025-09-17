"""
Main Dynamic Planning Agent using LangGraph

This module provides the main interface for the FSM-based planning agent.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import uuid

from .langgraph_workflow import DynamicPlanningWorkflow
from .workflow_state import create_initial_state, WorkflowState

logger = logging.getLogger(__name__)


class DynamicPlanningAgent:
    """
    Main interface for the Dynamic Planning Agent using LangGraph
    
    This agent provides a conversational interface for plant disease diagnosis
    and prescription using a state machine approach with LLM-driven transitions.
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize the Dynamic Planning Agent
        
        Args:
            llm_config: Configuration for the LLM (model, base_url, etc.)
        """
        self.workflow = DynamicPlanningWorkflow(llm_config)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.llm_config = llm_config
        
        logger.info("Dynamic Planning Agent initialized")
    
    async def start_session(self, user_message: str, user_image: Optional[str] = None, 
                          context: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a new session or continue existing one
        
        Args:
            user_message: Initial user message
            user_image: Optional base64 encoded image
            context: Optional context dict with plant_type, location, season, etc.
            session_id: Optional session ID (generates new if not provided)
        
        Returns:
            Dictionary containing session info and initial response
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = f"session_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
            
            # Create initial state
            initial_state = create_initial_state(session_id, user_message, user_image)
            
            # Store session
            self.sessions[session_id] = {
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "state": initial_state,
                "message_count": 1
            }
            
            # Process initial message
            result = await self.workflow.process_message(session_id, user_message, user_image, context)
            
            # Update session
            if session_id in self.sessions:
                self.sessions[session_id]["last_activity"] = datetime.now()
                self.sessions[session_id]["message_count"] += 1
            
            logger.info(f"Session {session_id} started successfully")
            
            return {
                "success": True,
                "session_id": session_id,
                "result": result
            }
            
        except Exception as e:
            error_msg = f"Failed to start session: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    async def process_message(self, session_id: str, user_message: str, 
                            user_image: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a message in an existing session
        
        Args:
            session_id: Session identifier
            user_message: User's message
            user_image: Optional base64 encoded image
        
        Returns:
            Dictionary containing response and state information
        """
        try:
            # Check if session exists in SessionManager (persistent storage)
            session_manager = self.workflow.session_manager
            session_exists = self._session_exists(session_id, session_manager)
            
            if not session_exists:
                # Session doesn't exist - create a new one gracefully
                logger.info(f"Session {session_id} not found, creating new session")
                
                # Create initial state for this session
                from .workflow_state import create_initial_state
                initial_state = create_initial_state(session_id, user_message, user_image, context)
                
                # Save the new session
                session_manager.save_state(initial_state)
            
            # Update session activity in local tracking
            if session_id not in self.sessions:
                # Session exists in persistent storage but not in local memory (e.g., after restart)
                self.sessions[session_id] = {
                    "created_at": datetime.now(),  # We don't know the real creation time
                    "last_activity": datetime.now(),
                    "message_count": 0  # This will be incremented below
                }
            
            self.sessions[session_id]["last_activity"] = datetime.now()
            self.sessions[session_id]["message_count"] += 1
            
            # Process message through workflow
            result = await self.workflow.process_message(session_id, user_message, user_image, context)
            
            # Check if session was ended
            if result.get("session_ended"):
                # Remove from local tracking when session ends
                if session_id in self.sessions:
                    del self.sessions[session_id]
                logger.info(f"Session {session_id} ended and removed from tracking")
            
            logger.info(f"Message processed for session {session_id}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to process message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "session_id": session_id
            }
    
    def _session_exists(self, session_id: str, session_manager) -> bool:
        """
        Check if a session exists using the persistent SessionManager
        
        Args:
            session_id: Session identifier
            session_manager: The SessionManager instance
            
        Returns:
            True if session exists, False otherwise
        """
        try:
            # Try to get the session file path and check if it exists
            import os
            session_file_path = session_manager._get_session_file(session_id)
            return os.path.exists(session_file_path)
        except Exception as e:
            logger.error(f"Error checking session existence: {str(e)}")
            return False
    
    async def stream_message(self, session_id: str, user_message: str, 
                           user_image: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream process a message in an existing session or create new session if not found
        
        Args:
            session_id: Session identifier
            user_message: User's message
            user_image: Optional base64 encoded image
            context: Optional context dict with plant_type, location, season, etc.
        
        Yields:
            Stream of responses and state updates
        """
        try:
            # Check if session exists in persistent storage
            session_manager = self.workflow.session_manager
            session_exists = self._session_exists(session_id, session_manager)
            
            if not session_exists:
                # Session doesn't exist - create a new one gracefully
                logger.info(f"Session {session_id} not found, creating new session for streaming")
                
                # Create initial state for this session
                from .workflow_state import create_initial_state
                initial_state = create_initial_state(session_id, user_message, user_image, context)
                
                # Save the new session
                session_manager.save_state(initial_state)
                
                # Yield session creation notification
                yield {
                    "type": "session_created",
                    "session_id": session_id,
                    "message": f"New session {session_id} created"
                }
            
            # Update local session tracking
            if session_id not in self.sessions:
                # Session exists in persistent storage but not in local memory
                self.sessions[session_id] = {
                    "created_at": datetime.now(),
                    "last_activity": datetime.now(),
                    "message_count": 0
                }
            
            self.sessions[session_id]["last_activity"] = datetime.now()
            self.sessions[session_id]["message_count"] += 1
            
            # Stream process message through workflow
            session_ended = False
            async for chunk in self.workflow.stream_process_message(session_id, user_message, user_image, context):
                # Check if this chunk indicates session ending
                if chunk.get("type") == "state_update" and chunk.get("data", {}).get("session_ended"):
                    session_ended = True
                
                yield chunk
            
            # Clean up session if it was ended
            if session_ended and session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Session {session_id} ended and removed from tracking during streaming")
            
            logger.info(f"Streaming completed for session {session_id}")
            
        except Exception as e:
            error_msg = f"Failed to stream message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {
                "type": "error",
                "success": False,
                "error": error_msg,
                "session_id": session_id
            }
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary containing session information
        """
        try:
            if session_id not in self.sessions:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            session = self.sessions[session_id]
            
            return {
                "success": True,
                "session_id": session_id,
                "created_at": session["created_at"].isoformat(),
                "last_activity": session["last_activity"].isoformat(),
                "message_count": session["message_count"],
                "current_state": session["state"].get("current_node"),
                "is_complete": session["state"].get("is_complete", False),
                "has_classification": bool(session["state"].get("classification_results")),
                "has_prescription": bool(session["state"].get("prescription_data")),
                "has_vendors": bool(session["state"].get("vendor_options"))
            }
            
        except Exception as e:
            error_msg = f"Failed to get session info: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    async def get_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary containing conversation history
        """
        try:
            if session_id not in self.sessions:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            session = self.sessions[session_id]
            messages = session["state"].get("messages", [])
            
            return {
                "success": True,
                "session_id": session_id,
                "messages": messages,
                "total_messages": len(messages)
            }
            
        except Exception as e:
            error_msg = f"Failed to get conversation history: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    async def get_classification_results(self, session_id: str) -> Dict[str, Any]:
        """
        Get classification results for a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary containing classification results
        """
        try:
            if session_id not in self.sessions:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            session = self.sessions[session_id]
            classification_results = session["state"].get("classification_results")
            
            if not classification_results:
                return {
                    "success": False,
                    "error": "No classification results available"
                }
            
            return {
                "success": True,
                "session_id": session_id,
                "classification_results": classification_results
            }
            
        except Exception as e:
            error_msg = f"Failed to get classification results: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    async def get_prescription_data(self, session_id: str) -> Dict[str, Any]:
        """
        Get prescription data for a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary containing prescription data
        """
        try:
            if session_id not in self.sessions:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            session = self.sessions[session_id]
            prescription_data = session["state"].get("prescription_data")
            
            if not prescription_data:
                return {
                    "success": False,
                    "error": "No prescription data available"
                }
            
            return {
                "success": True,
                "session_id": session_id,
                "prescription_data": prescription_data
            }
            
        except Exception as e:
            error_msg = f"Failed to get prescription data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a session and clean up resources
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary containing operation result
        """
        try:
            if session_id not in self.sessions:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            # Get session info for final report
            session = self.sessions[session_id]
            message_count = session["message_count"]
            duration = datetime.now() - session["created_at"]
            
            # Remove session
            del self.sessions[session_id]
            
            logger.info(f"Session {session_id} ended. Messages: {message_count}, Duration: {duration}")
            
            return {
                "success": True,
                "session_id": session_id,
                "message_count": message_count,
                "duration_seconds": duration.total_seconds()
            }
            
        except Exception as e:
            error_msg = f"Failed to end session: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def cleanup_inactive_sessions(self, max_inactive_hours: int = 24):
        """
        Clean up inactive sessions
        
        Args:
            max_inactive_hours: Maximum hours of inactivity before cleanup
        """
        try:
            current_time = datetime.now()
            inactive_sessions = []
            
            for session_id, session in self.sessions.items():
                last_activity = session["last_activity"]
                inactive_duration = current_time - last_activity
                
                if inactive_duration.total_seconds() > (max_inactive_hours * 3600):
                    inactive_sessions.append(session_id)
            
            # Remove inactive sessions
            for session_id in inactive_sessions:
                del self.sessions[session_id]
                logger.info(f"Cleaned up inactive session: {session_id}")
            
            logger.info(f"Cleaned up {len(inactive_sessions)} inactive sessions")
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}", exc_info=True)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "active_sessions": len(self.sessions),
            "total_messages": sum(session["message_count"] for session in self.sessions.values()),
            "llm_config": self.llm_config,
            "uptime_seconds": (datetime.now() - datetime.now()).total_seconds()  # This would be tracked differently in production
        }
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a session and clean up both local and persistent storage
        
        Args:
            session_id: Session identifier to end
            
        Returns:
            Dictionary containing operation result
        """
        try:
            session_manager = self.workflow.session_manager
            
            # Remove from persistent storage
            session_manager.clear_session(session_id)
            
            # Remove from local tracking
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            logger.info(f"Session {session_id} ended and cleaned up")
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "Session ended successfully"
            }
            
        except Exception as e:
            error_msg = f"Failed to end session {session_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "session_id": session_id
            }
