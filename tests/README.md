# FSM Agent Chat Stream Testing Suite

This directory contains comprehensive test scripts for the FSM Agent chat streaming endpoint, including image classification and agricultural context testing.

## 🚀 Quick Start

### Prerequisites

1. **Start FSM Server**:
   ```bash
   cd engine/fsm_agent
   python3 run_fsm_server.py
   ```

2. **Install Dependencies**:
   ```bash
   # Required for test scripts
   brew install curl jq  # macOS
   # or
   sudo apt-get install curl jq  # Ubuntu/Debian
   ```

### Run Tests

```bash
# Quick basic test
./tests/quick_chat_test.sh

# Comprehensive test suite
./tests/test_fsm_chat_stream.sh

# Image classification test
./tests/image_test.sh [optional_image_path]
```

## 📋 Test Scripts Overview

### 1. `quick_chat_test.sh` - Basic Functionality Test

**Purpose**: Quick verification that the FSM agent is responding to basic chat queries.

**Features**:
- Server health check
- Simple text-based agricultural query
- Basic SSE streaming verification

**Usage**:
```bash
./tests/quick_chat_test.sh
```

**Expected Output**:
- Server health verification
- Streaming chat response about tomato plant issues
- Success confirmation

---

### 2. `test_fsm_chat_stream.sh` - Comprehensive Test Suite

**Purpose**: Full-featured testing of all FSM agent capabilities.

**Features**:
- 📝 Text-only agricultural queries
- 🖼️ Image classification with multiple plant types
- 🌱 Various agricultural contexts (different plants, seasons, locations)
- 🔄 Follow-up conversation testing
- ⚡ Performance timing measurements
- 🎯 Attention overlay detection
- 📊 Response analysis and error detection

**Test Scenarios**:
1. **Simple Text Query**: Tomato yellowing leaves diagnosis
2. **Tomato Disease Classification**: Image analysis with `tomato_mosaic_virus.png`
3. **Apple Disease Diagnosis**: Early blight detection in apple leaves
4. **Potato Health Assessment**: Healthy plant verification
5. **Agricultural Advisory**: Comprehensive farming advice
6. **Follow-up Query**: Context-aware conversation continuation
7. **Performance Test**: Response time measurement

**Usage**:
```bash
./tests/test_fsm_chat_stream.sh

# With custom server URL
FSM_SERVER_URL=http://192.168.1.100:8080 ./tests/test_fsm_chat_stream.sh

# With custom images directory
IMAGES_DIR=/path/to/images ./tests/test_fsm_chat_stream.sh
```

**Output**: 
- Detailed test results with color-coded status
- Response time measurements  
- Debug files in `/tmp/fsm_test_*` directory

---

### 3. `image_test.sh` - Focused Image Classification Test

**Purpose**: Dedicated testing of image upload and AI classification capabilities.

**Features**:
- 📸 Base64 image encoding and upload
- 🔬 Plant disease classification
- 🎯 Attention overlay generation detection
- 🌿 Auto-detection of plant type from filename
- 📋 Detailed diagnosis and treatment recommendations

**Usage**:
```bash
# Default test image
./tests/image_test.sh

# Custom image
./tests/image_test.sh engine/resources/images_for_test/apple_healthy_multi_leaves_1.jpeg

# Test different plant diseases
./tests/image_test.sh engine/resources/images_for_test/Tomato_Target_Spot_multiple_leaves.jpg
```

**Supported Image Types**:
- `.jpg`, `.jpeg`, `.png`
- Automatic MIME type detection
- Base64 encoding with data URL format

---

## 🖼️ Available Test Images

The test scripts use images from `engine/resources/images_for_test/`:

### Tomato Diseases:
- `tomato_mosaic_virus.png` - Tomato Mosaic Virus
- `Tomato_Target_Spot_multiple_leaves.jpg` - Target Spot Disease
- `Tomato_Spider_Mites_multiple_leaves.jpg` - Spider Mites Infestation
- `Tomato_Yellow_Leaf_Curl_Virus.jpg` - Yellow Leaf Curl Virus
- `Tomato-Fruit-borer.png` - Fruit Borer Damage

### Apple Diseases:
- `apple_alternaria_Early_blight_multi_leaves_1.jpeg` - Early Blight
- `apple_alternaria_Early_blight_multi_leaves_2.jpeg` - Early Blight (variant)
- `Apple-Leaf-Root-Rot.png` - Root Rot symptoms
- `apple_tomato_mosaic_virus_multi_leaves.jpeg` - Mosaic Virus

### Potato Conditions:
- `potato_healthy_multi_leaves_1.JPG` - Healthy potato plants
- `potato_healthy_multi_1.JPG` - Healthy potato (variant 1)  
- `potato_healthy_multi_2.JPG` - Healthy potato (variant 2)
- `Potato_fungi_2_leaves.jpg` - Fungal infection

### Healthy Samples:
- `apple_healthy_multi_leaves_1.jpeg` - Healthy apple leaves
- `Apple_Healthy.jpeg` - Healthy apple plant

## 🔧 Configuration Options

### Environment Variables:

```bash
# Server URL (default: http://localhost:8080)
export FSM_SERVER_URL=http://your-server:8080

# Images directory (default: engine/resources/images_for_test)
export IMAGES_DIR=/path/to/your/images

# Test timeout in seconds (default: 60)
export TEST_TIMEOUT=120
```

### Agricultural Context Parameters:

The tests use realistic agricultural contexts:

```json
{
    "plant_type": "Tomato|Apple|Potato",
    "location": "Maharashtra, India|Karnataka, India|Punjab, India",
    "season": "Kharif|Rabi|Summer|Winter|Monsoon", 
    "growth_stage": "Seedling|Vegetative|Flowering|Fruiting|Maturation",
    "farm_size": "1-50 acres",
    "farming_experience": "1-10+ years",
    "farming_type": "Organic|Sustainable|Traditional",
    "irrigation_method": "Drip|Sprinkler|Flood",
    "soil_type": "Loamy|Sandy|Clay"
}
```

## 📊 Response Analysis

### Event Types:
- `thinking` - AI is processing the request
- `classifying` - Image classification in progress
- `attention_overlay` - Attention heatmap generated
- `complete` - Processing finished

### Response Content:
- **Text Responses**: Agricultural advice, disease information
- **Classification Results**: Disease name, confidence score
- **Treatment Recommendations**: Organic/chemical treatment options
- **Attention Overlays**: Base64-encoded heatmap images

## 🐛 Debugging

### Debug Files Location:
```
/tmp/fsm_test_<pid>/
├── request_Simple_Text_Query.json
├── response_Simple_Text_Query.txt
├── request_Tomato_Disease_Classification.json
└── response_Tomato_Disease_Classification.txt
```

### Common Issues:

1. **Server Not Responding**:
   ```bash
   # Check if FSM server is running
   curl -s http://localhost:8080/health
   
   # Start server if not running
   cd engine/fsm_agent && python3 run_fsm_server.py
   ```

2. **Image Not Found**:
   ```bash
   # List available test images
   ls engine/resources/images_for_test/
   
   # Use absolute path
   ./tests/image_test.sh /full/path/to/image.jpg
   ```

3. **Dependencies Missing**:
   ```bash
   # macOS
   brew install curl jq
   
   # Ubuntu/Debian
   sudo apt-get install curl jq base64
   ```

4. **Timeout Issues**:
   ```bash
   # Increase timeout for slow responses
   TEST_TIMEOUT=120 ./tests/test_fsm_chat_stream.sh
   ```

## 🚀 Advanced Usage

### Custom Test Scenarios:

Create your own test by modifying the request payload:

```bash
# Custom agricultural context
cat > custom_test.json <<EOF
{
    "message": "My crops are showing unusual symptoms",
    "session_id": "custom-$(date +%s)",
    "context": {
        "plant_type": "Rice",
        "location": "West Bengal, India", 
        "season": "Monsoon",
        "growth_stage": "Tillering",
        "farm_size": "15 acres"
    }
}
EOF

# Send request
curl -X POST http://localhost:8080/sasya-chikitsa/chat-stream \
    -H "Content-Type: application/json" \
    -H "Accept: text/event-stream" \
    -d @custom_test.json --no-buffer
```

### Batch Testing:

```bash
# Test multiple images
for img in engine/resources/images_for_test/*.jpg; do
    echo "Testing: $img"
    ./tests/image_test.sh "$img"
    sleep 5
done
```

## 📈 Performance Benchmarking

The comprehensive test suite includes performance measurements:

- **Response Time**: Time from request to first response
- **Streaming Latency**: Time between streaming events
- **Image Processing Time**: Classification and attention overlay generation
- **Memory Usage**: Monitor server resource consumption

## ✅ Expected Results

### Successful Test Indicators:
- ✅ Server health check passes
- 📡 SSE streaming events received
- 🤖 AI responses contain agricultural advice
- 🎯 Image classification returns disease names
- 🔍 Attention overlays generated for disease images
- ⏱️ Response times under 30 seconds

### Sample Success Output:
```
🚀 FSM Agent Chat Stream Test Suite
=====================================
✅ Server is healthy
📤 Test: Simple Text Query
📡 Streaming response:
🤖 Based on your description of yellowing leaves in tomato plants...
🎯 Disease Detected: Early Blight (Confidence: 87%)
✅ Response received successfully
⏱️ Response time: 12.34s
🎉 All tests completed!
```

This comprehensive testing suite ensures your FSM Agent is working correctly with both text and image inputs, providing reliable agricultural AI assistance.
