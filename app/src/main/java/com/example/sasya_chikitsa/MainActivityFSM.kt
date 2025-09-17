package com.example.sasya_chikitsa

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.ImageDecoder
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.util.Base64
import android.util.Log
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.cardview.widget.CardView
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.sasya_chikitsa.config.ServerConfig
import com.example.sasya_chikitsa.fsm.AttentionOverlayData
import com.example.sasya_chikitsa.fsm.ChatAdapter
import com.example.sasya_chikitsa.fsm.ChatMessage
import com.example.sasya_chikitsa.fsm.FSMRetrofitClient
import com.example.sasya_chikitsa.fsm.FSMSessionState
import com.example.sasya_chikitsa.fsm.FSMStateUpdate
import com.example.sasya_chikitsa.fsm.FSMStreamHandler
import com.example.sasya_chikitsa.models.FeedbackManager
import com.example.sasya_chikitsa.models.FeedbackType
import com.example.sasya_chikitsa.models.MessageFeedback
import com.example.sasya_chikitsa.network.RetrofitClient
import com.google.android.material.chip.Chip
import com.google.android.material.chip.ChipGroup
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.InputStream
import java.util.UUID

/**
 * Main Activity with integrated FSM Agent for plant diagnosis
 * Features:
 * - Real-time chat with FSM agent
 * - Streaming responses with state updates
 * - Light green follow-up buttons as requested
 * - Compact "Sasya Arogya" header design
 */
class MainActivityFSM : ComponentActivity(), FSMStreamHandler.StreamCallback {
    
    companion object {
        private const val TAG = "MainActivityFSM"
    }
    
    // UI Components
    private lateinit var profileBtn: ImageButton
    private lateinit var settingsBtn: ImageButton
    private lateinit var chatRecyclerView: RecyclerView
    private lateinit var followUpContainer: LinearLayout
    private lateinit var followUpChipGroup: ChipGroup
    private lateinit var uploadBtn: ImageButton
    private lateinit var messageInput: EditText
    private lateinit var sendBtn: ImageButton
    private lateinit var uploadSection: CardView
    private lateinit var imagePreview: ImageView
    private lateinit var imageFileName: TextView
    private lateinit var removeImageBtn: ImageButton
    
    // FSM Components
    private lateinit var chatAdapter: ChatAdapter
    private lateinit var streamHandler: FSMStreamHandler
    private var currentSessionState = FSMSessionState(
        sessionId = "fsm_${UUID.randomUUID().toString()}" // FIXED: Generate proper session ID  
    )
    
    // Image handling
    private var selectedImageUri: Uri? = null
    private var selectedImageBase64: String? = null
    
    // Thinking indicator
    private var isThinking = false
    private var thinkingAnimation: Runnable? = null
    private var thinkingMessage: ChatMessage? = null
    
    // Image picker launcher
    private val imagePickerLauncher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri ->
        uri?.let { handleSelectedImage(it) }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Log the session ID that was created
        Log.i(TAG, "🆔 FSM Session created: ${currentSessionState.sessionId}")
        
        initializeFSMComponents()
        initializeViews()
        setupClickListeners()
        setupRecyclerView()
        
        // Add welcome message
        addWelcomeMessage()
        
        // Copy test images to gallery on first launch
        copyTestImagesToGallery()
        
        Log.d(TAG, "FSM Activity initialized")
    }
    
    private fun initializeFSMComponents() {
        // Initialize FSM Retrofit client
        FSMRetrofitClient.initialize(this)
        
        // Initialize stream handler
        streamHandler = FSMStreamHandler()
        
        // Initialize chat adapter
        chatAdapter = ChatAdapter(
            onFollowUpClick = { followUpText ->
            handleFollowUpClick(followUpText)
            },
            onThumbsUpClick = { chatMessage ->
                handleThumbsUpFeedback(chatMessage)
            },
            onThumbsDownClick = { chatMessage ->
                handleThumbsDownFeedback(chatMessage)
            }
        )
        
        Log.d(TAG, "FSM components initialized")
    }
    
    private fun initializeViews() {
        // Header components
        profileBtn = findViewById(R.id.profileBtn)
        settingsBtn = findViewById(R.id.settingsBtn)
        
        // Chat components
        chatRecyclerView = findViewById(R.id.chatRecyclerView)
        followUpContainer = findViewById(R.id.followUpContainer)
        followUpChipGroup = findViewById(R.id.followUpChipGroup)
        
        // Input components
        uploadBtn = findViewById(R.id.uploadBtn)
        messageInput = findViewById(R.id.messageInput)
        sendBtn = findViewById(R.id.sendBtn)
        uploadSection = findViewById(R.id.uploadSection)
        imagePreview = findViewById(R.id.imagePreview)
        imageFileName = findViewById(R.id.imageFileName)
        removeImageBtn = findViewById(R.id.removeImageBtn)
        
        // Initialize profile button state
        updateProfileButtonState()
    }
    
    private fun setupClickListeners() {
        uploadBtn.setOnClickListener { openImagePicker() }
        sendBtn.setOnClickListener { sendMessage() }
        removeImageBtn.setOnClickListener { clearSelectedImage() }
        profileBtn.setOnClickListener { showAgriculturalProfileDialog() }
        settingsBtn.setOnClickListener { showServerSettings() }
        
        // Enter key to send message
        messageInput.setOnKeyListener { _, keyCode, event ->
            if (keyCode == android.view.KeyEvent.KEYCODE_ENTER && event.action == android.view.KeyEvent.ACTION_DOWN) {
                sendMessage()
                true
            } else false
        }
    }
    
    private fun setupRecyclerView() {
        val layoutManager = LinearLayoutManager(this)
        layoutManager.stackFromEnd = true
        chatRecyclerView.layoutManager = layoutManager
        chatRecyclerView.adapter = chatAdapter
    }
    
    private fun addWelcomeMessage() {
        val welcomeMessage = ChatMessage(
            text = "🌿 Welcome to Sasya Arogya! I'm your intelligent plant health assistant.\n\nI can help you:\n• Diagnose plant diseases from images\n• Recommend treatments and medicines\n• Connect you with local vendors\n• Provide seasonal care advice\n\nHow can I help you today?",
            isUser = false,
            state = "Ready"
        )
        
        chatAdapter.addMessage(welcomeMessage)
        currentSessionState.messages.add(welcomeMessage)
        scrollToBottom()
    }
    
    private fun openImagePicker() {
        try {
            imagePickerLauncher.launch("image/*")
        } catch (e: Exception) {
            Log.e(TAG, "Error opening image picker", e)
            showError("Failed to open image picker: ${e.message}")
        }
    }
    
    private fun handleSelectedImage(uri: Uri) {
        try {
            selectedImageUri = uri
            
            // Convert to bitmap and base64
            val bitmap = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                ImageDecoder.decodeBitmap(ImageDecoder.createSource(contentResolver, uri))
            } else {
                @Suppress("DEPRECATION")
                MediaStore.Images.Media.getBitmap(contentResolver, uri)
            }
            
            // Resize bitmap if too large
            val resizedBitmap = resizeBitmap(bitmap, 1024)
            selectedImageBase64 = bitmapToBase64(resizedBitmap)
            
            // Show image preview
            imagePreview.setImageBitmap(resizedBitmap)
            imageFileName.text = "📷 Image selected"
            uploadSection.visibility = View.VISIBLE
            
            Log.d(TAG, "Image selected and processed")
            
        } catch (e: Exception) {
            Log.e(TAG, "Error processing selected image", e)
            showError("Error processing image: ${e.message}")
        }
    }
    
    private fun clearSelectedImage() {
        selectedImageUri = null
        selectedImageBase64 = null
        uploadSection.visibility = View.GONE
        Log.d(TAG, "Image cleared")
    }
    
    private fun sendMessage() {
        val messageText = messageInput.text.toString().trim()
        if (messageText.isEmpty() && selectedImageBase64 == null) {
            return
        }
        
        // Create user message
        val userMessage = ChatMessage(
            text = if (messageText.isEmpty()) "📷 [Image uploaded]" else messageText,
            isUser = true,
            imageUri = selectedImageUri?.toString()
        )
        
        // Add user message to chat
        chatAdapter.addMessage(userMessage)
        currentSessionState.messages.add(userMessage)
        scrollToBottom()
        
        // Clear input
        messageInput.text.clear()
        val imageB64 = selectedImageBase64
        clearSelectedImage()
        
        // Send to FSM agent
        sendToFSMAgent(messageText.ifEmpty { "Please analyze this plant image" }, imageB64)
        
        // Show thinking indicator
        showThinkingIndicator()
        
        // Status updates handled by profile button state management
    }
    
    private fun sendToFSMAgent(message: String, imageBase64: String?) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                // Get agricultural profile for personalized responses
                val userProfile = getUserAgriculturalProfile()
                
                // Debug: Log what profile we got
                Log.d(TAG, "🌾 User agricultural profile: $userProfile")
                
                val context = createEnrichedContext(userProfile)
                
                // Debug: Log the context being sent to server
                Log.d(TAG, "📤 Sending context to server: $context")
                
                val request = streamHandler.createChatRequest(
                    message = message,
                    imageBase64 = imageBase64,
                    sessionId = currentSessionState.sessionId,
                    context = context
                )
                
                Log.d(TAG, "Sending request to FSM agent: $message")
                
                val call = FSMRetrofitClient.apiService.chatStream(request)
                val response = call.execute()
                
                if (response.isSuccessful && response.body() != null) {
                    streamHandler.processStream(response.body()!!, this@MainActivityFSM)
                } else {
                    withContext(Dispatchers.Main) {
                        showError("Failed to connect to FSM agent: ${response.message()}")
                        // Error state handled by user interaction, not status indicator
                    }
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Error sending message to FSM agent", e)
                withContext(Dispatchers.Main) {
                    showError("Connection error: ${e.message}")
                    // Error state handled by user interaction, not status indicator
                }
            }
        }
    }
    
    /**
     * Create enriched context with agricultural profile for personalized responses
     */
    private fun createEnrichedContext(userProfile: Map<String, String>): Map<String, Any> {
        // Helper function to get non-empty value or default
        fun getValueOrDefault(key: String, default: String): String {
            return userProfile[key]?.let { if (it.isBlank()) default else it } ?: default
        }
        
        val userState = getValueOrDefault("state", "Tamil Nadu")
        val userFarmSize = getValueOrDefault("farm_size", "Small (< 1 acre)")
        val currentSeason = getCurrentSeason()
        
        Log.d(TAG, "🏛️ Using state: $userState, farm size: $userFarmSize, season: $currentSeason")
        
        return mapOf(
            // Platform information
            "platform" to "android",
            "app_version" to "1.0.0",
            "timestamp" to System.currentTimeMillis(),
            
            // Agricultural context for personalized responses
            "location" to userState,
            "state" to userState,  
            "farm_size" to userFarmSize,
            "farming_experience" to "intermediate", // Default value
            "crop_type" to "general", // Default to general plant diagnosis
            "season" to currentSeason,
            "growth_stage" to "unknown", // Can be determined from image analysis
            
            // Request preferences
            "streaming_requested" to true,
            "detailed_analysis" to true,
            "include_confidence" to true,
            "image_source" to "android_camera",
            "fsm_version" to "2.0" // FSM agent version
        )
    }
    
    /**
     * Get current season based on current month (0-based: Jan=0, Dec=11)
     */
    private fun getCurrentSeason(): String {
        val calendar = java.util.Calendar.getInstance()
        val month = calendar.get(java.util.Calendar.MONTH)
        Log.d(TAG, "🗓️ Current month (0-based): $month")
        return when (month) {
            in 2..4 -> "spring"      // March(2) - May(4)
            in 5..7 -> "summer"      // June(5) - August(7)  
            in 8..10 -> "autumn"     // September(8) - November(10)
            else -> "winter"         // December(11) - February(1)
        }
    }
    
    private fun handleFollowUpClick(followUpText: String) {
        Log.d(TAG, "Follow-up clicked: $followUpText")
        
        // Add follow-up as user message
        val followUpMessage = ChatMessage(
            text = followUpText,
            isUser = true
        )
        
        chatAdapter.addMessage(followUpMessage)
        currentSessionState.messages.add(followUpMessage)
        scrollToBottom()
        
        // Send to FSM agent
        sendToFSMAgent(followUpText, null)
        
        // Show thinking indicator
        showThinkingIndicator()
        // Processing state handled by thinking indicator, not status indicator
        
        // Hide follow-up container
        followUpContainer.visibility = View.GONE
    }
    
    // FSM Stream Callback implementations
    override fun onStateUpdate(stateUpdate: FSMStateUpdate) {
        Log.d(TAG, "State update: ${stateUpdate.currentNode}")
        
        stateUpdate.currentNode?.let { node ->
            currentSessionState.currentNode = node
            currentSessionState.previousNode = stateUpdate.previousNode
            
            val displayName = streamHandler.getStateDisplayName(node)
            // State display handled by UI elements, not banner status indicator
        }
        
        // Update session ID if provided
        stateUpdate.toString().let { 
            // Extract session_id if present in the data
        }
    }
    
    override fun onMessage(message: String) {
        Log.d(TAG, "Received message: $message")
        
        runOnUiThread {
            // Stop thinking indicator when we receive first message
            stopThinkingIndicator()
            
            // WhatsApp-style: Accumulate all streaming responses into ONE message card
            if (currentSessionState.messages.isNotEmpty() && 
                !currentSessionState.messages.last().isUser) {
                
                // Continue building the current assistant response
                val currentMessage = currentSessionState.messages.last()
                val updatedText = if (currentMessage.text.isBlank()) {
                    message
                } else {
                    "${currentMessage.text}\n\n$message"
                }
                
                // Update the existing message card with accumulated content
                chatAdapter.updateLastMessage(updatedText)
                currentSessionState.messages[currentSessionState.messages.size - 1] = 
                    currentMessage.copy(text = updatedText)
            } else {
                // Start new assistant response card
                val assistantMessage = ChatMessage(
                    text = message,
                    isUser = false,
                    state = streamHandler.getStateDisplayName(currentSessionState.currentNode)
                )
                chatAdapter.addMessage(assistantMessage)
                currentSessionState.messages.add(assistantMessage)
            }
            scrollToBottom()
        }
    }
    
    override fun onFollowUpItems(items: List<String>) {
        Log.d(TAG, "Received follow-up items: $items")
        
        runOnUiThread {
            if (items.isNotEmpty()) {
                // Add follow-ups as light green clickable buttons within the message card (WhatsApp style)
                chatAdapter.addFollowUpToLastMessage(items)
                
                // Hide the separate follow-up container since we're using in-card buttons
                followUpContainer.visibility = View.GONE
            }
        }
    }
    
    override fun onAttentionOverlay(overlayData: AttentionOverlayData) {
        Log.d(TAG, "🎯 Received attention overlay from ${overlayData.sourceNode}: disease=${overlayData.diseaseName}, confidence=${overlayData.confidence}")
        runOnUiThread {
            if (currentSessionState.messages.isNotEmpty() && 
                !currentSessionState.messages.last().isUser && 
                overlayData.attentionOverlay != null) {
                
                // Add attention overlay to the last assistant message
                val lastMessage = currentSessionState.messages.last()
                val updatedMessage = lastMessage.copy(
                    attentionOverlayBase64 = overlayData.attentionOverlay,
                    diseaseName = overlayData.diseaseName,
                    confidence = overlayData.confidence
                )
                
                // Update message and notify adapter
                currentSessionState.messages[currentSessionState.messages.size - 1] = updatedMessage
                chatAdapter.updateLastMessageWithOverlay(updatedMessage)
                
                Log.d(TAG, "✅ Added attention overlay to last message")
            }
        }
    }
    
    override fun onError(error: String) {
        Log.e(TAG, "Stream error: $error")
        runOnUiThread {
            stopThinkingIndicator()
            showError(error)
            // Error state handled by user interaction, not status indicator
        }
    }
    
    override fun onStreamComplete() {
        Log.d(TAG, "Stream completed")
        runOnUiThread {
            stopThinkingIndicator()
            // Status updates no longer needed - profile button manages its own state
        }
    }
    
    /**
     * Update profile button based on user's agricultural profile setup status
     */
    private fun updateProfileButtonState() {
        runOnUiThread {
            val prefs = getSharedPreferences("agricultural_profile", Context.MODE_PRIVATE)
            val hasProfile = prefs.getBoolean("profile_setup_completed", false)
            
            if (hasProfile) {
                // User has profile - show normal green tint
                profileBtn.setColorFilter(ContextCompat.getColor(this, R.color.forest_green))
                profileBtn.contentDescription = "View Agricultural Profile"
            } else {
                // User needs to set up profile - show attention-grabbing color
                profileBtn.setColorFilter(ContextCompat.getColor(this, R.color.warm_amber))
                profileBtn.contentDescription = "Set Up Agricultural Profile"
            }
        }
    }
    
    private fun showFollowUpItems(items: List<String>) {
        followUpChipGroup.removeAllViews()
        
        items.forEach { item ->
            val chip = Chip(this).apply {
                text = item
                isClickable = true
                isCheckable = false
                
                // Apply light green styling as requested
                setChipBackgroundColorResource(R.color.followup_chip_background)
                setTextColor(resources.getColor(R.color.followup_chip_text, theme))
                chipStrokeColor = resources.getColorStateList(R.color.followup_chip_stroke, theme)
                chipStrokeWidth = 4f
                
                setOnClickListener {
                    // Change appearance
                    setChipBackgroundColorResource(R.color.followup_chip_clicked)
                    text = "✓ $item"
                    isClickable = false
                    
                    handleFollowUpClick(item)
                }
            }
            followUpChipGroup.addView(chip)
        }
        
        followUpContainer.visibility = View.VISIBLE
    }
    
    private fun scrollToBottom() {
        if (chatAdapter.itemCount > 0) {
            chatRecyclerView.smoothScrollToPosition(chatAdapter.itemCount - 1)
        }
    }
    
    private fun showError(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
    }
    
    /**
     * Show dedicated server configuration dialog
     */
    private fun showServerSettings() {
        try {
            val dialogView = layoutInflater.inflate(R.layout.dialog_server_url, null)
            val urlSpinner = dialogView.findViewById<Spinner>(R.id.urlSpinner)
            val customUrlInput = dialogView.findViewById<EditText>(R.id.customUrlInput)

            // Get available server options from ServerConfig
            val defaultUrls = ServerConfig.getDefaultUrls()
            val serverOptions = defaultUrls.map { it.first }

            // Setup spinner
            val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, serverOptions)
            adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
            urlSpinner.adapter = adapter

            // Get current server configuration and set selection
            val currentUrl = ServerConfig.getServerUrl(this)
            val currentIndex = defaultUrls.indexOfFirst { it.second == currentUrl }
                .takeIf { it >= 0 } ?: (defaultUrls.size - 1) // Default to "Custom URL" if not found

            urlSpinner.setSelection(currentIndex)

            // Show/hide custom URL input based on selection
            urlSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
                override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
                    val isCustom = position == defaultUrls.size - 1 // Last option is "Custom URL"
                    customUrlInput.visibility = if (isCustom) View.VISIBLE else View.GONE
                    
                    if (isCustom) {
                        customUrlInput.setText(currentUrl)
                        customUrlInput.requestFocus()
                    }
                }
                override fun onNothingSelected(parent: AdapterView<*>?) {}
            }

            // Trigger initial selection to show/hide custom input
            urlSpinner.onItemSelectedListener?.onItemSelected(urlSpinner, null, currentIndex, 0)

            AlertDialog.Builder(this)
                .setTitle("🌐 Server Configuration")
                .setMessage("Select your server endpoint for the Sasya Chikitsa AI assistant:")
                .setView(dialogView)
                .setPositiveButton("Connect") { _, _ ->
                    val selectedPosition = urlSpinner.selectedItemPosition
                    val newUrl = if (selectedPosition == defaultUrls.size - 1) {
                        // Custom URL selected
                        var customUrl = customUrlInput.text.toString().trim()
                        if (customUrl.isNotEmpty() && !customUrl.endsWith("/")) {
                            customUrl += "/"
                        }
                        customUrl
                    } else {
                        // Preset URL selected
                        defaultUrls[selectedPosition].second
                    }

                    if (newUrl.isNotEmpty() && ServerConfig.isValidUrl(newUrl)) {
                        ServerConfig.setServerUrl(this, newUrl)
                        
                        val serverName = if (selectedPosition == defaultUrls.size - 1) "Custom Server" else defaultUrls[selectedPosition].first
                        Toast.makeText(this, "✅ Connected to $serverName\n$newUrl", Toast.LENGTH_LONG).show()
                        
                        Log.d(TAG, "Server URL updated to: $newUrl")
                        
                        // Refresh FSM client with new URL
                        FSMRetrofitClient.initialize(this)
                    } else {
                        Toast.makeText(this, "❌ Please enter a valid URL (e.g., http://192.168.1.100:8080/)", Toast.LENGTH_LONG).show()
                    }
                }
                .setNeutralButton("Test Connection") { _, _ ->
                    val selectedPosition = urlSpinner.selectedItemPosition
                    val testUrl = if (selectedPosition == defaultUrls.size - 1) {
                        customUrlInput.text.toString().trim()
                    } else {
                        defaultUrls[selectedPosition].second
                    }
                    testServerConnection(testUrl)
                }
                .setNegativeButton("Cancel", null)
                .show()
                
        } catch (e: Exception) {
            Log.e(TAG, "Error showing server settings dialog: ${e.message}", e)
            Toast.makeText(this, "Failed to show server settings: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }
    
    /**
     * Test server connection
     */
    private fun testServerConnection(url: String) {
        if (url.isEmpty() || !ServerConfig.isValidUrl(url)) {
            Toast.makeText(this, "❌ Invalid URL format", Toast.LENGTH_SHORT).show()
            return
        }
        
        Toast.makeText(this, "🔄 Testing connection to $url...", Toast.LENGTH_SHORT).show()
        
        CoroutineScope(Dispatchers.IO).launch {
            try {
                // Create a test request to check server connectivity
                val testUrl = if (!url.endsWith("/")) "$url/" else url
                val response = RetrofitClient.getApiService(testUrl).testConnection()
                
                withContext(Dispatchers.Main) {
                    if (response.isSuccessful) {
                        Toast.makeText(this@MainActivityFSM, "✅ Server connection successful!", Toast.LENGTH_LONG).show()
                    } else {
                        Toast.makeText(this@MainActivityFSM, "⚠️ Server responded but may not be fully ready (${response.code()})", Toast.LENGTH_LONG).show()
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    Toast.makeText(this@MainActivityFSM, "❌ Connection failed: ${e.message}", Toast.LENGTH_LONG).show()
                    Log.e(TAG, "Server connection test failed for $url", e)
                }
            }
        }
    }
    
    // Server status management removed - profile button replaced status indicator
    
    /**
     * Show dialog to collect/update user agricultural profile
     */
    private fun showAgriculturalProfileDialog() {
        val currentProfile = getUserAgriculturalProfile()
        val dialogView = layoutInflater.inflate(R.layout.dialog_agricultural_profile, null)
        
        // Get dialog elements
        val stateSpinner = dialogView.findViewById<Spinner>(R.id.stateSpinner)
        val farmSizeSpinner = dialogView.findViewById<Spinner>(R.id.farmSizeSpinner)
        
        // Set up spinners
        setupProfileSpinner(stateSpinner, getStateOptions(), currentProfile["state"])
        setupProfileSpinner(farmSizeSpinner, getFarmSizeOptions(), currentProfile["farm_size"])
        
        AlertDialog.Builder(this)
            .setTitle("🌱 Agricultural Profile")
            .setMessage("Help us provide personalized plant advice:")
            .setView(dialogView)
            .setPositiveButton("Save") { _, _ ->
                val newProfile = mapOf(
                    "state" to stateSpinner.selectedItem.toString(),
                    "farm_size" to farmSizeSpinner.selectedItem.toString()
                )
                saveAgriculturalProfile(newProfile)
                Toast.makeText(this, "✅ Profile saved successfully!", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun getUserAgriculturalProfile(): Map<String, String> {
        val prefs = getSharedPreferences("agricultural_profile", Context.MODE_PRIVATE)
        return mapOf(
            "state" to (prefs.getString("state", null) ?: ""),
            "farm_size" to (prefs.getString("farm_size", null) ?: "")
        )
    }
    
    private fun saveAgriculturalProfile(profile: Map<String, String>) {
        val prefs = getSharedPreferences("agricultural_profile", Context.MODE_PRIVATE)
        val editor = prefs.edit()
        
        profile.forEach { (key, value) ->
            editor.putString(key, value)
        }
        editor.putBoolean("profile_setup_completed", true)
        editor.apply()
        
        // Update profile button to reflect completed setup
        updateProfileButtonState()
    }
    
    private fun setupProfileSpinner(spinner: Spinner, options: List<String>, selectedValue: String?) {
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, options)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        spinner.adapter = adapter
        
        selectedValue?.let { value ->
            val position = options.indexOf(value)
            if (position >= 0) {
                spinner.setSelection(position)
            }
        }
    }
    
    private fun getStateOptions() = listOf(
        "Tamil Nadu", "Karnataka", "Andhra Pradesh", "Telangana", "Kerala",
        "Maharashtra", "Gujarat", "Rajasthan", "Punjab", "Haryana",
        "Uttar Pradesh", "Madhya Pradesh", "Bihar", "West Bengal", "Odisha"
    )
    
    private fun getFarmSizeOptions() = listOf(
        "Small (< 1 acre)",
        "Medium (1-5 acres)", 
        "Large (5-10 acres)",
        "Very Large (> 10 acres)"
    )
    
    /**
     * Copy bundled test images to device photo gallery on first launch
     */
    private fun copyTestImagesToGallery() {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val prefs = getSharedPreferences("app_setup", Context.MODE_PRIVATE)
                val imagesCopied = prefs.getBoolean("test_images_copied_v2", false)
                
                if (!imagesCopied) {
                    Log.d(TAG, "📸 Copying test images to device gallery...")
                    
                    val testImages = listOf(
                        // Original test images
                        R.raw.apple_mosaic_1 to "Apple Mosaic Disease - Sample 1.jpg",
                        R.raw.apple_mosaic_2 to "Apple Mosaic Disease - Sample 2.jpg", 
                        R.raw.eggplant_leaf_spot to "Eggplant Leaf Spot Disease - Sample.jpg",
                        R.raw.eggplant_mosaic_virus to "Eggplant Mosaic Virus - Sample.jpg",
                        
                        // New comprehensive test images for attention overlay testing
                        R.raw.apple_alternaria_early_blight_multi_leaves_1 to "Apple Alternaria Early Blight - Multi Leaves 1.jpg",
                        R.raw.apple_alternaria_early_blight_multi_leaves_2 to "Apple Alternaria Early Blight - Multi Leaves 2.jpg",
                        R.raw.apple_healthy_multi_leaves_1 to "Apple Healthy - Multi Leaves Sample.jpg",
                        R.raw.apple_healthy to "Apple Healthy - Single Leaf Sample.jpg",
                        R.raw.apple_tomato_mosaic_virus_1 to "Apple Tomato Mosaic Virus - Sample 1.jpg",
                        R.raw.apple_tomato_mosaic_virus_multi_leaves to "Apple Tomato Mosaic Virus - Multi Leaves.jpg",
                        R.raw.apple_leaf_root_rot to "Apple Leaf Root Rot Disease.jpg",
                        R.raw.healthy_leaf_image_test to "Healthy Leaf Test Image.jpg",
                        R.raw.leaf_with_spotting to "Leaf with Spotting Disease.jpg",
                        R.raw.potato_fungi_2_leaves to "Potato Fungal Disease - 2 Leaves.jpg",
                        R.raw.potato_healthy_multi_1 to "Potato Healthy - Multi Sample 1.jpg",
                        R.raw.potato_healthy_multi_2 to "Potato Healthy - Multi Sample 2.jpg", 
                        R.raw.potato_healthy_multi_leaves_1 to "Potato Healthy - Multi Leaves Sample.jpg",
                        R.raw.tomato_dry to "Tomato Dry Condition Sample.jpg",
                        R.raw.tomato_mosaic_virus to "Tomato Mosaic Virus Disease.jpg",
                        R.raw.tomato_fruit_borer to "Tomato Fruit Borer Damage.jpg"
                    )
                    
                    var copiedCount = 0
                    testImages.forEach { (resourceId, displayName) ->
                        if (copyRawImageToGallery(resourceId, displayName)) {
                            copiedCount++
                        }
                    }
                    
                    // Mark as completed
                    prefs.edit().putBoolean("test_images_copied_v2", true).apply()
                    
                    withContext(Dispatchers.Main) {
                        if (copiedCount > 0) {
                            Toast.makeText(
                                this@MainActivityFSM,
                                "✅ $copiedCount sample plant images added to your gallery for testing!",
                                Toast.LENGTH_LONG
                            ).show()
                            Log.d(TAG, "📸 Successfully copied $copiedCount test images to gallery")
                        }
                    }
                } else {
                    Log.d(TAG, "📸 Test images already copied to gallery")
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Error copying test images to gallery", e)
                withContext(Dispatchers.Main) {
                    Toast.makeText(this@MainActivityFSM, "⚠️ Could not add sample images to gallery", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }
    
    /**
     * Copy a single raw resource image to the device gallery
     */
    private fun copyRawImageToGallery(resourceId: Int, displayName: String): Boolean {
        return try {
            // Open raw resource file
            val inputStream: InputStream = resources.openRawResource(resourceId)
            
            // Prepare content values for MediaStore
            val contentValues = ContentValues().apply {
                put(MediaStore.Images.Media.DISPLAY_NAME, displayName)
                put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")
                put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/Sasya Chikitsa Samples")
            }
            
            // Insert into MediaStore
            val uri = contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, contentValues)
            
            if (uri != null) {
                // Write image data
                contentResolver.openOutputStream(uri)?.use { outputStream ->
                    inputStream.copyTo(outputStream)
                }
                inputStream.close()
                
                Log.d(TAG, "✅ Successfully copied $displayName to gallery")
                true
            } else {
                Log.e(TAG, "❌ Failed to create MediaStore entry for $displayName")
                inputStream.close()
                false
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "❌ Error copying resource $resourceId to gallery", e)
            false
        }
    }
    
    // Utility methods
    private fun resizeBitmap(bitmap: Bitmap, maxSize: Int): Bitmap {
        val width = bitmap.width
        val height = bitmap.height
        
        if (width <= maxSize && height <= maxSize) {
            return bitmap
        }
        
        val ratio = minOf(maxSize.toFloat() / width, maxSize.toFloat() / height)
        val newWidth = (width * ratio).toInt()
        val newHeight = (height * ratio).toInt()
        
        return Bitmap.createScaledBitmap(bitmap, newWidth, newHeight, true)
    }
    
    private fun bitmapToBase64(bitmap: Bitmap): String {
        val byteArrayOutputStream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 80, byteArrayOutputStream)
        val byteArray = byteArrayOutputStream.toByteArray()
        return Base64.encodeToString(byteArray, Base64.DEFAULT)
    }
    
    // Thinking Indicator Methods
    private fun showThinkingIndicator() {
        Log.d(TAG, "🤔 Showing thinking indicator")
        
        isThinking = true
        
        // Create thinking message
        thinkingMessage = ChatMessage(
            text = "🤖 Sasya Arogya Thinking",
            isUser = false,
            state = "Thinking"
        )
        
        chatAdapter.addMessage(thinkingMessage!!)
        currentSessionState.messages.add(thinkingMessage!!)
        scrollToBottom()
        
        // Start dot animation
        startThinkingAnimation()
    }
    
    private fun startThinkingAnimation() {
        var dotCount = 0
        
        thinkingAnimation = object : Runnable {
            override fun run() {
                if (!isThinking) return
                
                runOnUiThread {
                    val dots = ".".repeat((dotCount % 3) + 1)
                    val thinkingText = "🤖 Sasya Arogya Thinking$dots"
                    
                    // Update the thinking message
                    thinkingMessage?.let { message ->
                        val updatedMessage = message.copy(text = thinkingText)
                        val messageIndex = currentSessionState.messages.indexOf(message)
                        if (messageIndex != -1) {
                            currentSessionState.messages[messageIndex] = updatedMessage
                            chatAdapter.updateLastMessage(thinkingText)
                            thinkingMessage = updatedMessage
                        }
                    }
                    
                    dotCount++
                    
                    // Schedule next update if still thinking
                    if (isThinking) {
                        chatRecyclerView.postDelayed(thinkingAnimation!!, 500)
                    }
                }
            }
        }
        
        chatRecyclerView.postDelayed(thinkingAnimation!!, 500)
    }
    
    private fun stopThinkingIndicator() {
        if (!isThinking) return
        
        Log.d(TAG, "🛑 Stopping thinking indicator")
        
        isThinking = false
        
        // Cancel animation
        thinkingAnimation?.let { 
            chatRecyclerView.removeCallbacks(it)
            thinkingAnimation = null
        }
        
        // Remove thinking message from chat
        thinkingMessage?.let { message ->
            val messageIndex = currentSessionState.messages.indexOf(message)
            if (messageIndex != -1) {
                currentSessionState.messages.removeAt(messageIndex)
                // Recreate the entire adapter to remove the message
                val tempMessages = currentSessionState.messages.toList()
                chatAdapter.clear()
                tempMessages.forEach { chatAdapter.addMessage(it) }
                scrollToBottom()
            }
            thinkingMessage = null
        }
    }
    
    // Feedback handling methods
    private fun handleThumbsUpFeedback(chatMessage: ChatMessage) {
        Log.d(TAG, "👍 Thumbs up feedback for message: ${chatMessage.text.take(50)}...")
        
        // Record feedback using FeedbackManager
        val feedback = MessageFeedback(
            messageText = chatMessage.text,
            feedbackType = FeedbackType.THUMBS_UP,
            sessionId = currentSessionState.sessionId,
            userContext = "User gave positive feedback in FSM chat"
        )
        FeedbackManager.recordFeedback(feedback)
        
        runOnUiThread {
            Toast.makeText(this, "👍 Thanks for your feedback!", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun handleThumbsDownFeedback(chatMessage: ChatMessage) {
        Log.d(TAG, "👎 Thumbs down feedback for message: ${chatMessage.text.take(50)}...")
        
        // Record feedback using FeedbackManager
        val feedback = MessageFeedback(
            messageText = chatMessage.text,
            feedbackType = FeedbackType.THUMBS_DOWN,
            sessionId = currentSessionState.sessionId,
            userContext = "User gave negative feedback in FSM chat - needs improvement"
        )
        FeedbackManager.recordFeedback(feedback)
        
        runOnUiThread {
            Toast.makeText(this, "👎 Thanks for your feedback! We'll improve.", Toast.LENGTH_SHORT).show()
        }
    }
}
