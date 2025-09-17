"""
FastAPI Server for Dynamic Planning Agent using LangGraph

This module provides a FastAPI server interface for the FSM-based planning agent.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os
from contextlib import asynccontextmanager

# Custom JSON encoder to handle datetime objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

from fsm_agent.core.fsm_agent import DynamicPlanningAgent

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global agent instance
agent: Optional[DynamicPlanningAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global agent
    
    # Initialize agent on startup
    llm_config = {
        "model": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "temperature": 0.1,
    }
    
    try:
        agent = DynamicPlanningAgent(llm_config)
        logger.info("Dynamic Planning Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}")
        agent = None
    
    yield
    
    # Cleanup on shutdown
    if agent:
        logger.info("Shutting down Dynamic Planning Agent")


# Create FastAPI app with lifespan manager
app = FastAPI(
    title="Dynamic Planning Agent API",
    description="LangGraph-based FSM agent for plant disease diagnosis and prescription",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== REQUEST/RESPONSE MODELS ====================

class ChatRequest(BaseModel):
    """Request model for chat endpoints"""
    session_id: Optional[str] = None
    message: str = Field(..., description="User message")
    image_b64: Optional[str] = Field(None, description="Base64 encoded image")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    """Response model for chat endpoints"""
    success: bool
    session_id: str
    messages: list
    state: Optional[str] = None
    is_complete: bool = False
    requires_user_input: bool = False
    classification_results: Optional[Dict[str, Any]] = None
    prescription_data: Optional[Dict[str, Any]] = None
    vendor_options: Optional[list] = None
    error: Optional[str] = None


class SessionInfoResponse(BaseModel):
    """Response model for session info"""
    success: bool
    session_id: Optional[str] = None
    created_at: Optional[str] = None
    last_activity: Optional[str] = None
    message_count: Optional[int] = None
    current_state: Optional[str] = None
    is_complete: bool = False
    has_classification: bool = False
    has_prescription: bool = False
    has_vendors: bool = False
    error: Optional[str] = None


class AgentStatsResponse(BaseModel):
    """Response model for agent statistics"""
    active_sessions: int
    total_messages: int
    llm_config: Dict[str, Any]
    uptime_seconds: float


# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Dynamic Planning Agent API",
        "version": "1.0.0",
        "status": "active" if agent else "unavailable"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": agent.get_active_sessions_count()
    }


@app.post("/sasya-chikitsa/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message (non-streaming)
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if request.session_id:
            # Continue existing session
            result = await agent.process_message(
                request.session_id, 
                request.message, 
                request.image_b64
            )
        else:
            # Start new session
            result = await agent.start_session(
                request.message, 
                request.image_b64,
                request.context
            )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
        
        # Format response
        session_data = result.get("result", result)
        
        return ChatResponse(
            success=True,
            session_id=session_data.get("session_id"),
            messages=session_data.get("messages", []),
            state=session_data.get("state"),
            is_complete=session_data.get("is_complete", False),
            requires_user_input=session_data.get("requires_user_input", False),
            classification_results=session_data.get("classification_results"),
            prescription_data=session_data.get("prescription_data"),
            vendor_options=session_data.get("vendor_options")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sasya-chikitsa/chat-stream")
async def chat_stream(request: ChatRequest):
    """
    Process a chat message with streaming response
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    async def generate_stream():
        try:
            if request.session_id:
                # Continue existing session
                async for chunk in agent.stream_message(
                    request.session_id, 
                    request.message, 
                    request.image_b64,
                    request.context
                ):
                    chunk_type = chunk.get("type", "unknown")
                    
                    # FIXED: Support both state_update AND assistant_response events for modular architecture
                    
                    if chunk_type == "state_update":
                        # Stream clean state updates (metadata, progress, etc.)
                        state_data = chunk.get("data", {})
                        if isinstance(state_data, dict) and state_data:
                            yield f"event: state_update\ndata: {json.dumps(state_data, cls=CustomJSONEncoder)}\n\n"
                    
                    elif chunk_type == "assistant_response":
                        # FIXED: Stream dedicated assistant responses (final answers for users)
                        response_data = chunk.get("data", {})
                        if isinstance(response_data, dict) and response_data:
                            yield f"event: assistant_response\ndata: {json.dumps(response_data, cls=CustomJSONEncoder)}\n\n"
                    
                    elif chunk_type == "attention_overlay":
                        # Stream attention overlay visualization data
                        overlay_data = chunk.get("data", {})
                        if isinstance(overlay_data, dict) and overlay_data.get("attention_overlay"):
                            yield f"event: attention_overlay\ndata: {json.dumps(overlay_data, cls=CustomJSONEncoder)}\n\n"
                            logger.info(f"🎯 Streamed attention overlay for session {chunk.get('session_id')}")
                    
                    elif chunk_type == "error":
                        # Stream error
                        error = chunk.get("error", "Unknown error")
                        yield f"event: error\ndata: {json.dumps({'error': error})}\n\n"
                        yield f"data: ❌ Error: {error}\n\n"
                        break
            else:
                # Start new session - create session first, then stream the workflow
                import uuid
                from datetime import datetime
                
                # Generate new session ID
                new_session_id = f"session_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
                
                yield f"data: 🚀 Starting new session: {new_session_id}\n\n"
                yield f"event: session_start\ndata: Session {new_session_id} created\n\n"
                
                # Stream the workflow execution for the new session
                async for chunk in agent.stream_message(
                    new_session_id,
                    request.message, 
                    request.image_b64,
                    request.context
                ):
                    chunk_type = chunk.get("type", "unknown")
                    
                    # Remove message streaming - all content is in state_update to prevent duplication
                    
                    if chunk_type == "state_update":
                        # Stream ONLY clean state updates (no duplication, no separate events)
                        state_data = chunk.get("data", {})
                        if isinstance(state_data, dict) and state_data:
                            # Single clean state update - contains all necessary information
                            yield f"event: state_update\ndata: {json.dumps(state_data, cls=CustomJSONEncoder)}\n\n"
                    
                    elif chunk_type == "attention_overlay":
                        # Stream attention overlay visualization data
                        overlay_data = chunk.get("data", {})
                        if isinstance(overlay_data, dict) and overlay_data.get("attention_overlay"):
                            yield f"event: attention_overlay\ndata: {json.dumps(overlay_data, cls=CustomJSONEncoder)}\n\n"
                            logger.info(f"🎯 Streamed attention overlay for new session {chunk.get('session_id')}")
                    
                    elif chunk_type == "error":
                        # Stream error
                        error = chunk.get("error", "Unknown error")
                        yield f"event: error\ndata: {json.dumps({'error': error})}\n\n"
                        yield f"data: ❌ Error: {error}\n\n"
                        break
            
            yield "event: done\ndata: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming: {str(e)}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.get("/sasya-chikitsa/session/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(session_id: str):
    """
    Get information about a specific session
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent.get_session_info(session_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Session not found"))
        
        return SessionInfoResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sasya-chikitsa/session/{session_id}/history")
async def get_conversation_history(session_id: str):
    """
    Get conversation history for a session
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent.get_conversation_history(session_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Session not found"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sasya-chikitsa/session/{session_id}/classification")
async def get_classification_results(session_id: str):
    """
    Get classification results for a session
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent.get_classification_results(session_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Classification results not found"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting classification results: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sasya-chikitsa/session/{session_id}/prescription")
async def get_prescription_data(session_id: str):
    """
    Get prescription data for a session
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent.get_prescription_data(session_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Prescription data not found"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prescription data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sasya-chikitsa/session/{session_id}")
async def end_session(session_id: str):
    """
    End a specific session
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent.end_session(session_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Session not found"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sasya-chikitsa/stats", response_model=AgentStatsResponse)
async def get_agent_stats():
    """
    Get agent statistics
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        stats = agent.get_agent_stats()
        return AgentStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sasya-chikitsa/cleanup")
async def cleanup_sessions(background_tasks: BackgroundTasks, max_inactive_hours: int = 24):
    """
    Clean up inactive sessions
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    def cleanup_task():
        agent.cleanup_inactive_sessions(max_inactive_hours)
    
    background_tasks.add_task(cleanup_task)
    
    return {
        "message": "Session cleanup scheduled",
        "max_inactive_hours": max_inactive_hours
    }


# ==================== SERVER UTILITIES ====================

class FSMServer:
    """
    Utility class for running the FSM server
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
    
    def run(self, **kwargs):
        """
        Run the server
        
        Args:
            **kwargs: Additional uvicorn configuration
        """
        config = {
            "host": self.host,
            "port": self.port,
            "log_level": "info",
            "access_log": True,
            **kwargs
        }
        
        logger.info(f"Starting FSM server on {self.host}:{self.port}")
        
        # Use import string when reload or workers are specified to avoid warning
        if config.get("reload") or config.get("workers", 1) > 1:
            # Use import string format for reload/workers compatibility
            uvicorn.run("fsm_agent.server.fsm_server:app", **config)
        else:
            # Use app object directly for normal operation
            uvicorn.run(app, **config)


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Dynamic Planning Agent Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8002, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run server
    server = FSMServer(args.host, args.port)
    server.run(
        log_level=args.log_level,
        reload=args.reload
    )
