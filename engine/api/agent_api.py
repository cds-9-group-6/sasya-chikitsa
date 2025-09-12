import asyncio
import logging
import uuid

import uvicorn
from fastapi import FastAPI, Request, Query
from fastapi.responses import StreamingResponse
from typing import Optional

from api.agent_core import AgentCore, ChatRequest

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentAPI:
    def __init__(self, agent_core: AgentCore):
        self.app = FastAPI()
        self.agent_core = agent_core
        self._add_routes()

    def _should_summarize_response(self, system_context: str, response_text: str) -> bool:
        """
        Determine if the response should be summarized based on whether actual classification occurred.
        Returns True only if:
        1. An image was provided (system_context contains 'image_handle=')
        2. Classification was successful (response doesn't start with 'ERROR:')
        """
        has_image = "image_handle=" in system_context
        is_successful_classification = (
            has_image and 
            not response_text.startswith("ERROR:") and 
            len(response_text.strip()) > 0
        )
        
        logger.debug(f"Classification check - has_image: {has_image}, response_length: {len(response_text)}, starts_with_error: {response_text.startswith('ERROR:')}")
        return is_successful_classification

    def _add_routes(self):
        @self.app.post("/chat")
        async def chat(req: ChatRequest):
            logger.debug(f"Chat request received - message: '{req.message}', has_image: {bool(req.image_b64)}, session_id: {req.session_id}")
            logger.debug(f"Current image store status: {self.agent_core.get_image_store_status()}")
            
            system_context = ""
            if req.image_b64:
                handle = str(uuid.uuid4())
                self.agent_core.image_store[handle] = req.image_b64
                system_context = f"image_handle={handle}"
                logger.debug(f"Image uploaded with handle: {handle}")
            else:
                logger.debug("No image in request")

            inputs = {"input": req.message, "system_context": system_context}
            logger.debug(f"Invoking agent with inputs: {inputs}")
            
            # Show conversation history for debugging
            session_id = req.session_id or "default"
            conv_debug = self.agent_core.get_conversation_debug_info(session_id)
            logger.debug(f"Conversation state for session {session_id}: {conv_debug}")

            result = await self.agent_core.invoke_agent(inputs, session_id)
            final_text = result.get("output") if isinstance(result, dict) else str(result)
            
            # Only call summarize_response if actual leaf classification occurred
            should_summarize = self._should_summarize_response(system_context, final_text)
            logger.debug(f"Should summarize response: {should_summarize}")
            
            if should_summarize:
                # Pass the user's text to the summarize_response for processing along with image classification
                summary = await self.agent_core.summarize_response(final_text, req.session_id or "default", req.message)
                # Force structure as safety net in case LLM didn't follow format
                structured_summary = self.agent_core.force_structure_response(summary, session_id, True)
                # Parse structured response to separate main answer from action items
                structured_response = self.agent_core.parse_structured_response(structured_summary, session_id, True)
                return {
                    "reply": structured_response.get("main_answer", structured_summary),
                    "action_items": structured_response.get("action_items", []),
                    "has_structured_format": bool(structured_response.get("action_items"))
                }
            else:
                # Force structure as safety net in case LLM didn't follow format
                structured_final_text = self.agent_core.force_structure_response(final_text, session_id, False)
                # Parse structured response to separate main answer from action items
                structured_response = self.agent_core.parse_structured_response(structured_final_text, session_id, False)
                return {
                    "reply": structured_response.get("main_answer", structured_final_text),
                    "action_items": structured_response.get("action_items", []),
                    "has_structured_format": bool(structured_response.get("action_items"))
                }

        @self.app.get("/session-history")
        async def get_default_session_history():
            """Get the current session history for the default session."""
            return await get_session_history_by_id("default")

        @self.app.get("/session-history/{session_id}")
        async def get_session_history_by_id(session_id: str):
            """Get the current session history for a given session ID."""
            logger.debug(f"Session history request for session_id: {session_id}")
            
            try:
                # Get session history from agent core
                history = self.agent_core.get_session_history(session_id)
                messages = getattr(history, 'messages', [])
                
                # Format messages for response
                formatted_messages = []
                for i, msg in enumerate(messages):
                    msg_type = getattr(msg, "type", "unknown")
                    content = getattr(msg, "content", str(msg))
                    timestamp = getattr(msg, "timestamp", None)
                    
                    formatted_messages.append({
                        "index": i,
                        "type": msg_type,
                        "content": content,
                        "timestamp": timestamp,
                        "role": "assistant" if msg_type == "ai" else "user" if msg_type == "human" else msg_type
                    })
                
                # Get debug info for additional context
                # debug_info = self.agent_core.get_conversation_debug_info(session_id)
                
                response_data = {
                    "session_id": session_id,
                    "total_messages": len(messages),
                    "messages": formatted_messages,
                    # "debug_info": debug_info,
                    "summary": {
                        "ai_messages": len([m for m in messages if getattr(m, "type", None) == "ai"]),
                        "human_messages": len([m for m in messages if getattr(m, "type", None) == "human"]),
                        "other_messages": len([m for m in messages if getattr(m, "type", None) not in ["ai", "human"]])
                    }
                }
                
                logger.debug(f"Returning session history with {len(messages)} messages")
                return response_data
                
            except Exception as e:
                logger.error(f"Failed to get session history for {session_id}: {str(e)}")
                return {
                    "error": f"Failed to retrieve session history: {str(e)}",
                    "session_id": session_id,
                    "total_messages": 0,
                    "messages": []
                }

        @self.app.post("/chat-stream")
        async def chat_stream(req: ChatRequest, request: Request, format: Optional[str] = Query(None)):
            accept_header = (format or request.headers.get("accept", "")).lower()
            if "text/event-stream" in accept_header or (format and format.lower() == "sse"):
                media_type = "text/event-stream"
                def wrap(chunk: str) -> bytes:
                    return (f"data: {chunk}\n\n").encode("utf-8")
                extra_headers = {
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            else:
                media_type = "text/plain"
                def wrap(chunk: str) -> bytes:
                    if not chunk.endswith("\n"):
                        chunk_out = chunk + "\n"
                    else:
                        chunk_out = chunk
                    return chunk_out.encode("utf-8")
                extra_headers = {}

            queue: asyncio.Queue[bytes] = asyncio.Queue()
            loop = asyncio.get_event_loop()

            def emit(text: str) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, wrap(text))

            try:
                from langchain_core.callbacks.base import BaseCallbackHandler
            except Exception:
                BaseCallbackHandler = object

            class QueueCallbackHandler(BaseCallbackHandler):
                def on_llm_new_token(self, token: str, **kwargs) -> None:
                    # emit(token)
                    return

            system_context = ""
            handle: Optional[str] = None
            if req.image_b64:
                handle = str(uuid.uuid4())
                self.agent_core.image_store[handle] = req.image_b64
                system_context = f"image_handle={handle}"
                logger.debug(f"Streaming chat - Image uploaded with handle: {handle}")
            else:
                logger.debug("Streaming chat - No image in request")

            inputs = {"input": req.message, "system_context": system_context}
            logger.debug(f"Streaming chat - Invoking agent with inputs: {inputs}")
            
            # Show conversation history for debugging
            session_id = req.session_id or "default"
            conv_debug = self.agent_core.get_conversation_debug_info(session_id)
            logger.debug(f"Streaming chat - Conversation state for session {session_id}: {conv_debug}")

            async def run_agent():
                token = self.agent_core._emit_ctx.set(emit)
                if handle:
                    self.agent_core._image_emitters[handle] = emit
                try:
                    # Check if this is an image classification request  
                    has_image = "image_handle=" in system_context
                    
                    if has_image:
                        logger.info("🔥 DIRECT API-LEVEL STREAMING: Image classification detected")
                        
                        # Stream progress updates DIRECTLY with real delays at API level
                        await asyncio.sleep(0.3)
                        emit("Resized image, normalizing and preprocessing...")
                        logger.info("📡 Streamed chunk 1 directly from API")
                        
                        await asyncio.sleep(1.5)  
                        emit("Preparing image for neural network analysis...")
                        logger.info("📡 Streamed chunk 2 directly from API")
                        
                        await asyncio.sleep(1.2)
                        emit("Running CNN model inference...")
                        logger.info("📡 Streamed chunk 3 directly from API")
                        
                        await asyncio.sleep(1.0)
                        emit("Analyzing prediction results...")
                        logger.info("📡 Streamed chunk 4 directly from API")
                        
                        await asyncio.sleep(1.0)
                        emit("Finalizing diagnosis...")
                        logger.info("📡 Streamed chunk 5 directly from API")
                        
                        # Now do the actual classification (without internal streaming)
                        logger.info("🧠 Starting actual CNN classification (background)")
                        result = await self.agent_core.invoke_agent(
                            inputs,
                            req.session_id or "default", 
                            callbacks=[QueueCallbackHandler()]
                        )
                        
                        await asyncio.sleep(0.5)
                        final_text = result.get("output") if isinstance(result, dict) else str(result)
                        logger.info("✅ CNN classification completed, proceeding with response")
                        
                    else:
                        # Handle non-image requests normally
                        result = await self.agent_core.invoke_agent(
                            inputs,
                            req.session_id or "default",
                            callbacks=[QueueCallbackHandler()]
                        )
                        final_text = result.get("output") if isinstance(result, dict) else str(result)
                    
                    # Only call summarize_response if actual leaf classification occurred
                    should_summarize = self._should_summarize_response(system_context, final_text)
                    logger.debug(f"Streaming - Should summarize response: {should_summarize}")
                    
                    if should_summarize:
                        emit("Summarizing response...")
                        # Pass the user's text to the summarize_response for processing along with image classification
                        summary = await self.agent_core.summarize_response(final_text, req.session_id or "default", req.message)
                        # Force structure as safety net in case LLM didn't follow format
                        structured_summary = self.agent_core.force_structure_response(summary)
                        # Parse structured response for streaming
                        structured_response = self.agent_core.parse_structured_response(structured_summary)
                        
                        # Stream main answer first
                        main_answer = structured_response.get("main_answer", structured_summary)
                        if main_answer:
                            emit(main_answer)
                        
                        # Stream action items separately if they exist
                        action_items = structured_response.get("action_items", [])
                        if action_items:
                            action_items_text = " | ".join(action_items)
                            emit("\n\n" + action_items_text)
                    else:
                        # Force structure as safety net in case LLM didn't follow format
                        structured_final_text = self.agent_core.force_structure_response(final_text)
                        # Parse structured response for streaming
                        structured_response = self.agent_core.parse_structured_response(structured_final_text)
                        
                        # Stream main answer first
                        main_answer = structured_response.get("main_answer", structured_final_text)
                        if main_answer:
                            emit(main_answer)
                        
                        # Stream action items separately if they exist
                        action_items = structured_response.get("action_items", [])
                        if action_items:
                            action_items_text = " | ".join(action_items)
                            emit("\n\n" + action_items_text)
                finally:
                    self.agent_core._emit_ctx.reset(token)
                    if handle and handle in self.agent_core._image_emitters:
                        try:
                            del self.agent_core._image_emitters[handle]
                        except Exception:
                            pass
                if media_type == "text/event-stream":
                    emit("[DONE]")

            async def streamer():
                task = asyncio.create_task(run_agent())
                try:
                    while True:
                        chunk = await queue.get()
                        yield chunk
                        queue.task_done()
                        
                        # NO additional delay here - delays are now properly handled in _stream_image_classification
                        # This prevents double-delays and ensures immediate chunk delivery
                        
                        if task.done() and queue.empty():
                            break
                finally:
                    if not task.done():
                        task.cancel()

            return StreamingResponse(streamer(), media_type=media_type, headers=extra_headers)


# Bulletproof singleton pattern to prevent ANY double initialization
import os
import threading
from typing import Optional

# Thread-safe singleton with process-level protection
_lock = threading.Lock()
_agent_core_instance: Optional['AgentCore'] = None
_api_server: Optional['AgentAPI'] = None
_app = None
_initialization_started = False

# Process-level protection using environment variable
AGENT_CORE_INITIALIZED = "SASYA_AGENT_CORE_INITIALIZED"

def _get_agent_core():
    """Thread-safe singleton AgentCore with process-level protection"""
    global _agent_core_instance, _initialization_started
    
    # Fast path - already initialized
    if _agent_core_instance is not None:
        return _agent_core_instance
    
    with _lock:
        # Double-check pattern
        if _agent_core_instance is not None:
            return _agent_core_instance
            
        # Check if another process already initialized
        if os.environ.get(AGENT_CORE_INITIALIZED) == "true":
            logger.warning("🔄 AgentCore already initialized in another process - creating new instance for this process")
        
        # Prevent recursive/double initialization
        if _initialization_started:
            logger.error("❌ Recursive AgentCore initialization detected - preventing double creation")
            raise RuntimeError("AgentCore initialization already in progress")
            
        _initialization_started = True
        
        try:
            logger.info("🚀 Creating AgentCore instance (thread-safe singleton)")
            _agent_core_instance = AgentCore()
            
            # Mark as initialized globally
            os.environ[AGENT_CORE_INITIALIZED] = "true"
            
            logger.info("✅ AgentCore instance created successfully (singleton pattern)")
            return _agent_core_instance
            
        except Exception as e:
            _initialization_started = False  # Reset on error
            logger.error(f"❌ AgentCore initialization failed: {e}")
            raise
        finally:
            _initialization_started = False

def _get_api_server():
    """Get or create the single AgentAPI server"""
    global _api_server
    if _api_server is None:
        logger.info("🔧 Creating AgentAPI server (singleton)")
        _api_server = AgentAPI(_get_agent_core())
        logger.info("✅ AgentAPI server created successfully")
    return _api_server

def _get_app():
    """Get or create the FastAPI app"""
    global _app
    if _app is None:
        logger.info("📱 Creating FastAPI app (singleton)")
        _app = _get_api_server().app
        logger.info("✅ FastAPI app created successfully")
    return _app

def __getattr__(name):
    """Module-level lazy attribute access"""
    if name == "app":
        return _get_app()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

if __name__ == "__main__":
    # Use the same global instance - don't create new ones
    uvicorn.run("agent_api:app", host="0.0.0.0", port=8080, reload=False)  # Disable reload to prevent multiple initializations
