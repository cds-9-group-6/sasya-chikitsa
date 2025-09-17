# Dynamic Planning Agent (FSM) 🌱

A LangGraph-based finite state machine agent for plant disease diagnosis and prescription. This agent provides a conversational interface that dynamically transitions between states based on user input and LLM reasoning.

## Architecture

The agent uses **LangGraph StateGraph** for orchestrating a dynamic workflow with the following states:

- **INITIAL** - Entry point, context extraction
- **CLASSIFYING** - CNN-based disease classification 
- **PRESCRIBING** - RAG-based treatment recommendations
- **VENDOR_QUERY** - Ask user about vendor preferences
- **SHOW_VENDORS** - Display vendor options and pricing
- **ORDER_BOOKING** - Process orders with selected vendors
- **FOLLOWUP** - Handle additional questions and navigation
- **COMPLETED** - Terminal success state with contextual follow-up suggestions
- **ERROR** - Terminal error state

## Key Features

### 🧠 **LLM-Driven State Transitions**
- Dynamic routing based on user input interpretation
- Flexible conversation flow with branching and looping
- Context-aware decision making

### 🔧 **Modular Tool System**
- **ClassificationTool** - CNN with attention mechanism
- **PrescriptionTool** - RAG-based recommendations  
- **VendorTool** - Local vendor search and pricing
- **ContextExtractorTool** - NLP-based context extraction
- **AttentionOverlayTool** - Retrieve and display stored attention visualizations

### 🔄 **Streaming Support**
- Real-time response streaming
- State update notifications
- Progress indicators during long operations

### 📊 **Session Management**
- Persistent conversation history
- State tracking across interactions
- Session cleanup and monitoring

### 🎯 **Intelligent Follow-Up System**
- Context-aware follow-up questions in completed state
- Smart deduplication to avoid repeating discussed topics
- Up to 3 relevant suggestions based on workflow path
- Personalized recommendations based on user context

## Installation

1. **Install Dependencies**
   ```bash
   cd engine/fsm_agent
   pip install -r requirements.txt
   ```

2. **Setup Ollama** (if not already running)
   ```bash
   ollama serve
   ollama pull llama3.1:8b
   ```

3. **Environment Configuration**
   ```bash
   # Create .env file
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=llama3.1:8b
   ```

## Usage

### 1. **Start the Server**

```bash
# Basic startup
python run_fsm_server.py

# Custom configuration
python run_fsm_server.py --host 0.0.0.0 --port 8002 --log-level debug

# Development mode with auto-reload
python run_fsm_server.py --reload
```

### 2. **Test the Agent**

```bash
# Run comprehensive tests
python test_fsm_agent.py

# Check environment only
python run_fsm_server.py --check-env
```

### 3. **API Usage**

**Start a conversation:**
```bash
curl -X POST "http://localhost:8002/sasya-chikitsa/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need help with my tomato plant showing yellow spots",
    "context": {
      "location": "Tamil Nadu",
      "season": "summer"
    }
  }'
```

**Continue conversation:**
```bash
curl -X POST "http://localhost:8002/sasya-chikitsa/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_abc123",
    "message": "Yes, I would like to see vendor options"
  }'
```

**Stream responses:**
```bash
curl -X POST "http://localhost:8002/sasya-chikitsa/chat-stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this plant image for diseases",
    "image_b64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA..."
  }'
```

## API Endpoints

### Core Endpoints
- `POST /sasya-chikitsa/chat` - Process messages (non-streaming)
- `POST /sasya-chikitsa/chat-stream` - Process messages with streaming
- `GET /health` - Health check
- `GET /sasya-chikitsa/stats` - Agent statistics

### Session Management
- `GET /sasya-chikitsa/session/{session_id}` - Get session info
- `GET /sasya-chikitsa/session/{session_id}/history` - Get conversation history
- `GET /sasya-chikitsa/session/{session_id}/classification` - Get classification results
- `GET /sasya-chikitsa/session/{session_id}/prescription` - Get prescription data
- `DELETE /sasya-chikitsa/session/{session_id}` - End session

### Utilities
- `POST /sasya-chikitsa/cleanup` - Clean up inactive sessions

## Configuration

### LLM Configuration
```python
llm_config = {
   "model": "llama3.1:8b",        # Ollama model name
   "base_url": "http://localhost:11434",  # Ollama server URL
   "temperature": 0.1,            # Lower for more deterministic responses
}
```

### Tool Configuration
Each tool can be configured independently:

```python
# Classification Tool
classification_tool = ClassificationTool()

# Prescription Tool with custom RAG
prescription_tool = PrescriptionTool()

# Vendor Tool with custom database
vendor_tool = VendorTool()
```

## Workflow Example

```
User: "My tomato plants have yellow spots"
  ↓
[INITIAL] → Extract context (location: Tamil Nadu, plant: tomato)
  ↓
[CLASSIFYING] → "Please upload an image for analysis"
  ↓
User: [uploads image]
  ↓
[CLASSIFYING] → CNN analysis → "Early Blight detected (85% confidence)"
  ↓
[PRESCRIBING] → RAG query → Treatment recommendations
  ↓
[VENDOR_QUERY] → "Would you like vendor options?"
  ↓
User: "Yes, show me organic options"
  ↓
[SHOW_VENDORS] → Local organic suppliers with pricing
  ↓
[ORDER_BOOKING] → Process order with selected vendor
  ↓
[COMPLETED] → "🌱 Workflow completed successfully!

📝 Here are some additional things that might interest you:
1. Would you like to know about vendors or suppliers who can provide these treatments?
2. Do you need detailed application instructions or dosage information?  
3. Would you like information about crop insurance options to protect your investment?"
```

## Intelligent Follow-Up System 🎯

The FSM agent features an advanced follow-up system that provides contextual suggestions when workflows complete, helping farmers discover additional relevant services and information.

### How It Works

1. **Context Analysis**: When a workflow reaches the completed state, the system analyzes:
   - Previous workflow state (classification, prescription, vendor query)
   - User context (location, plant type, season, growth stage)
   - Conversation history to avoid repetition
   - User intent indicators from previous interactions

2. **Smart Suggestions**: Generates up to 3 relevant follow-up questions based on:
   - **After Classification**: Treatment options, prevention tips, general plant care
   - **After Prescription**: Vendor information, application instructions, dosage details
   - **After Vendor Query**: Application timing, progress monitoring, follow-up care

3. **Deduplication**: Automatically filters out topics already discussed by analyzing conversation history for relevant keywords

### Follow-Up Examples by State

#### After Classification
```
🌱 Workflow completed successfully!

📝 Here are some additional things that might interest you:
1. Would you like specific treatment recommendations for this disease?
2. Would you like to know how to prevent this disease in the future?
3. Are you interested in seasonal care tips for summer?
```

#### After Prescription  
```
🌱 Workflow completed successfully!

📝 Here are some additional things that might interest you:
1. Would you like to know about vendors or suppliers who can provide these treatments?
2. Do you need detailed application instructions or dosage information?
3. Would you like information about crop insurance options to protect your investment?
```

#### After Vendor Search
```
🌱 Workflow completed successfully!

📝 Here are some additional things that might interest you:
1. Would you like guidance on the best timing and method for applying treatments?
2. Would you like to know how to monitor treatment progress and follow-up care?
3. Are you interested in soil health assessment or nutrient management tips?
```

### Context-Aware Suggestions

The system also provides personalized suggestions based on user context:

- **Location-based**: Weather recommendations for specific regions
- **Plant-specific**: Care tips tailored to the identified plant type
- **Season-aware**: Seasonal advice and timing recommendations
- **Technical interests**: Detailed analysis options for users wanting deeper insights
- **Commercial interests**: Market insights, insurance options, and business aspects

### API Integration

Follow-up suggestions are automatically included in completion responses:

**Streaming Response:**
```
event: state_update
data: {
  "current_node": "completed",
  "assistant_response": "🌱 Workflow completed successfully!\n\n📝 Here are some additional things that might interest you:\n1. Would you like to know about vendors...",
  "is_complete": true
}
```

**JSON Response:**
```json
{
  "response": "🌱 Workflow completed successfully!\n\n📝 Here are some additional things that might interest you:\n1. Would you like to know about vendors who can provide these treatments?\n2. Do you need detailed application instructions?\n3. Would you like crop insurance information?",
  "session_id": "session_123",
  "current_state": "completed"
}
```

### Benefits

- **Enhanced User Experience**: Proactively suggests relevant next steps
- **Increased Engagement**: Helps users discover additional valuable services
- **Contextual Relevance**: Suggestions tailored to specific user journey and needs
- **Conversation Continuity**: Seamless transition from completion to new topics
- **Smart Filtering**: Avoids repetition and information overload

## Attention Overlay Functionality 🎯

The FSM agent includes a dedicated **AttentionOverlayTool** that allows users to retrieve and view attention visualizations from previous classifications without needing to re-run the analysis.

### How It Works

1. **During Classification**: When the CNN classifies a plant disease, it generates an attention overlay showing which parts of the image were most important for the diagnosis
2. **Stored in Session**: The base64-encoded attention overlay is automatically stored in the session state
3. **On-Demand Retrieval**: Users can request to view the overlay at any time during the conversation

### Usage Examples

Users can request attention overlays using natural language:

```
User: "show me the attention overlay"
User: "can I see the attention map?"
User: "display the heatmap" 
User: "show me where the AI was looking"
User: "what parts of the image were important?"
User: "attention overlay info"
User: "explain the attention overlay"
```

### API Integration

**Request Format:**
```json
{
  "message": "show attention overlay",
  "session_id": "existing-session-with-classification"
}
```

**Response Format:**
```json
{
  "response": "🎯 **Attention Overlay for Tomato Late Blight**\n\n**Confidence:** 92.50%\n**Overlay Format:** Base64 encoded image\n\n**Attention Overlay Data:**\niVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAY...\n\n💡 **Usage:** Display this as an overlay on your original image to see where the AI focused its attention.",
  "session_id": "session-123",
  "current_state": "followup"
}
```

### Implementation Details

The attention overlay functionality is handled by the **FOLLOWUP** state, which detects overlay-related keywords and:

1. ✅ **Retrieves** the stored attention data from session state
2. 🔍 **Validates** that classification results exist
3. 📤 **Returns** the base64-encoded overlay image
4. ❌ **Handles errors** gracefully when no overlay is available

### Error Handling

- **No Classification**: Prompts user to perform classification first
- **No Overlay**: Explains that overlay generation may have failed
- **Session Issues**: Suggests starting a new classification session

### Testing

Run the attention overlay test suite:
```bash
cd engine/fsm_agent/tests
./test_attention_overlay.sh
```

This test verifies:
- ✅ Overlay retrieval after successful classification
- ❌ Error handling for no-classification scenarios  
- 📡 Streaming overlay responses
- 🔍 Base64 data format validation

### Streaming Test with Real Images

Run the comprehensive streaming test with real plant disease images:
```bash
cd engine/fsm_agent/tests
./test_fsm_streaming_with_image.sh
```

This test validates:
- 🌊 **Real-time streaming responses** with actual plant disease images
- 🔄 **LangGraph state transitions** through the complete workflow
- 🔬 **CNN classification** with status message parsing
- 💊 **RAG-based prescriptions** with plant-specific recommendations
- 🎯 **Attention overlay requests** from stored session data
- 🏪 **Vendor recommendations** and interaction flow
- 💬 **Followup conversations** with contextual responses
- 🗄️ **Session persistence** and state management

## Extending the Agent

### Adding New States

1. **Create State Node Function**
   ```python
   async def _my_new_state_node(self, state: WorkflowState) -> WorkflowState:
       # State logic here
       return state
   ```

2. **Add to Workflow**
   ```python
   workflow.add_node("my_new_state", self._my_new_state_node)
   ```

3. **Add Routing**
   ```python
   workflow.add_conditional_edges(
       "previous_state",
       self._route_to_new_state,
       {"my_new_state": "my_new_state"}
   )
   ```

### Adding New Tools

1. **Create Tool Class**
   ```python
   class MyCustomTool(BaseTool):
       name = "my_custom_tool"
       description = "My custom tool description"
       
       def _run(self, **kwargs):
           # Tool logic here
           return result
   ```

2. **Register Tool**
   ```python
   self.tools["my_custom_tool"] = MyCustomTool()
   ```

3. **Use in State**
   ```python
   tool_result = await self.tools["my_custom_tool"].run(input_data)
   ```

## Monitoring and Debugging

### Logs
- All state transitions are logged
- Tool execution is tracked
- Error conditions are captured

### Session Information
```bash
curl "http://localhost:8002/sasya-chikitsa/session/session_123"
```

### Agent Statistics  
```bash
curl "http://localhost:8002/sasya-chikitsa/stats"
```

## Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama if needed
   ollama serve
   ```

2. **Model Not Found**
   ```bash
   # Pull required model
   ollama pull llama3.1:8b
   ```

3. **Classification Tool Fails**
   - Ensure CNN model files are in `../models/`
   - Check model path in configuration

4. **RAG System Issues**
   - Verify ChromaDB data in `../rag/data/`
   - Check HuggingFace embeddings model

5. **Memory Issues**
   - Reduce batch size in CNN classifier
   - Use smaller LLM model
   - Enable session cleanup

### Debug Mode
```bash
python run_fsm_server.py --log-level debug
```

## Performance

### Optimization Tips
- Use streaming for better UX
- Enable session cleanup for memory management
- Cache frequently used data
- Use appropriate LLM temperature settings

### Scaling
- Run multiple worker processes
- Use load balancer for multiple instances
- Implement session persistence with external storage
- Consider async database operations

## Contributing

1. **Add Tests**
   - Test new states in `test_fsm_agent.py`
   - Add tool tests for new functionality

2. **Documentation**
   - Update this README for new features
   - Add docstrings to new functions

3. **Code Quality**
   - Follow existing patterns
   - Use type hints
   - Add proper error handling

## License

This project is part of the Sasya Chikitsa plant disease diagnosis system.
