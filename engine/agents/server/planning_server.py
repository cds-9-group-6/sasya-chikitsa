#!/usr/bin/env python3
"""
Planning Agent FastAPI Server

A standalone FastAPI server for the multi-step planning agent system.
Run with: python planning_server.py or uvicorn planning_server:app --reload
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the necessary directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
agents_dir = os.path.dirname(current_dir)
engine_dir = os.path.dirname(agents_dir)
project_root = os.path.dirname(engine_dir)

# Add paths in correct order
for path in [agents_dir, engine_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

from agents.server.planning_agent import PlanningAgent, WorkflowState
from agents.session.session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('../planning_agent.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class PlanningChatRequest(BaseModel):
    """Extended chat request for planning agent."""
    session_id: Optional[str] = "default"
    message: str = ""
    image_b64: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    workflow_action: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    components: Dict[str, str]
    timestamp: str

# Global planning agent instance
planning_agent: Optional[PlanningAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    global planning_agent
    logger.info("🚀 Starting Planning Agent Server...")
    
    try:
        planning_agent = PlanningAgent()
        logger.info("✅ Planning Agent initialized successfully")
        yield
    except Exception as e:
        logger.error(f"❌ Failed to initialize Planning Agent: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down Planning Agent Server...")
        if planning_agent:
            # Clean up any resources if needed
            logger.info("✅ Planning Agent cleanup completed")

# Create FastAPI application
app = FastAPI(
    title="Sasya Chikitsa - Planning Agent API",
    description="Multi-step plant disease diagnosis planning agent system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development
        "http://localhost:8080",  # Vue development  
        "http://localhost:8000",  # Local development
        "http://10.0.2.2:3000",   # Android emulator
        "http://10.0.2.2:8080",   # Android emulator
        "*"  # Allow all origins for development (restrict in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for debugging."""
    start_time = asyncio.get_event_loop().time()
    
    # Log request details
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"📥 {request.method} {request.url.path} from {client_ip}")
    
    response = await call_next(request)
    
    # Log response time
    process_time = asyncio.get_event_loop().time() - start_time
    logger.info(f"📤 Response: {response.status_code} in {process_time:.3f}s")
    
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again."
        }
    )

# Health check endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    import datetime
    
    components_status = {
        "planning_agent": "healthy" if planning_agent else "unhealthy",
        "session_manager": "healthy",
        "workflow_controller": "healthy"
    }
    
    return HealthResponse(
        status="healthy" if all(status == "healthy" for status in components_status.values()) else "unhealthy",
        version="1.0.0",
        components=components_status,
        timestamp=datetime.datetime.utcnow().isoformat()
    )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "🌱 Sasya Chikitsa Planning Agent API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "planning_chat": "/planning/chat",
            "planning_stream": "/planning/chat-stream",
            "session_info": "/planning/session/{session_id}",
            "restart_session": "/planning/session/{session_id}/restart",
            "available_actions": "/planning/session/{session_id}/actions"
        },
        "documentation": "/docs"
    }

# Planning Agent Endpoints

@app.post("/planning/chat")
async def planning_chat(req: PlanningChatRequest):
    """
    Main planning agent chat endpoint.
    Processes user requests through the multi-step workflow.
    """
    try:
        if not planning_agent:
            raise HTTPException(status_code=503, detail="Planning agent not available")
        
        logger.info(f"🎯 Planning chat request: session={req.session_id}, has_image={bool(req.image_b64)}")
        logger.debug(f"   Message: '{req.message[:100]}...'")
        
        result = await planning_agent.process_user_request(
            session_id=req.session_id or "default",
            user_input=req.message,
            image_data=req.image_b64,
            context=req.context or {}
        )
        
        return {
            "success": result.success,
            "response": result.response,
            "current_state": result.current_state.value,
            "next_actions": result.next_actions,
            "requires_user_input": result.requires_user_input,
            "error_message": result.error_message,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error(f"❌ Planning chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/planning/chat-stream")
async def planning_chat_stream(req: PlanningChatRequest):
    """
    Streaming version of planning agent chat.
    Streams progress updates and results in real-time.
    """
    try:
        if not planning_agent:
            raise HTTPException(status_code=503, detail="Planning agent not available")
        
        logger.info(f"🌊 Planning stream request: session={req.session_id}")
        
        async def stream_generator():
            try:
                # Emit initial status
                yield f"data: 🚀 Starting analysis...\n\n"
                await asyncio.sleep(0.1)
                
                # Get session summary for context
                session_summary = await planning_agent.get_session_summary(req.session_id or "default")
                current_state = session_summary.get('session_info', {}).get('current_state', 'initial')
                
                logger.debug(f"   Current state: {current_state}")
                
                # Emit progress based on current state and request content
                if current_state in ['initial', 'intent_capture'] and req.image_b64:
                    yield f"data: 📸 Processing uploaded image...\n\n"
                    await asyncio.sleep(0.5)
                    yield f"data: 🔍 Analyzing plant condition...\n\n"
                    await asyncio.sleep(1.0)
                    yield f"data: 🧠 Extracting features and context...\n\n"
                    await asyncio.sleep(0.3)
                
                elif current_state == 'clarification':
                    yield f"data: 💬 Analyzing your response...\n\n"
                    await asyncio.sleep(0.3)
                    yield f"data: 🎯 Determining next steps...\n\n"
                    await asyncio.sleep(0.2)
                
                elif current_state == 'classification':
                    yield f"data: 🔬 Running disease classification...\n\n"
                    await asyncio.sleep(0.8)
                    yield f"data: 🎯 Generating attention visualization...\n\n"
                    await asyncio.sleep(0.5)
                    yield f"data: 📊 Calculating confidence scores...\n\n"
                    await asyncio.sleep(0.3)
                
                elif current_state == 'prescription':
                    yield f"data: 📚 Searching treatment database...\n\n"
                    await asyncio.sleep(0.7)
                    yield f"data: 🎯 Personalizing recommendations...\n\n"
                    await asyncio.sleep(0.4)
                    yield f"data: 💊 Generating prescription options...\n\n"
                    await asyncio.sleep(0.3)
                
                elif current_state == 'vendor_recommendation':
                    yield f"data: 🏪 Finding local suppliers...\n\n"
                    await asyncio.sleep(0.5)
                    yield f"data: 💰 Calculating cost estimates...\n\n"
                    await asyncio.sleep(0.3)
                
                # Process the actual request
                logger.debug("   Invoking planning agent...")
                result = await planning_agent.process_user_request(
                    session_id=req.session_id or "default",
                    user_input=req.message,
                    image_data=req.image_b64,
                    context=req.context or {}
                )
                
                # Emit final result
                yield f"data: {result.response}\n\n"
                
                # Emit completion marker
                yield f"data: [DONE]\n\n"
                
                logger.info("✅ Planning stream completed successfully")
                
            except Exception as e:
                logger.error(f"❌ Stream generation error: {e}")
                yield f"data: ❌ Error: {str(e)}\n\n"
                yield f"data: [ERROR]\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache", 
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Planning stream error: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")

@app.get("/planning/session/{session_id}")
async def get_planning_session(session_id: str):
    """Get current planning session state and history."""
    try:
        if not planning_agent:
            raise HTTPException(status_code=503, detail="Planning agent not available")
        
        logger.info(f"📊 Getting session info: {session_id}")
        session_summary = await planning_agent.get_session_summary(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "summary": session_summary,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"❌ Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Session retrieval error: {str(e)}")

@app.post("/planning/session/{session_id}/restart")
async def restart_planning_session(session_id: str):
    """Restart a planning session from the beginning."""
    try:
        if not planning_agent:
            raise HTTPException(status_code=503, detail="Planning agent not available")
        
        logger.info(f"🔄 Restarting session: {session_id}")
        result = await planning_agent.restart_session(session_id)
        
        return {
            "success": result.success,
            "message": "Session restarted successfully",
            "response": result.response,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"❌ Error restarting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Session restart error: {str(e)}")

@app.get("/planning/session/{session_id}/actions")
async def get_available_actions(session_id: str):
    """Get available actions for current session state."""
    try:
        if not planning_agent:
            raise HTTPException(status_code=503, detail="Planning agent not available")
        
        logger.debug(f"🎮 Getting available actions: {session_id}")
        actions = await planning_agent.get_available_actions(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "available_actions": actions,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"❌ Error getting actions for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Actions retrieval error: {str(e)}")

@app.delete("/planning/session/{session_id}")
async def delete_planning_session(session_id: str):
    """Delete/clear a planning session."""
    try:
        if not planning_agent:
            raise HTTPException(status_code=503, detail="Planning agent not available")
        
        logger.info(f"🗑️ Deleting session: {session_id}")
        await planning_agent.restart_session(session_id)  # This clears the session
        
        return {
            "success": True,
            "message": f"Session {session_id} deleted successfully",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"❌ Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Session deletion error: {str(e)}")

# Development and debugging endpoints

@app.get("/planning/debug/sessions")
async def debug_all_sessions():
    """Debug endpoint to see all active sessions."""
    try:
        if not planning_agent:
            raise HTTPException(status_code=503, detail="Planning agent not available")
        
        # This would need to be implemented in SessionManager
        logger.info("🐛 Debug: Getting all sessions")
        return {
            "success": True,
            "message": "Debug endpoint - session listing not yet implemented",
            "active_sessions": [],
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"❌ Debug sessions error: {e}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")

def main():
    """Main function to run the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Planning Agent FastAPI Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🐛 Debug mode enabled")
    
    logger.info(f"🚀 Starting Planning Agent Server on {args.host}:{args.port}")
    
    try:
        uvicorn.run(
            "planning_server:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info" if not args.debug else "debug",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()
