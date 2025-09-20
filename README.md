# Sasya Chikitsa (Sasya Arogya)
An AI-driven application to help farmers and plant enthusiasts identify plant diseases and get useful recommendations with intelligent multi-session conversation management.

## 🌟 Key Features

### 🤖 **Intelligent Plant Health Assistant**
- **AI-Powered Disease Detection**: Advanced machine learning models for accurate plant disease identification
- **Real-time Analysis**: Instant plant health assessment from uploaded images
- **Treatment Recommendations**: Comprehensive care advice and prescription suggestions
- **Multi-language Support**: Farmer-friendly explanations in local languages

### 💬 **Advanced Session Management**
- **Multi-Session Conversations**: Analyze multiple plants in separate conversation sessions
- **Auto-Session Creation**: Automatically creates new sessions when analyzing different plants
- **Session History**: Complete conversation history preservation across sessions
- **Visual Indicators**: 📷 for sessions with images, 🔍 for completed diagnoses
- **Smart Session Switching**: Seamless navigation between different plant analysis sessions

### 🎨 **Modern User Experience**
- **WhatsApp-style Text Formatting**: Supports **bold** text formatting in responses
- **Inline Image Preview**: Clean image preview within the chat interface  
- **Responsive Design**: Optimized for various Android screen sizes
- **Intuitive Navigation**: Easy-to-use session management controls
- **Real-time Streaming**: Live response streaming for better user engagement

## 🏗️ Architecture Overview

### **Session Management System**
- **In-Memory Storage**: Fast session switching with in-memory persistence
- **SessionManager**: Centralized session lifecycle management
- **ConversationSession**: Complete session data model with FSM state tracking
- **SessionMetadata**: Lightweight session information for UI display

### **FSM (Finite State Machine) Agent**
- **Intelligent Workflow**: Smart state transitions for plant diagnosis
- **Multi-modal Processing**: Handles both text and image inputs
- **Context Awareness**: Maintains conversation context across interactions
- **Streaming Responses**: Real-time response generation and delivery

## 📱 User Interface

### **Session Management UI**
```
┌─────────────────────────────────────────────┐
│  🌿 Sasya Arogya          👤  ⚙️           │ ← Header Bar
├─────────────────────────────────────────────┤
│ 💬 Sessions: [🌱 Plant Analysis ▼]  [+]   │ ← Session Controls
├─────────────────────────────────────────────┤
│                                             │
│  🌿 Welcome to Sasya Arogya! I can help... │ ← Chat Area
│                                             │
│  👤 Hello! My tomato plant has spots       │
│                                             │
│  🤖 🌿 **PLANT DISEASE ANALYSIS**          │
│     **WHAT WE FOUND:** Tomato Blight...    │
│                                             │
├─────────────────────────────────────────────┤
│ [📷 Image Preview]  [Type message...]  [📤] │ ← Input Area
└─────────────────────────────────────────────┘
```

### **Session Dropdown Features**
- **Current Session Highlighting**: Green dot (●) indicates active session
- **Visual Indicators**: 📷 for image uploads, 🔍 for completed diagnoses  
- **Smart Labeling**: Auto-generated session titles with timestamps
- **Quick Navigation**: One-tap session switching

## 🚀 Usage

### **Analyzing Multiple Plants**
1. **Upload First Plant Image** → System creates initial session
2. **Get Diagnosis & Treatment** → Session marked with 🔍 indicator  
3. **Upload Different Plant** → New session auto-created
4. **Switch Between Sessions** → Use dropdown to navigate histories
5. **Add New Session Manually** → Click + button anytime

### **Session Management**
- **Auto-Creation**: New sessions created automatically when uploading images after existing diagnosis
- **Manual Creation**: Use the + button to create sessions on-demand
- **History Preservation**: All conversations persist across app restarts
- **Visual Tracking**: Clear indicators show session status and content

## Instructions and Pre-requisites for Building the App
Step 1 : Install Android Studio from developer.android.com.
Launch Android Studio → Create New Project → Empty Activity.
Choose:
Language: Kotlin
Minimum SDK: API 24+ (for camera/gallery access)
Finish project creation.
Open AVD Manager (Device Manager) → Create an Emulator.

 Steps to Create an Emulator
 1. Open Device Manager in the right side corner like Phone like Diagram.
 2. Click “+ Create Device”.
 3. Select a Pixel device (Pixel 7). 
 4. Choose a System Image (API 34 "UpsideDownCake"; Android 14.0). ( I have choosen Pixel and System Image Randomly)
 5.Download the system image if not installed.
 6. Name your emulator.
 7.Finish → Now you can run the emulator.


Step 2 : Update AndroidManifest.xml file with my code in app/src/main folder

Step 3 : Update activity_main.xml file with my code in app/src/main/res folder( This file should be in res/layout. If u don't find layout directory then create the Android Resource Directory and Rename it to layout and then create Android Resource File and rename it to activity_main.xml) 

Step 4 : Update MainActivity.kt file with my code in app/src/main/java folder

Step 5: Run on Emulator (Click Run Button on Top ) -- It will take 5-6 min to connect and Run the Emulator

## 🔧 Technical Implementation

### **New Files Added (Latest Update)**
- `fsm/SessionManager.kt` - In-memory session storage and lifecycle management
- `fsm/ConversationSession.kt` - Complete session data model with FSM state
- `fsm/SessionMetadata.kt` - Lightweight session information for UI
- `fsm/SessionSpinnerAdapter.kt` - Custom dropdown adapter for session selection
- `session_spinner_*.xml` - UI layouts for session dropdown components

### **Enhanced Files**
- `MainActivityFSM.kt` - Integrated session management (+233 lines)
- `activity_main.xml` - Added session management UI components (+101 lines)
- `ChatAdapter.kt` - WhatsApp-style **bold** text formatting support

### **Key Classes & Methods**

#### **SessionManager**
```kotlin
class SessionManager {
    fun createNewSession(): ConversationSession
    fun switchToSession(sessionId: String): ConversationSession?
    fun addMessageToSession(sessionId: String, message: ChatMessage)
    fun shouldCreateNewSessionForImage(): Boolean
}
```

#### **ConversationSession**
```kotlin
data class ConversationSession(
    val sessionId: String,
    val title: String,
    val messages: MutableList<ChatMessage>,
    var hasDiagnosis: Boolean,
    var fsmState: FSMSessionState?
)
```

## 📊 Performance & Storage

- **Memory Usage**: Efficient in-memory storage for fast session switching
- **Response Time**: Instant session switching with preserved conversation history  
- **Data Persistence**: In-memory sessions (configurable for disk persistence)
- **UI Responsiveness**: Smooth animations and real-time updates

## 🛠️ Development Features

- **Comprehensive Logging**: Detailed logs for session management and FSM states
- **Error Handling**: Graceful error recovery and user feedback
- **Modular Architecture**: Clean separation of concerns for maintainability
- **Extensible Design**: Easy to add new session management features

## How to check logs

```bash
# get the temp token from the system admin or self generate.
oc login --token=$(echo $OCP_TOKEN) --server=https://api.cluster-mx6z7.mx6z7.sandbox5315.opentlc.com:6443

oc get pods -n sasya-chikitsa

oc logs -f engine-5947d8d5f5-w52l4 -n sasya-chikitsa 

oc logs -f llama318b-6984764f89-22vjl -n sasya-chikitsa
```

## Instruction for running MADR on local

```bash
❯ cd docs
❯ chruby ruby-3.4.1
❯ ruby -v
ruby 3.4.1 (2024-12-25 revision 48d4efcb85) +PRISM [arm64-darwin24]

❯ gem install bundler jekyll
Successfully installed bundler-2.7.1
Successfully installed jekyll-4.4.1
2 gems installed

❯ bundle install
Bundle complete! 6 Gemfile dependencies, 39 gems now installed.
Use `bundle info [gemname]` to see where a bundled gem is installed.

❯ bundle exec jekyll serve
Run in verbose mode to see all warnings.
                    done in 0.223 seconds.
 Auto-regeneration: enabled for '/Users/rajranja/Documents/github/cds-9-group-6/sasya-chikitsa/docs'
    Server address: http://127.0.0.1:4000/
  Server running... press ctrl-c to stop.

```