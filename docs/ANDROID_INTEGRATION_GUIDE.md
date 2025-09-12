# Android App Integration with Planning Agent

## ✅ Integration Complete!

The Android app has been successfully updated to work with the new Planning Agent streaming server.

## 🔧 Changes Made

### 1. **Updated API Endpoint**
**File:** `app/src/main/java/com/example/sasya_chikitsa/network/ApiService.kt`
```kotlin
// BEFORE
@POST("chat-stream")

// AFTER  
@POST("planning/chat-stream")
```

### 2. **Updated Server Configuration**
**File:** `app/src/main/java/com/example/sasya_chikitsa/config/ServerConfig.kt`
```kotlin
// BEFORE
const val DEFAULT_EMULATOR_URL = "http://10.0.2.2:8080/"
const val DEFAULT_LOCALHOST_URL = "http://localhost:8080/"

// AFTER
const val DEFAULT_EMULATOR_URL = "http://10.0.2.2:8001/"
const val DEFAULT_LOCALHOST_URL = "http://localhost:8001/"
```

### 3. **Enhanced Request Format**
**File:** `app/src/main/java/com/example/sasya_chikitsa/network/request/ChatRequestData.kt`
```kotlin
// BEFORE
data class ChatRequestData(
    val message: String,
    val image_b64: String? = null,
    val session_id: String? = null
)

// AFTER
data class ChatRequestData(
    val message: String,
    val image_b64: String? = null,
    val session_id: String? = null,
    val context: Map<String, Any>? = null // NEW: Context for planning agent
)
```

### 4. **Added Context Data**
**File:** `app/src/main/java/com/example/sasya_chikitsa/MainActivity.kt`
```kotlin
// BEFORE
val requestData = ChatRequestData(
    message = message,
    image_b64 = imageBase64,
    session_id = sessionId
)

// AFTER
val requestData = ChatRequestData(
    message = message,
    image_b64 = imageBase64,
    session_id = sessionId,
    context = mapOf(
        "platform" to "android",
        "app_version" to "1.0.0", 
        "timestamp" to System.currentTimeMillis()
    )
)
```

## 🌐 Server Setup

### **Planning Agent Server**
- **Port:** 8001 (changed from 8080)
- **Endpoint:** `/planning/chat-stream`
- **Protocol:** Server-Sent Events (SSE)

### **Start the Server**
```bash
cd engine/agents
./run_planning_server.sh --port 8001
```

## 📱 Android Configuration

### **Emulator Setup**
- **URL:** `http://10.0.2.2:8001/`
- **Reason:** Android emulator maps `10.0.2.2` to host `localhost`

### **Physical Device Setup**  
- **URL:** `http://192.168.1.100:8001/` (replace with your computer's IP)
- **Requirement:** Device and computer on same WiFi network

### **Update Server URL in App**
1. Open the Android app
2. Go to Settings → Server Configuration  
3. Select "Android Emulator" or enter custom URL
4. Test connection

## 🔄 Request/Response Format

### **Android Request Format**
```json
{
  "message": "analyze this tomato plant disease",
  "image_b64": "base64_encoded_image_data",
  "session_id": "android_session_123",
  "context": {
    "platform": "android",
    "app_version": "1.0.0",
    "timestamp": 1757520447982
  }
}
```

### **Streaming Response Format**
```
data: Starting analysis...

data: 🧠 I can see you've uploaded an image. Let me analyze this plant for any disease signs...

data: 🔄 **CLASSIFICATION STEP COMPLETED**

data: 💊 **Treatment Prescription for Early Blight**
**Chemical:** Copper sulfate spray (2g/L), weekly application
**Organic:** Neem oil spray + proper plant spacing

data: 🔄 **PRESCRIPTION STEP COMPLETED**

data: [DONE]
```

## 🧪 Testing the Integration

### **Test Script**
Run the integration test:
```bash
cd tests
./android_planning_integration_test.sh
```

### **Manual Testing**
1. **Start Planning Server:**
   ```bash
   cd engine/agents
   ./run_planning_server.sh --port 8001
   ```

2. **Build & Run Android App:**
   - Open project in Android Studio
   - Select emulator or connected device
   - Run the app

3. **Test Scenarios:**
   - Send text message: "What's wrong with my plant?"
   - Send image with text: Upload plant image + "Diagnose this"
   - Verify streaming responses appear in chat

## 🎯 Benefits of Planning Agent Integration

### **Multi-Step Intelligent Workflow**
- **Intent Capture** → **Classification** → **Prescription** → **Vendor Recommendations**
- **Automatic state transitions** based on user input and image data
- **Continuous streaming** of intermediate results

### **Enhanced Features**
- ✅ **Real-time progress updates** during analysis
- ✅ **Context-aware responses** based on user profile
- ✅ **Multi-step conversation flow** with memory
- ✅ **Intelligent workflow routing** (image → classification, text → clarification)
- ✅ **Attention overlay visualization** for disease detection

### **Improved User Experience**
- **Faster feedback:** See analysis progress in real-time
- **Better accuracy:** Multi-step validation and clarification
- **Personalized recommendations:** Based on location, season, crop type
- **Seamless flow:** Automatic progression through diagnosis steps

## 🔍 Troubleshooting

### **Common Issues**

**1. Connection Failed**
```
❌ Server not responding at 10.0.2.2:8001
```
**Solution:** Ensure planning agent server is running on port 8001

**2. Streaming Not Working**  
```
❌ No streaming data received
```
**Solution:** Verify `Accept: text/event-stream` header is set

**3. Request Format Error**
```
❌ Invalid request format
```
**Solution:** Check that context field is properly formatted as Map<String, Any>

### **Debug Steps**
1. **Check server logs** for request processing errors
2. **Verify network connectivity** from Android to server
3. **Test with curl** to isolate Android vs server issues
4. **Check Retrofit logs** for detailed HTTP communication

## ✅ Integration Status: COMPLETE

The Android app is now fully integrated with the Planning Agent system and ready for testing with the multi-step plant disease diagnosis workflow!
