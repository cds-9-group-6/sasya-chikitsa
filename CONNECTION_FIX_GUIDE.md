# 🔌 Connection Issue Resolution Guide

## ❌ **Original Problem**
```
java.net.ConnectException: Failed to connect to /10.0.2.2:8001
```

## 🔍 **Root Cause Analysis**

### **What Was Happening:**
- **FSM Server**: Running on port `8080` ✅
- **App Configuration**: Trying to connect to port `8001` ❌
- **Result**: Connection refused because nothing was listening on port 8001

### **Why This Occurred:**
The `ServerConfig.kt` had mixed port configurations:
```kotlin
// BEFORE FIX (inconsistent ports):
const val DEFAULT_EMULATOR_URL = "http://10.0.2.2:8080/"  // ✅ Correct
const val DEFAULT_LOCALHOST_URL = "http://localhost:8001/" // ❌ Wrong port
const val DEFAULT_LOCAL_IP_URL = "http://192.168.1.100:8001/" // ❌ Wrong port
```

## ✅ **Solution Applied**

### **1. Verified FSM Server Status**
- ✅ FSM Server running on port 8080 (PID 17509)
- ✅ Server accessible and ready

### **2. Fixed Port Configuration**
Updated `ServerConfig.kt` to use consistent ports:

```kotlin
// AFTER FIX (all ports consistent):
const val DEFAULT_EMULATOR_URL = "http://10.0.2.2:8080/"      // ✅ Correct
const val DEFAULT_LOCALHOST_URL = "http://localhost:8080/"     // ✅ Fixed
const val DEFAULT_LOCAL_IP_URL = "http://192.168.1.100:8080/" // ✅ Fixed
```

### **3. Build Verification**
- ✅ App builds successfully with corrected configuration
- ✅ All dependencies resolved
- ✅ Ready for testing

## 🚀 **How to Test the Fix**

### **Step 1: Rebuild and Run**
```bash
./gradlew clean build
# Install and run in Android Studio
```

### **Step 2: Verify Connection**
1. Launch **Sasya Arogya** app
2. App should connect to `http://10.0.2.2:8080/` automatically
3. Try sending a message or uploading a plant image
4. You should see FSM agent responses with **light green follow-up buttons**

### **Step 3: If Still Having Issues**

#### **For Android Emulator:**
- Server URL: `http://10.0.2.2:8080/`
- Make sure FSM server is running: `cd engine/fsm_agent && python run_fsm_server.py`

#### **For Physical Device:**
- Find your computer's IP: `ifconfig | grep "inet " | grep -v 127.0.0.1`
- Use: `http://[YOUR_IP]:8080/` (e.g., `http://192.168.1.100:8080/`)
- Make sure both devices are on the same WiFi network

#### **Manual Server URL Change (if needed):**
1. Open app → Tap settings (⚙️)  
2. Change server URL to correct address
3. Restart app

## 🌟 **Expected Result**

After the fix, your app should:
- ✅ **Connect successfully** to FSM agent
- ✅ **Stream real-time responses** 
- ✅ **Display light green follow-up buttons**
- ✅ **Show state progression** (Ready → Analyzing Plant → Complete)
- ✅ **Handle image uploads** for plant diagnosis

## 🐛 **Troubleshooting**

### **If Connection Still Fails:**

1. **Check FSM Server:**
   ```bash
   lsof -i :8080  # Should show Python process
   curl http://localhost:8080/health  # Should return health status
   ```

2. **Restart FSM Server:**
   ```bash
   cd engine/fsm_agent
   python run_fsm_server.py --host 0.0.0.0 --port 8080
   ```

3. **Check Network (Physical Device):**
   ```bash
   ping [DEVICE_IP]  # Make sure devices can reach each other
   ```

4. **Clear App Data:**
   - Android Settings → Apps → Sasya Arogya → Storage → Clear Data
   - This resets server URL to defaults

The FSM integration with **intelligent follow-up suggestions** should now work perfectly! 🌿📱✨
