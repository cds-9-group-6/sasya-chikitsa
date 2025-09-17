package com.example.sasya_chikitsa

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Bitmap
import android.graphics.ImageDecoder
import android.graphics.Typeface
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
import android.text.SpannableString
import android.text.SpannableStringBuilder
import android.text.Spanned
import android.text.method.LinkMovementMethod
import android.text.style.ClickableSpan
import android.text.style.ForegroundColorSpan
import android.text.style.StyleSpan
import android.text.style.UnderlineSpan
import android.util.Base64
import android.util.Log
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.cardview.widget.CardView
import androidx.core.content.ContextCompat
import com.example.sasya_chikitsa.config.ServerConfig
import com.example.sasya_chikitsa.network.RetrofitClient
import com.example.sasya_chikitsa.network.request.ChatRequestData
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONException
import org.json.JSONObject
import java.io.BufferedReader
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.io.InputStreamReader
import java.util.UUID

class MainActivity : ComponentActivity() {
    private lateinit var imagePreview: ImageView
    private lateinit var uploadBtn: ImageButton
    private lateinit var sendBtn: ImageButton
    private lateinit var messageInput: EditText
    private lateinit var removeImageBtn: ImageButton
    private lateinit var uploadSection: CardView
    private lateinit var imageFileName: TextView
    private lateinit var settingsBtn: ImageButton
    private lateinit var fsmModeBtn: ImageButton // Stub initialization in onCreate

    // Note: Chat interface replaced with RecyclerView in MainActivityFSM.kt  
    private lateinit var responseTextView: TextView // Stub initialization in onCreate
    private lateinit var conversationScrollView: ScrollView // Stub initialization in onCreate
    private lateinit var conversationContainer: LinearLayout // Stub initialization in onCreate

    private var selectedImageUri: Uri? = null
    private var conversationHistory =
        SpannableStringBuilder() // Store conversation history with formatting

    // Data class for conversation messages with images and attention overlay
    data class ConversationMessage(
        val text: String,
        val isUser: Boolean,
        val imageUri: Uri? = null,
        val attentionOverlayData: String? = null, // Base64 attention overlay
        val timestamp: Long = System.currentTimeMillis()
    )

    // List to store conversation messages with images
    private val conversationMessages = mutableListOf<ConversationMessage>()

    // Store attention overlay data during streaming
    private var currentAttentionOverlayData: String? = null

    private val TAG = "MainActivity" // For logging
    
    // Modern Activity Result API for image selection
    private val imagePickerLauncher =
        registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) {
            try {
                showSelectedImage(uri)
//                Toast.makeText(this, "Image selected.", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                Log.e(TAG, "Error handling selected image", e)
                    Toast.makeText(this, "Error processing image: ${e.message}", Toast.LENGTH_LONG)
                        .show()
                }
            }
        }

    // Conversation persistence functions
    private fun saveConversations() {
        try {
            val gson = Gson()
            val sharedPrefs = getSharedPreferences("sasya_chikitsa_conversations", MODE_PRIVATE)

            // Convert conversation messages to JSON, excluding imageUri (can't persist Uri easily)
            val conversationsToSave = conversationMessages.map { message ->
                ConversationMessage(
                    text = message.text,
                    isUser = message.isUser,
                    imageUri = null, // Don't persist image URIs - they become invalid
                    attentionOverlayData = message.attentionOverlayData,
                    timestamp = message.timestamp
                )
            }

            val conversationsJson = gson.toJson(conversationsToSave)
            val conversationHistoryText = conversationHistory.toString()

            sharedPrefs.edit()
                .putString("conversation_messages", conversationsJson)
                .putString("conversation_history", conversationHistoryText)
                .putLong("last_saved", System.currentTimeMillis())
                .apply()

            Log.d(TAG, "💾 Conversations saved: ${conversationMessages.size} messages")
        } catch (e: Exception) {
            Log.e(TAG, "❌ Failed to save conversations", e)
        }
    }

    private fun loadConversations() {
        try {
            val gson = Gson()
            val sharedPrefs = getSharedPreferences("sasya_chikitsa_conversations", MODE_PRIVATE)

            val conversationsJson = sharedPrefs.getString("conversation_messages", null)
            val historyText = sharedPrefs.getString("conversation_history", null)

            if (conversationsJson != null) {
                val type = object : TypeToken<List<ConversationMessage>>() {}.type
                val loadedMessages: List<ConversationMessage> =
                    gson.fromJson(conversationsJson, type)

                conversationMessages.clear()
                conversationMessages.addAll(loadedMessages)

                Log.d(TAG, "📱 Conversations loaded: ${conversationMessages.size} messages")
            }

            if (historyText != null) {
                conversationHistory.clear()
                conversationHistory.append(historyText)
                Log.d(
                    TAG,
                    "📜 Conversation history loaded: ${conversationHistory.length} characters"
                )
            }

            // Update display after loading
            if (conversationMessages.isNotEmpty()) {
                updateConversationDisplay()
                scrollToResponseEnd()
            }

        } catch (e: Exception) {
            Log.e(TAG, "❌ Failed to load conversations", e)
            // Initialize empty conversations if loading fails
            conversationMessages.clear()
            conversationHistory.clear()
        }
    }

    private fun clearConversations() {
        try {
            conversationMessages.clear()
            conversationHistory.clear()

            val sharedPrefs = getSharedPreferences("sasya_chikitsa_conversations", MODE_PRIVATE)
            sharedPrefs.edit().clear().apply()

            // Clear conversation display
            if (conversationContainer.childCount > 1) {
                conversationContainer.removeViews(1, conversationContainer.childCount - 1)
            }
            responseTextView.text = ""

            Log.d(TAG, "🗑️ All conversations cleared")
            Toast.makeText(this, "Conversation history cleared", Toast.LENGTH_SHORT).show()

        } catch (e: Exception) {
            Log.e(TAG, "❌ Failed to clear conversations", e)
        }
    }

    @SuppressLint("MissingInflatedId")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        try {
        setContentView(R.layout.activity_main)

        // Initialize RetrofitClient with context for configurable server URL
        RetrofitClient.initialize(this)
        Log.d(TAG, "Server URL configured: ${ServerConfig.getServerUrl(this)}")

        imagePreview = findViewById(R.id.imagePreview)
        uploadBtn = findViewById(R.id.uploadBtn)
        sendBtn = findViewById(R.id.sendBtn)
        messageInput = findViewById(R.id.messageInput)
        removeImageBtn = findViewById(R.id.removeImageBtn)
        uploadSection = findViewById(R.id.uploadSection)
        imageFileName = findViewById(R.id.imageFileName)
        // Profile button replaces status indicator
        val profileBtn = findViewById<ImageButton>(R.id.profileBtn)
        settingsBtn = findViewById(R.id.settingsBtn)
        
        // Set up profile button click listener
        profileBtn.setOnClickListener {
            showAgriculturalProfileDialog()
        }
        
        // Note: Create stub views for legacy MainActivity compatibility
        // Since MainActivityFSM.kt is now the primary activity, create minimal stubs
        fsmModeBtn = settingsBtn // Use settingsBtn as placeholder for fsmModeBtn
        
        // Create stub views for legacy chat interface (MainActivityFSM uses RecyclerView)
        responseTextView = TextView(this).apply { text = "Legacy MainActivity - Use MainActivityFSM for full functionality" }
        conversationScrollView = ScrollView(this) 
        conversationContainer = LinearLayout(this)
        
        // Update profile button state
        updateProfileButtonState()
        
        // Initialize conversation history if empty
        if (conversationHistory.length == 0) {
                val welcomeMessage =
                    "MAIN_ANSWER: Welcome to Sasya Chikitsa! I'm your AI plant health assistant. I can help diagnose plant diseases, provide care recommendations, and guide you through treatment procedures. Each app session starts fresh with a new conversation. Upload a photo or ask me about plant care to get started.\n\nACTION_ITEMS: Send Image | Give me watering schedule | Show fertilization procedure | Explain prevention methods"
            addAssistantMessage(welcomeMessage)
            
            // Add some test content to demonstrate action items
                val exampleMessage =
                    "MAIN_ANSWER: Here are some common plant problems I can help with:\n• Leaf spots and discoloration\n• Wilting and drooping\n• Pest infestations\n• Nutrient deficiencies\n• Growth issues\n\nACTION_ITEMS: Identify plant disease from photo | Create plant care schedule | Get soil testing recommendations | Show organic treatment options"
            addAssistantMessage(exampleMessage)
        }

        // FSM Mode Button - Launch intelligent assistant
        fsmModeBtn.setOnClickListener {
            launchFSMMode()
        }

        // Settings Button
        settingsBtn.setOnClickListener {
            showSettingsDialog()
        }

        // Upload Button
        uploadBtn.setOnClickListener {
            imagePickerLauncher.launch("image/*")
        }

        // Remove Image Button
        removeImageBtn.setOnClickListener {
            clearSelectedImage()
        }

        // Send Button
        sendBtn.setOnClickListener {
            try {
            val message = messageInput.text.toString().trim()
            val currentImageUri = selectedImageUri // Use the stored URI
            if (message.isEmpty() && currentImageUri == null) {
                        Toast.makeText(
                            this,
                            "Please enter a message or upload an image.",
                            Toast.LENGTH_SHORT
                        ).show()
                return@setOnClickListener
            }
            // Convert image to Base64 if an image is selected
            var imageBase64: String? = null
            if (currentImageUri != null) {
                try {
                    imageBase64 = uriToBase64(currentImageUri)
                } catch (e: IOException) {
                    Log.e(TAG, "Error converting image to Base64", e)
                            Toast.makeText(this, "Error processing image.", Toast.LENGTH_SHORT)
                                .show()
                    return@setOnClickListener
                }
            }

                    // Add user message to conversation history with image
            if (message.isNotEmpty()) {
                        addUserMessageWithImage(message, currentImageUri)
//                Toast.makeText(this, "Message sent: $message", Toast.LENGTH_SHORT).show()
            } else if (currentImageUri != null) {
                        addUserMessageWithImage("Image", currentImageUri)
//                Toast.makeText(this, "Image sent", Toast.LENGTH_SHORT).show()
            }

            // Clear the input field
            messageInput.text.clear()

            // Fetch the stream
            fetchChatStreamFromServer(message, imageBase64, sessionId)
            
                    // Clear the upload preview but keep image in conversation history
                if (currentImageUri != null) {
                    clearSelectedImage(showToast = false)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error in send button logic", e)
                    Toast.makeText(this, "Error sending message: ${e.message}", Toast.LENGTH_LONG)
                        .show()
                }
            }

            // Load saved conversations after all UI is initialized
            loadConversations()

            // Check if this is first time user and prompt for agricultural profile setup
            checkAndPromptAgriculturalProfile()

            Log.d(TAG, "✅ MainActivity initialization completed with conversation loading")

        } catch (e: Exception) {
            Log.e(TAG, "❌ Fatal error in MainActivity onCreate", e)
            Toast.makeText(this, "Error initializing app: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    // Helper method to show selected image
    private fun showSelectedImage(imageUri: Uri) {
        selectedImageUri = imageUri
            imagePreview.setImageURI(imageUri)
        imageFileName.text = "📷 Image attached"
        uploadSection.visibility = android.view.View.VISIBLE
        
        Log.d(TAG, "Image selected and upload section shown")
    }

    // Helper method to clear selected image
    private fun clearSelectedImage(showToast: Boolean = true) {
        selectedImageUri = null
        imagePreview.setImageURI(null)
        uploadSection.visibility = android.view.View.GONE
        
        if (showToast) {
            Toast.makeText(this, "Image removed", Toast.LENGTH_SHORT).show()
        }
        Log.d(TAG, "Image cleared and upload section hidden")
    }

    // Helper method to add user message to conversation
    private fun addUserMessage(message: String, hasImage: Boolean = false) {
        val imageIndicator = if (hasImage) " 📷" else ""
        val userMsg = "👤 $message$imageIndicator\n\n"
        
        Log.d(TAG, "Adding user message to history. Current length: ${conversationHistory.length}")
        conversationHistory.append(userMsg)
        Log.d(TAG, "After adding user message. New length: ${conversationHistory.length}")
        
        updateConversationDisplay()
    }

    // Enhanced helper method to add user message with image support
    private fun addUserMessageWithImage(message: String, imageUri: Uri?) {
        // Add to new conversation messages list
        val conversationMsg = ConversationMessage(
            text = message,
            isUser = true,
            imageUri = imageUri
        )
        conversationMessages.add(conversationMsg)

        // Also add to legacy text-based history for compatibility
        val imageIndicator = if (imageUri != null) " 📷" else ""
        val userMsg = "👤 $message$imageIndicator\n\n"
        conversationHistory.append(userMsg)

        Log.d(TAG, "Added user message with image. Total messages: ${conversationMessages.size}")
        updateConversationDisplay()

        // Save conversations after adding user message
        saveConversations()
    }

    // Helper method to add assistant message to conversation
    private fun addAssistantMessage(message: String) {
        // Check if this is a structured response
        val structuredResponse = parseStructuredResponse(message)
        
        if (structuredResponse != null) {
            // Handle structured response with separate main answer and action items
            addStructuredAssistantMessage(
                structuredResponse.mainAnswer,
                structuredResponse.actionItems
            )
        } else {
            // Handle regular unstructured response
            addAssistantMessageToConversation(message)
        }
    }

    // Enhanced helper method to add assistant message to new conversation structure
    private fun addAssistantMessageToConversation(message: String) {
            val formattedMessage = formatMessageWithCollapsibleJson(message)

        // Add to new conversation messages list
        val conversationMsg = ConversationMessage(
            text = formattedMessage,
            isUser = false,
            imageUri = null,
            attentionOverlayData = null // Regular messages don't have attention overlay
        )
        conversationMessages.add(conversationMsg)

        // Also add to legacy text-based history for compatibility
        val assistantMsg = "🤖 $formattedMessage\n\n"
            conversationHistory.append(assistantMsg)
            
        Log.d(TAG, "Added assistant message. Total messages: ${conversationMessages.size}")
            updateConversationDisplay()

        // Save conversations after adding assistant message
        saveConversations()

        // Ensure user can see the complete response
        scrollToResponseEnd()
    }

    // Helper method to create a user message view with optional image (aligned right, WhatsApp-style)
    private fun createUserMessageView(message: ConversationMessage): View {
        // Calculate width for proper zigzag chat layout (50% max width for better layout balance)
        val displayMetrics = resources.displayMetrics
        val screenWidth = displayMetrics.widthPixels
        val maxCardWidth = (screenWidth * 0.5).toInt() // Reduced to 50% for zigzag layout
        val minCardWidth = (screenWidth * 0.3).toInt()
        val rightMargin = 16
        val leftMargin = (screenWidth * 0.4).toInt() // More space on left to push right and balance layout

        val messageCard = androidx.cardview.widget.CardView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                maxCardWidth, // Set explicit max width instead of WRAP_CONTENT
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                setMargins(leftMargin, 12, rightMargin, 12) // More spacing between messages
                gravity = android.view.Gravity.END // Align to right
            }
            radius = 16f // Rounded corners
            cardElevation = 8f // Strong shadow for clear separation
            setCardBackgroundColor(
                ContextCompat.getColor(
                    this@MainActivity,
                    R.color.user_message_bg
                )
            )
        }

        val messageLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, 0, 0, 16) // No side padding for header, bottom padding for content
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, // Use full card width for proper text wrapping
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
        }

        // Add header with icon and "Human" label with colored background
        val headerLayout = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(12, 6, 12, 6) // Padding for colored background
            setBackgroundColor(ContextCompat.getColor(this@MainActivity, R.color.user_header_bg))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                setMargins(0, 0, 0, 8) // Space between header and content
            }
        }

        val headerText = TextView(this).apply {
            text = "👤 Human"
            textSize = 14f // Smaller header text
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.header_text_white))
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        headerLayout.addView(headerText)
        messageLayout.addView(headerLayout)

        // Add image if present (WhatsApp-style image sizing) - Show image first
        if (message.imageUri != null) {
            val imageView = ImageView(this).apply {
                val imageSize =
                    minOf(maxCardWidth - 32, 240) // Reduced max size for narrower cards, account for padding
                layoutParams = LinearLayout.LayoutParams(
                    imageSize,
                    imageSize
                ).apply {
                    setMargins(16, 8, 16, if (message.text.isNotEmpty()) 8 else 8) // Bottom margin only if text follows
                }
                scaleType = ImageView.ScaleType.CENTER_CROP
                setImageURI(message.imageUri)

                // WhatsApp-like rounded corner background
                background =
                    ContextCompat.getDrawable(this@MainActivity, R.drawable.modern_card_background)
                clipToOutline = true
            }
            messageLayout.addView(imageView)
        }

        // Add message text if not empty - Show text below image
        if (message.text.isNotEmpty()) {
            val textView = TextView(this).apply {
                text = message.text // Clean text without emoji (header has it)
                textSize = 16f // Standard message text size
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.user_text))
                setLineSpacing(4f, 1.1f) // WhatsApp-like line spacing
                typeface = android.graphics.Typeface.DEFAULT
                setPadding(16, if (message.imageUri != null) 8 else 8, 16, 8) // Top padding reduced if image above

                // Enable proper text wrapping
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, // Use full available width
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
                
                // Additional text wrapping settings
                setSingleLine(false) // Allow multi-line
                maxLines = Int.MAX_VALUE // No line limit
                ellipsize = null // No ellipsize to prevent truncation
            }
            messageLayout.addView(textView)
        }

        messageCard.addView(messageLayout)
        return messageCard
    }

    // Helper method to create an assistant message view (aligned left, WhatsApp-style)
    private fun createAssistantMessageView(message: ConversationMessage): View {
        // Calculate width for proper zigzag chat layout (60% max width to balance with user messages)
        val displayMetrics = resources.displayMetrics
        val screenWidth = displayMetrics.widthPixels
        val maxCardWidth = (screenWidth * 0.6).toInt() // Reduced for zigzag balance
        val leftMargin = 16
        val rightMargin = (screenWidth * 0.3).toInt() // More space on right to maintain zigzag layout

        val messageCard = androidx.cardview.widget.CardView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                maxCardWidth, // Set explicit max width for proper wrapping
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                setMargins(leftMargin, 12, rightMargin, 12) // More spacing between messages
                gravity = android.view.Gravity.START // Align to left
            }
            radius = 16f // Rounded corners
            cardElevation = 8f // Strong shadow for clear separation
            setCardBackgroundColor(
                ContextCompat.getColor(
                    this@MainActivity,
                    R.color.assistant_message_bg
                )
            )
        }

        val messageLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, 0, 0, 16) // No side padding for header, bottom padding for content
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, // Use full card width
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
        }

        // Check if this is a structured response with action items
        val structuredResponse = parseStructuredResponse(message.text)

        if (structuredResponse != null) {
            // Handle structured response with separate formatting for main answer and action items
            createStructuredAssistantView(messageLayout, structuredResponse)
        } else {
            // Handle regular response with bullet point formatting preserved
            if (message.text.contains("📋 Recommended Actions:")) {
                createStreamingActionItemsView(messageLayout, message.text)
            } else {
                // Add header with icon and "Sasya Chikitsa" label with colored background
                val headerLayout = LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL
                    setPadding(12, 6, 12, 6) // Padding for colored background
                    setBackgroundColor(
                        ContextCompat.getColor(
                            this@MainActivity,
                            R.color.assistant_header_bg
                        )
                    )
                    layoutParams = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                    ).apply {
                        setMargins(0, 0, 0, 8) // Space between header and content
                    }
                }

                val headerText = TextView(this).apply {
                    text = "🤖 Sasya Chikitsa"
                    textSize = 14f // Smaller header text
                    setTextColor(
                        ContextCompat.getColor(
                            this@MainActivity,
                            R.color.header_text_white
                        )
                    )
                    setTypeface(typeface, android.graphics.Typeface.BOLD)
                }
                headerLayout.addView(headerText)
                messageLayout.addView(headerLayout)

                val textView = TextView(this).apply {
                    // Clean text without emoji prefix (header has it)
                    val displayText = message.text.removePrefix("🤖 ").trim()
                    text = displayText
                    textSize = 16f // Consistent with user messages
                    setTextColor(ContextCompat.getColor(this@MainActivity, R.color.assistant_text))
                    setLineSpacing(4f, 1.1f) // WhatsApp-like line spacing
                    movementMethod = LinkMovementMethod.getInstance()
                    setPadding(16, 8, 16, 8) // Padding for text content

                    // Enable proper text wrapping
                    layoutParams = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT, // Use full available width
                        LinearLayout.LayoutParams.WRAP_CONTENT
                    )
                    
                    // Additional text wrapping settings
                    setSingleLine(false) // Allow multi-line
                    maxLines = Int.MAX_VALUE // No line limit
                    ellipsize = null // No ellipsize to prevent truncation
                }
                messageLayout.addView(textView)
            }
        }

        // Add feedback buttons for all assistant messages
        val feedbackContainer = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(16, 8, 16, 16)
            gravity = android.view.Gravity.START
        }
        
        val thumbsUpButton = android.widget.ImageButton(this).apply {
            layoutParams = LinearLayout.LayoutParams(96, 96).apply { 
                setMargins(0, 0, 24, 0) 
            }
            setImageDrawable(ContextCompat.getDrawable(this@MainActivity, R.drawable.ic_thumb_up))
            background = ContextCompat.getDrawable(this@MainActivity, android.R.drawable.ic_input_add)
            scaleType = android.widget.ImageView.ScaleType.CENTER_INSIDE
            setPadding(18, 18, 18, 18)
            contentDescription = "Thumbs up"
            
            setOnClickListener {
                // Visual feedback - highlight the clicked button
                setColorFilter(ContextCompat.getColor(this@MainActivity, R.color.thumbs_up_selected))
                
                // Handle thumbs up feedback
                handleThumbsUpFeedback(message)
            }
        }
        
        val thumbsDownButton = android.widget.ImageButton(this).apply {
            layoutParams = LinearLayout.LayoutParams(96, 96)
            setImageDrawable(ContextCompat.getDrawable(this@MainActivity, R.drawable.ic_thumb_down))
            background = ContextCompat.getDrawable(this@MainActivity, android.R.drawable.ic_delete)
            scaleType = android.widget.ImageView.ScaleType.CENTER_INSIDE
            setPadding(18, 18, 18, 18)
            contentDescription = "Thumbs down"
            
            setOnClickListener {
                // Visual feedback - highlight the clicked button  
                setColorFilter(ContextCompat.getColor(this@MainActivity, R.color.thumbs_down_selected))
                
                // Handle thumbs down feedback
                handleThumbsDownFeedback(message)
            }
        }
        
        feedbackContainer.addView(thumbsUpButton)
        feedbackContainer.addView(thumbsDownButton)
        messageLayout.addView(feedbackContainer)

        messageCard.addView(messageLayout)
        return messageCard
    }

    // Helper method to create structured assistant view with clickable action items (WhatsApp-style)
    private fun createStructuredAssistantView(
        messageLayout: LinearLayout,
        structuredResponse: StructuredResponse
    ) {
        // Add header with icon and "Sasya Chikitsa" label with colored background
        val headerLayout = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(12, 6, 12, 6) // Padding for colored background
            setBackgroundColor(
                ContextCompat.getColor(
                    this@MainActivity,
                    R.color.assistant_header_bg
                )
            )
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                setMargins(0, 0, 0, 8) // Space between header and content
            }
        }

        val headerText = TextView(this).apply {
            text = "🤖 Sasya Chikitsa"
            textSize = 14f // Smaller header text
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.header_text_white))
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        headerLayout.addView(headerText)
        messageLayout.addView(headerLayout)

        // Main answer text with WhatsApp styling
        val mainAnswerText = TextView(this).apply {
            text = structuredResponse.mainAnswer // Clean text (header has icon)
            textSize = 16f // Consistent with user messages
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.assistant_text))
            setLineSpacing(4f, 1.1f) // WhatsApp-like line spacing
            setPadding(16, 8, 16, 8) // Padding for text content
        }
        messageLayout.addView(mainAnswerText)

        // Action items section if they exist
        if (structuredResponse.actionItems.isNotEmpty()) {
            // Add spacing between main answer and actions
            val spacing = LinearLayout(this).apply {
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    12
                ) // 12dp spacing like WhatsApp
            }
            messageLayout.addView(spacing)

            // Action items header with better styling
            val actionHeader = TextView(this).apply {
                text = "📋 Quick Actions:"
                textSize = 15f // Slightly smaller for section headers
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.assistant_text))
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                setPadding(0, 4, 0, 8) // WhatsApp-like spacing
            }
            messageLayout.addView(actionHeader)

            // Create clickable action items with WhatsApp-like styling
            structuredResponse.actionItems.forEach { actionItem ->
                val actionTextView = TextView(this).apply {
                    val actionText = "• $actionItem"
                    val spannableString = SpannableString(actionText)

                    // Make the entire action item clickable
                    val clickableSpan = object : ClickableSpan() {
                        override fun onClick(view: View) {
                            messageInput.setText(actionItem.trim())
                            conversationScrollView.post {
                                conversationScrollView.fullScroll(ScrollView.FOCUS_DOWN)
                            }
                            Toast.makeText(
                                this@MainActivity,
                                "Action added to input",
                                Toast.LENGTH_SHORT
                            ).show()
                        }
                    }

                    // Apply styling to make it look clickable
                    spannableString.setSpan(
                        clickableSpan,
                        0,
                        actionText.length,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )
                    spannableString.setSpan(
                        ForegroundColorSpan(
                            ContextCompat.getColor(
                                this@MainActivity,
                                R.color.action_item_color
                            )
                        ),
                        0, actionText.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )
                    spannableString.setSpan(
                        UnderlineSpan(),
                        0,
                        actionText.length,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )
                    spannableString.setSpan(
                        StyleSpan(android.graphics.Typeface.BOLD),
                        0,
                        actionText.length,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )

                    text = spannableString
                    textSize = 15f // WhatsApp-like action item size
                    setLineSpacing(3f, 1.1f) // WhatsApp-like line spacing
                    movementMethod = LinkMovementMethod.getInstance()
                    setPadding(12, 6, 0, 6) // WhatsApp-like padding
                }
                messageLayout.addView(actionTextView)
            }
        }
    }

    // Helper method to create streaming action items view (with checkmarks ✓)
    private fun createStreamingActionItemsView(messageLayout: LinearLayout, messageText: String) {
        // Add header with icon and "Sasya Chikitsa" label with colored background
        val headerLayout = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(12, 6, 12, 6) // Padding for colored background
            setBackgroundColor(
                ContextCompat.getColor(
                    this@MainActivity,
                    R.color.assistant_header_bg
                )
            )
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                setMargins(0, 0, 0, 8) // Space between header and content
            }
        }

        val headerText = TextView(this).apply {
            text = "🤖 Sasya Chikitsa"
            textSize = 14f // Smaller header text
            setTextColor(ContextCompat.getColor(this@MainActivity, R.color.header_text_white))
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        headerLayout.addView(headerText)
        messageLayout.addView(headerLayout)
        val lines = messageText.split("\n")
        var inActionSection = false
        val regularContent = mutableListOf<String>()
        val actionItems = mutableListOf<String>()

        // Parse the message to separate regular content from action items
        for (line in lines) {
            when {
                line.contains("📋 Recommended Actions:") -> {
                    inActionSection = true
                }

                inActionSection && line.trim().startsWith("✓") -> {
                    // Extract action item (remove the checkmark and whitespace)
                    val actionText = line.trim().removePrefix("✓").trim()
                    if (actionText.isNotEmpty()) {
                        actionItems.add(actionText)
                    }
                }

                !inActionSection && line.trim().isNotEmpty() -> {
                    regularContent.add(line)
                }
            }
        }

        // Display regular content (bullet points)
        if (regularContent.isNotEmpty()) {
            val regularText = TextView(this).apply {
                // Clean content without emoji prefix (header has it)
                val cleanContent = regularContent.joinToString("\n").removePrefix("🤖 ").trim()
                text = cleanContent
                textSize = 16f // Consistent with other messages
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.assistant_text))
                setLineSpacing(4f, 1.1f) // WhatsApp-like line spacing
                setPadding(16, 8, 16, 8) // Padding for text content
            }
            messageLayout.addView(regularText)
        }

        // Display action items section if they exist
        if (actionItems.isNotEmpty()) {
            // Add WhatsApp-like spacing between content and actions
            val spacing = LinearLayout(this).apply {
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    12
                ) // 12dp spacing like WhatsApp
            }
            messageLayout.addView(spacing)

            // Action items header with WhatsApp-like styling  
            val actionHeader = TextView(this).apply {
                text = "📋 Recommended Actions:"
                textSize = 15f // Slightly smaller for section headers like WhatsApp
                setTextColor(ContextCompat.getColor(this@MainActivity, R.color.assistant_text))
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                setPadding(0, 4, 0, 8) // WhatsApp-like spacing
            }
            messageLayout.addView(actionHeader)

            // Create clickable action items with checkmarks
            actionItems.forEach { actionItem ->
                val actionTextView = TextView(this).apply {
                    val actionText = "  ✓ $actionItem"
                    val spannableString = SpannableString(actionText)

                    // Make the action item clickable (skip the checkmark part)
                    val clickableSpan = object : ClickableSpan() {
                        override fun onClick(view: View) {
                            messageInput.setText(actionItem.trim())
                            conversationScrollView.post {
                                conversationScrollView.fullScroll(ScrollView.FOCUS_DOWN)
                            }
                            Toast.makeText(
                                this@MainActivity,
                                "Action added to input",
                                Toast.LENGTH_SHORT
                            ).show()
                        }
                    }

                    // Apply styling to make it look clickable
                    spannableString.setSpan(
                        clickableSpan,
                        0,
                        actionText.length,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )
                    spannableString.setSpan(
                        ForegroundColorSpan(
                            ContextCompat.getColor(
                                this@MainActivity,
                                R.color.action_item_color
                            )
                        ),
                        0, actionText.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )
                    spannableString.setSpan(
                        UnderlineSpan(),
                        0,
                        actionText.length,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )
                    spannableString.setSpan(
                        StyleSpan(android.graphics.Typeface.BOLD),
                        0,
                        actionText.length,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )

                    text = spannableString
                    textSize = 15f // WhatsApp-like action item size
                    setLineSpacing(3f, 1.1f) // WhatsApp-like line spacing
                    movementMethod = LinkMovementMethod.getInstance()
                    setPadding(12, 6, 0, 6) // WhatsApp-like padding
                }
                messageLayout.addView(actionTextView)
            }
        }
    }

    // Data class to hold parsed structured response
    data class StructuredResponse(
        val mainAnswer: String,
        val actionItems: List<String>
    )

    // Helper method to parse structured response format
    private fun parseStructuredResponse(message: String): StructuredResponse? {
        Log.d(TAG, "Parsing response for structure: $message")
        
        try {
            // Look for MAIN_ANSWER section
            val mainAnswerRegex = Regex(
                "MAIN_ANSWER:\\s*(.*?)(?=ACTION_ITEMS:|$)",
                setOf(RegexOption.DOT_MATCHES_ALL, RegexOption.IGNORE_CASE)
            )
            val mainAnswerMatch = mainAnswerRegex.find(message)
            
            // Look for ACTION_ITEMS section
            val actionItemsRegex = Regex(
                "ACTION_ITEMS:\\s*(.*?)$",
                setOf(RegexOption.DOT_MATCHES_ALL, RegexOption.IGNORE_CASE)
            )
            val actionItemsMatch = actionItemsRegex.find(message)
            
            if (mainAnswerMatch != null && actionItemsMatch != null) {
                val mainAnswer = mainAnswerMatch.groupValues[1].trim()
                val actionItemsText = actionItemsMatch.groupValues[1].trim()
                val actionItemsList =
                    actionItemsText.split("|").map { it.trim() }.filter { it.isNotEmpty() }
                
                Log.d(
                    TAG,
                    "Structured response found - Main: '${mainAnswer.take(50)}...', Actions: $actionItemsList"
                )
                return StructuredResponse(mainAnswer, actionItemsList)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing structured response", e)
        }
        
        Log.d(TAG, "No structured format found in response")
        return null
    }

    // Helper method to add structured assistant message with separate action items
    private fun addStructuredAssistantMessage(mainAnswer: String, actionItems: List<String>) {
        // Format main answer
        val formattedMainAnswer = formatMessageWithCollapsibleJson(mainAnswer)
        var assistantMsg = "🤖 $formattedMainAnswer"
        
        // Add action items as clickable elements if they exist
        if (actionItems.isNotEmpty()) {
            assistantMsg += "\n\n📋 Quick Actions:"
            actionItems.forEach { actionItem ->
                assistantMsg += "\n• $actionItem"
            }
        }
        
        assistantMsg += "\n\n"
        
        Log.d(
            TAG,
            "Adding structured assistant message to history. Current length: ${conversationHistory.length}"
        )
        
        // Create a SpannableString for the new message and apply action item spans immediately
        val spannableMessage = SpannableString(assistantMsg)
        applyActionItemSpansToText(spannableMessage, actionItems)
        
        // Add to new conversation messages list (convert SpannableString to String)
        val conversationMsg = ConversationMessage(
            text = spannableMessage.toString(),
            isUser = false,
            imageUri = null,
            attentionOverlayData = null // Regular structured messages don't have attention overlay
        )
        conversationMessages.add(conversationMsg)

        // Append to legacy conversation history
        conversationHistory.append(spannableMessage)
        Log.d(
            TAG,
            "After adding structured assistant message. New length: ${conversationHistory.length}"
        )
        
        updateConversationDisplay()

        // Save conversations after adding structured assistant message
        saveConversations()

        // Ensure user can see the complete response including action items
        scrollToResponseEnd()
    }

    // Helper method to apply action item spans to a specific text
    private fun applyActionItemSpansToText(
        spannableText: SpannableString,
        actionItems: List<String>
    ) {
        if (actionItems.isEmpty()) return
        
        val text = spannableText.toString()
        val quickActionsIndex = text.indexOf("📋 Quick Actions:")
        
        if (quickActionsIndex != -1) {
            actionItems.forEach { actionItem ->
                val bulletItemText = "• $actionItem"
                val itemIndex = text.indexOf(bulletItemText, quickActionsIndex)
                
                if (itemIndex != -1) {
                    val itemEndIndex = itemIndex + bulletItemText.length
                    
                    // Create clickable span for this specific action item
                    val clickableSpan = object : ClickableSpan() {
                        override fun onClick(view: View) {
                            messageInput.setText(actionItem.trim())
                            conversationScrollView.post {
                                conversationScrollView.fullScroll(ScrollView.FOCUS_DOWN)
                            }
                            Toast.makeText(
                                this@MainActivity,
                                "Action added to input",
                                Toast.LENGTH_SHORT
                            ).show()
                        }
                    }
                    
                    // Apply styling spans
                    spannableText.setSpan(
                        clickableSpan,
                        itemIndex,
                        itemEndIndex,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )
                    spannableText.setSpan(
                        ForegroundColorSpan(
                            ContextCompat.getColor(
                                this,
                                android.R.color.holo_blue_dark
                            )
                        ),
                        itemIndex, itemEndIndex, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )
                    spannableText.setSpan(
                        UnderlineSpan(),
                        itemIndex,
                        itemEndIndex,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )
                    spannableText.setSpan(
                        StyleSpan(Typeface.BOLD),
                        itemIndex,
                        itemEndIndex,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                    )
                }
            }
        }
    }

    // Helper method to format messages with collapsible JSON and highlighted questions
    private fun formatMessageWithCollapsibleJson(message: String): String {
        // Detect JSON blocks in the message
        val jsonRegex = Regex("\\{[^{}]*(?:\\{[^{}]*\\}[^{}]*)*\\}", RegexOption.DOT_MATCHES_ALL)
        val arrayRegex =
            Regex("\\[[^\\[\\]]*(?:\\[[^\\[\\]]*\\][^\\[\\]]*)*\\]", RegexOption.DOT_MATCHES_ALL)
        
        var formattedMessage = message
        
        // Find and replace JSON objects
        jsonRegex.findAll(message).forEach { match ->
            val jsonString = match.value
            if (isValidJson(jsonString)) {
                val collapsibleJson = createCollapsibleJsonText(jsonString, "JSON Data")
                formattedMessage = formattedMessage.replace(jsonString, collapsibleJson)
            }
        }
        
        // Find and replace JSON arrays
        arrayRegex.findAll(formattedMessage).forEach { match ->
            val jsonString = match.value
            if (isValidJson(jsonString)) {
                val collapsibleJson = createCollapsibleJsonText(jsonString, "JSON Array")
                formattedMessage = formattedMessage.replace(jsonString, collapsibleJson)
            }
        }
        
        return formattedMessage
    }


    // Helper method to check if string is valid JSON
    private fun isValidJson(jsonString: String): Boolean {
        return try {
            when {
                jsonString.trim().startsWith("{") -> {
                    JSONObject(jsonString)
                    true
                }

                jsonString.trim().startsWith("[") -> {
                    JSONArray(jsonString)
                    true
                }

                else -> false
            }
        } catch (e: JSONException) {
            false
        }
    }

    // Helper method to create collapsible JSON text
    private fun createCollapsibleJsonText(jsonString: String, label: String): String {
        return "\n▼ $label (tap to expand)\n[COLLAPSED_JSON:$jsonString]\n"
    }

    // Helper method to handle JSON collapsibles (action items are now handled immediately when added)
    private fun makeJsonCollapsiblesClickable() {
        val text = responseTextView.text.toString()
        
        val spannableString = SpannableString(text)
        var foundInteractiveElements = false
        
        // Handle collapsible JSON blocks
        val collapsedJsonRegex =
            Regex("▼ ([^\\n]+) \\(tap to expand\\)\\n\\[COLLAPSED_JSON:([^\\]]+)\\]")
        collapsedJsonRegex.findAll(text).forEach { match ->
            foundInteractiveElements = true
            val fullMatch = match.value
            val label = match.groupValues[1]
            val jsonContent = match.groupValues[2]
            
            val clickableSpan = object : ClickableSpan() {
                override fun onClick(view: View) {
                    // Replace collapsed section with expanded JSON
                    val currentText = responseTextView.text.toString()
                    val prettyJson = try {
                        if (jsonContent.trim().startsWith("{")) {
                            JSONObject(jsonContent).toString(2)
                        } else {
                            JSONArray(jsonContent).toString(2)
                        }
                    } catch (e: JSONException) {
                        jsonContent
                    }
                    
                    val expandedText = "▲ $label (tap to collapse)\n```json\n$prettyJson\n```"
                    val updatedText = currentText.replace(fullMatch, expandedText)
                    
                    // Update both conversation history and display
                    conversationHistory.clear()
                    conversationHistory.append(updatedText)
                    responseTextView.text = updatedText
                    
                    // Re-apply clickable spans for collapse functionality
                    makeExpandedJsonCollapsible()
                    
                    Toast.makeText(this@MainActivity, "JSON expanded", Toast.LENGTH_SHORT).show()
                }
            }
            
            val labelStart = text.indexOf("▼ $label")
            val labelEnd = labelStart + "▼ $label (tap to expand)".length
            
            spannableString.setSpan(
                clickableSpan, 
                labelStart, 
                labelEnd, 
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            )
            
            // Make the label blue and underlined to indicate it's clickable
            spannableString.setSpan(
                ForegroundColorSpan(ContextCompat.getColor(this, android.R.color.holo_blue_dark)),
                labelStart,
                labelEnd,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            )
            
            spannableString.setSpan(
                UnderlineSpan(),
                labelStart,
                labelEnd,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            )
            
            spannableString.setSpan(
                StyleSpan(Typeface.BOLD),
                labelStart,
                labelEnd,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            )
        }
        
        if (foundInteractiveElements) {
            responseTextView.text = spannableString
            responseTextView.movementMethod = LinkMovementMethod.getInstance()
        }
    }

    // Helper method to make expanded JSON collapsible
    private fun makeExpandedJsonCollapsible() {
        val text = responseTextView.text.toString()
        val expandedJsonRegex =
            Regex("▲ ([^\\n]+) \\(tap to collapse\\)\\n```json\\n([\\s\\S]*?)\\n```")
        
        expandedJsonRegex.findAll(text).forEach { match ->
            val fullMatch = match.value
            val label = match.groupValues[1]
            val jsonContent = match.groupValues[2]
            
            val spannableString = SpannableString(text)
            val clickableSpan = object : ClickableSpan() {
                override fun onClick(view: View) {
                    // Replace expanded section with collapsed JSON
                    val currentText = responseTextView.text.toString()
                    val collapsedText = "▼ $label (tap to expand)\n[COLLAPSED_JSON:${
                        jsonContent.replace(
                            "\\s+".toRegex(),
                            " "
                        ).trim()
                    }]"
                    val updatedText = currentText.replace(fullMatch, collapsedText)
                    
                    // Update both conversation history and display
                    conversationHistory.clear()
                    conversationHistory.append(updatedText)
                    responseTextView.text = updatedText
                    
                    // Re-apply clickable spans for JSON
                    makeJsonCollapsiblesClickable()
                    
                    Toast.makeText(this@MainActivity, "JSON collapsed", Toast.LENGTH_SHORT).show()
                }
            }
            
            val labelStart = text.indexOf("▲ $label")
            val labelEnd = labelStart + "▲ $label (tap to collapse)".length
            
            spannableString.setSpan(
                clickableSpan, 
                labelStart, 
                labelEnd, 
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            )
            
            // Make the label blue and underlined to indicate it's clickable
            spannableString.setSpan(
                ForegroundColorSpan(ContextCompat.getColor(this, android.R.color.holo_blue_dark)),
                labelStart,
                labelEnd,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            )
            
            spannableString.setSpan(
                UnderlineSpan(),
                labelStart,
                labelEnd,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            )
            
            spannableString.setSpan(
                StyleSpan(Typeface.BOLD),
                labelStart,
                labelEnd,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            )
            
            responseTextView.text = spannableString
            responseTextView.movementMethod = LinkMovementMethod.getInstance()
        }
    }

    /**
     * Smooth scrolling method to show new content
     * Only scrolls when actual content is added, not during thinking/waiting phases
     */
    private fun scrollToResponseEnd() {
        runOnUiThread {
            // Simple, clean scroll approach - only when content is actually present
            conversationScrollView.post {
                conversationScrollView.smoothScrollTo(0, conversationScrollView.getChildAt(0).height)
            }
        }
    }

    // Helper method to update conversation display and scroll to bottom
    private fun updateConversationDisplay() {
        runOnUiThread {
            Log.d(TAG, "Updating conversation display. Messages: ${conversationMessages.size}")

            // Clear existing conversation views (except welcome message)
            if (conversationContainer.childCount > 1) {
                conversationContainer.removeViews(1, conversationContainer.childCount - 1)
            }

            // Add each conversation message as a separate view
            for (message in conversationMessages) {
                val messageView = if (message.isUser) {
                    createUserMessageView(message)
                } else {
                    createAssistantMessageView(message)
                }
                conversationContainer.addView(messageView)
                
                // If this is the last user message and we're thinking, add thinking indicator
                if (message.isUser && message == conversationMessages.lastOrNull() && isThinking) {
                    addThinkingIndicatorToContainer()
                }
            }

            // Only update legacy TextView if NOT currently streaming to avoid wiping streaming content
            if (!isCurrentlyStreaming) {
            responseTextView.text = conversationHistory
            responseTextView.movementMethod = LinkMovementMethod.getInstance()
                Log.d(TAG, "Updated legacy TextView (not streaming)")
            } else {
                Log.d(TAG, "Skipping TextView update - streaming in progress")
            }
            
            Log.d(TAG, "Display updated. Message views: ${conversationMessages.size}")
            
            // Force layout update
            responseTextView.requestLayout()
            
            // Enhanced scroll to bottom - ensure user sees complete response
            scrollToResponseEnd()
        }
    }

    // Variables for animated thinking indicator
    private var thinkingAnimation: Runnable? = null
    private var isThinking = false
    private var thinkingIndicatorView: View? = null

    // Helper method to show animated thinking indicator with animated dots
    private fun showAnimatedThinkingIndicator() {
        runOnUiThread {
            Log.d(TAG, "🤔 Starting animated thinking indicator")

            // Mark that we're thinking
            isThinking = true
            
            // Add thinking indicator to conversation container after the latest user message
            addThinkingIndicatorToContainer()

            // Start dot animation
            startThinkingDotAnimation()

            // DO NOT scroll during thinking - keep current scroll position stable
            // Scrolling will happen once actual response content is received
        }
    }

    private fun addThinkingIndicatorToContainer() {
        // Remove existing thinking indicator if any
        removeThinkingIndicatorFromContainer()
        
        // Create thinking indicator view
        thinkingIndicatorView = createThinkingIndicatorView()
        conversationContainer.addView(thinkingIndicatorView)
        
        Log.d(TAG, "✅ Thinking indicator added to conversation container")
    }

    private fun createThinkingIndicatorView(): View {
        return TextView(this).apply {
            text = "🤖 Sasya Chikitsa AI Agent Thinking"
            textSize = 14f
            setTextColor(getColor(R.color.assistant_text))
            setPadding(16, 8, 16, 8)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                setMargins(16, 4, 16, 4) // Simple margins
            }
            alpha = 0.7f // Slightly transparent to make it more subtle
            setTypeface(typeface, android.graphics.Typeface.ITALIC) // Make text italic
            id = View.generateViewId() // For animation updates
        }
    }

    private fun removeThinkingIndicatorFromContainer() {
        thinkingIndicatorView?.let { view ->
            conversationContainer.removeView(view)
            thinkingIndicatorView = null
            Log.d(TAG, "✅ Thinking indicator removed from conversation container")
        }
    }

    private fun startThinkingDotAnimation() {
        var dotCount = 0

        thinkingAnimation = object : Runnable {
            override fun run() {
                // Stop if we're no longer thinking or streaming has started
                if (!isThinking || isCurrentlyStreaming) {
                    Log.d(
                        TAG,
                        "🛑 Stopping thinking animation - streaming started: $isCurrentlyStreaming"
                    )
                    return
                }

                runOnUiThread {
                    // Create animated dots (1-4 dots cycling) - define outside loop scope
                    val dots = ".".repeat((dotCount % 4) + 1)
                    
                    val currentText = responseTextView.text.toString()
                    val lines = currentText.split("\n").toMutableList()

                    // Find and update the thinking line
                    for (i in lines.indices.reversed()) {
                        if (lines[i].contains("Sasya Chikitsa AI Agent Thinking")) {
                            lines[i] = "🤖 Sasya Chikitsa AI Agent Thinking$dots"
                            break
                        }
                    }

                    // Update the thinking indicator view text with dots
                    thinkingIndicatorView?.let { view ->
                        val textView = view as? TextView
                        textView?.text = "🤖 Sasya Chikitsa AI Agent Thinking$dots"
                    }
                    
                    // NO scrolling during thinking animation - keep position stable

                    dotCount++

                    // Continue animation every 500ms
                    if (::responseTextView.isInitialized) {
                        responseTextView.postDelayed(this, 500)
                    }
                }
            }
        }

        // Start the animation
        responseTextView.postDelayed(thinkingAnimation!!, 500)
    }

    private fun stopThinkingIndicator() {
        runOnUiThread {
            Log.d(TAG, "🛑 Stopping thinking indicator")

            isThinking = false

            // Cancel any pending animation
            thinkingAnimation?.let { 
                if (::responseTextView.isInitialized) {
                    responseTextView.removeCallbacks(it)
                }
            }

            // Remove thinking indicator from conversation container
            removeThinkingIndicatorFromContainer()
            
            Log.d(TAG, "✅ Thinking indicator stopped and removed from container")
        }
    }

    // Helper method to show engaging progress indicator - keeps users engaged during AI processing
    private fun showTypingIndicator() {
        runOnUiThread {
            Log.d(TAG, "🎯 Starting engaging progress indicator for plant analysis")

            // Remove any existing indicator first
            val currentText = responseTextView.text.toString()
            if (currentText.contains("🤖 typing")) {
                val lines = currentText.split("\n").toMutableList()
                // Remove typing lines
                lines.removeAll { it.contains("typing") || it.contains("⚡") || it.contains("🧠") }
                responseTextView.text = lines.joinToString("\n")
            }

            // Add engaging plant analysis header
            responseTextView.append("🤖 Sasya Chikitsa AI Analyzing...\n")
            responseTextView.append("🌱 Examining your plant health\n")
            responseTextView.append("🔍 Running disease detection algorithms\n")

            // Start animated progress dots
            startProgressAnimation()

            // DO NOT scroll during progress animation - keep position stable
        }
    }

    private fun startProgressAnimation() {
        // Create animated progress indicator to keep users engaged
        val progressRunnable = object : Runnable {
            private var dotCount = 0
            private var progressStep = 0

            override fun run() {
                // Stop animation if streaming has started
                if (isCurrentlyStreaming) {
                    Log.d(TAG, "🛑 Stopping progress animation - streaming started")
                    return
                }

                runOnUiThread {
                    val currentText = responseTextView.text.toString()

                    // Remove previous progress line if exists
                    val lines = currentText.split("\n").toMutableList()
                    if (lines.isNotEmpty() && (lines.last().startsWith("⚡") || lines.last()
                            .startsWith("🧠") || lines.last().startsWith("🔬"))
                    ) {
                        lines.removeAt(lines.size - 1)
                        if (lines.isNotEmpty() && lines.last().isEmpty()) {
                            lines.removeAt(lines.size - 1)
                        }
                    }

                    // Create animated progress with agricultural context
                    val dots = ".".repeat((dotCount % 4) + 1)
                    val progressTexts = arrayOf(
                        "⚡ Preprocessing plant image$dots",
                        "🧠 CNN neural network analyzing$dots",
                        "🔬 Detecting disease symptoms$dots",
                        "📊 Calculating confidence levels$dots",
                        "💊 Preparing treatment recommendations$dots",
                        "🌱 Finalizing plant diagnosis$dots"
                    )

                    val progressText = progressTexts[progressStep % progressTexts.size]
                    lines.add(progressText)

                    responseTextView.text = lines.joinToString("\n") + "\n"
                    // NO scrolling during progress animation - keep position stable

                    dotCount++
                    if (dotCount % 4 == 0) {
                        progressStep++
                    }

                    // Continue animation every 400ms for smooth progress feel
                    responseTextView.postDelayed(this, 400)
                }
            }
        }

        // Start the animation after a small delay
        responseTextView.postDelayed(progressRunnable, 200)
    }

    // Helper method to remove typing indicator - restores from conversationHistory
    private fun removeTypingIndicator() {
        runOnUiThread {
            Log.d(TAG, "🧹 Removing all typing/progress/thinking indicators")

            // Stop any thinking animation
            stopThinkingIndicator()

            // Remove any typing-related text including all indicators
            val currentText = responseTextView.text.toString()
            val lines = currentText.split("\n").toMutableList()

            // Remove typing, progress, thinking, and analysis indicators
            lines.removeAll { line ->
                line.contains("Typing...") ||
                        line.contains("typing") ||
                        line.contains("Thinking") ||
                        line.contains("⚡") ||
                        line.contains("🧠") ||
                        line.contains("🔬") ||
                        line.contains("📊") ||
                        line.contains("💊") ||
                        line.contains("🌱") ||
                        line.contains("Analyzing...") ||
                        line.contains("Examining") ||
                        line.contains("Sasya Chikitsa AI Agent Typing") ||
                        line.contains("Sasya Chikitsa AI Agent Thinking")
            }

            // Restore clean text
            responseTextView.text = lines.joinToString("\n")

            Log.d(TAG, "✅ All typing/progress/thinking indicators removed. Clean text restored.")
        }
    }

    // Variables for streaming response handling
    private val streamingChunks = mutableListOf<String>()
    private var isCurrentlyStreaming = false
    
    // Generate unique session ID for this app instance
    private val sessionId: String = UUID.randomUUID().toString().also { 
        Log.i(TAG, "🆔 New session created: $it") 
    }

    /**
     * Create ImageView for attention overlay visualization from base64 data
     */
    private fun createAttentionOverlayImageView(base64Data: String): ImageView? {
        return try {
            Log.i(TAG, "🎨 Creating attention overlay ImageView")

            // Decode base64 to bitmap
            val imageBytes = Base64.decode(base64Data, Base64.DEFAULT)
            val bitmap =
                android.graphics.BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)

            if (bitmap != null) {
                // Create ImageView with proper styling
                val imageView = ImageView(this)
                imageView.setImageBitmap(bitmap)
                imageView.scaleType = ImageView.ScaleType.FIT_CENTER
                imageView.adjustViewBounds = true

                // Set layout parameters for the image
                val layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
                layoutParams.setMargins(16, 16, 16, 16) // Add margins
                imageView.layoutParams = layoutParams

                // Add styling - rounded corners, elevation
                imageView.setPadding(8, 8, 8, 8)
                imageView.background =
                    ContextCompat.getDrawable(this, R.drawable.modern_card_background)

                Log.i(TAG, "   ✅ Attention overlay ImageView created successfully")
                Log.i(TAG, "   📏 Image dimensions: ${bitmap.width} x ${bitmap.height}")

                imageView
            } else {
                Log.e(TAG, "   ❌ Failed to decode bitmap from base64 data")
                null
            }
        } catch (e: Exception) {
            Log.e(TAG, "   ❌ Exception creating attention overlay ImageView: ${e.message}")
            null
        }
    }

    /**
     * Add a streaming chunk immediately to the UI while preserving conversation history
     */
    private fun addStreamingChunk(chunk: String) {
        runOnUiThread {
            try {
                // SAFETY: Check if UI components are still valid
                if (!::responseTextView.isInitialized) {
                    Log.e(TAG, "❌ responseTextView not initialized, skipping chunk")
                    return@runOnUiThread
                }

                val currentTime = System.currentTimeMillis()

                // 📊 ENHANCED LOGGING - Track streaming chunks with precise timing
                Log.i(TAG, "🔥 STREAMING CHUNK RECEIVED FOR DISPLAY:")
            Log.i(TAG, "   📦 Chunk content: '$chunk'")
            Log.i(TAG, "   📊 Chunk length: ${chunk.length} characters")
                Log.i(TAG, "   ⏰ Display timestamp: $currentTime")
            Log.i(TAG, "   🔄 Currently streaming: $isCurrentlyStreaming")
            Log.i(TAG, "   📈 Total chunks so far: ${streamingChunks.size}")
                Log.i(TAG, "   🎯 About to display this chunk individually")
            
            if (!isCurrentlyStreaming) {
                    // Starting new streaming - clear any thinking/typing indicators
                Log.i(TAG, "🚀 STARTING NEW STREAMING SESSION")
                    try {
                        stopThinkingIndicator() // Stop animated thinking dots and remove from container
                        removeTypingIndicator() // Remove any other typing indicators
                streamingChunks.clear()
                        currentAttentionOverlayData = null // Clear previous attention data
                isCurrentlyStreaming = true
                
                // Add assistant header for the streaming response
                responseTextView.append("🤖 Plant Analysis Progress:\n")
                Log.i(TAG, "   ✅ Added assistant header with progress indicator")
                    } catch (e: Exception) {
                        Log.e(TAG, "❌ Error initializing streaming session: ${e.message}", e)
                        return@runOnUiThread
                    }
            }
            
            // Add the chunk to the display and track it
            streamingChunks.add(chunk)
            
                // 🎯 ATTENTION OVERLAY IMAGE DETECTION
                if (chunk.startsWith("ATTENTION_OVERLAY_BASE64:")) {
                    Log.i(TAG, "🎯 ATTENTION OVERLAY CHUNK DETECTED!")
                    Log.i(TAG, "   🖼️ Processing attention visualization image")

                    // Extract base64 data after the prefix
                    val base64Data = chunk.substring("ATTENTION_OVERLAY_BASE64:".length)
                    Log.i(TAG, "   📊 Base64 data length: ${base64Data.length} characters")

                    // Store the attention overlay data for later rendering
                    currentAttentionOverlayData = base64Data

                    // Add explanatory text to the stream
                    responseTextView.append("\n🎯 AI Attention Map - Focus Areas:\n")
                    responseTextView.append("  👁️ The highlighted areas show where the AI focused during disease detection\n")
                    responseTextView.append("  🖼️ Generating attention heatmap visualization...\n")

                    // Don't add this chunk to streamingChunks since we handle it separately
                    Log.i(TAG, "   ✅ Attention overlay data stored for rendering")
                    // Return early to avoid adding to streamingChunks
                    return@runOnUiThread

                } else if (isPipeSeperatedActionItems(chunk)) {
            // 🔍 PIPE-SEPARATED ACTION ITEMS DETECTION
                Log.i(TAG, "🎯 DETECTED PIPE-SEPARATED ACTION ITEMS:")
                Log.i(TAG, "   📋 Raw action items: '$chunk'")
                
                // Parse and display action items with special formatting
                val actionItems = chunk.split("|").map { it.trim() }.filter { it.isNotEmpty() }
                Log.i(TAG, "   📊 Parsed ${actionItems.size} action items")
                
                // Add section header for action items
                responseTextView.append("\n📋 Recommended Actions:\n")
                
                // Display each action item with special formatting
                actionItems.forEachIndexed { index, actionItem ->
                    val actionBullet = "  ✓ $actionItem"
                    responseTextView.append("$actionBullet\n")
                    Log.i(TAG, "   ✓ Action ${index + 1}: '$actionItem'")
                }
                
                Log.i(TAG, "   🎨 Formatted as highlighted action items list")
                
            } else {
                // 🎯 REGULAR BULLET POINT FORMATTING - Each chunk as a bullet point
                val bulletPointChunk = "  • $chunk"
                responseTextView.append("$bulletPointChunk\n")
                Log.i(TAG, "   💡 Formatted as regular bullet point: '$bulletPointChunk'")
            }
            
                Log.i(TAG, "   📱 CHUNK DISPLAYED ON SCREEN")
                Log.i(TAG, "   ⏰ Screen display time: ${System.currentTimeMillis()}")
                Log.i(TAG, "   ✅ Individual chunk streaming successful")
            
                // Auto-scroll to show new content with robust scrolling
                scrollToResponseEnd()
                Log.d(TAG, "   📜 Auto-scrolled to show new content")
            
            Log.i(TAG, "✅ STREAMING CHUNK PROCESSED SUCCESSFULLY")
            Log.i(TAG, "   📊 Updated total chunks: ${streamingChunks.size}")
                Log.i(TAG, "   🎯 Display format: Bullet point list / Attention image")
            Log.i(TAG, "   " + "=".repeat(50))
            } catch (e: Exception) {
                Log.e(TAG, "❌ Critical error in addStreamingChunk: ${e.message}", e)
                try {
                    // Attempt to show error to user if possible
                    responseTextView.append("\n⚠️ Error displaying response chunk\n")
                } catch (ex: Exception) {
                    Log.e(TAG, "❌ Failed to display error message: ${ex.message}", ex)
                }
            }
        }
    }

    // Helper method to reconstruct streaming bullet format from collected chunks
    private fun reconstructStreamedBulletFormat(chunks: List<String>): String {
        val result = StringBuilder()
        var hasActionItems = false

        // First, check if we have any pipe-separated action items
        val actionItemChunks = chunks.filter { isPipeSeperatedActionItems(it) }
        val regularChunks = chunks.filter { !isPipeSeperatedActionItems(it) }

        // Add regular bullet points first
        if (regularChunks.isNotEmpty()) {
            regularChunks.forEach { chunk ->
                result.append("  • $chunk\n")
            }
        }

        // Add action items with special formatting
        if (actionItemChunks.isNotEmpty()) {
            if (result.isNotEmpty()) {
                result.append("\n") // Add spacing before action items
            }
            result.append("📋 Recommended Actions:\n")

            actionItemChunks.forEach { chunk ->
                val actionItems = chunk.split("|").map { it.trim() }.filter { it.isNotEmpty() }
                actionItems.forEach { actionItem ->
                    result.append("  ✓ $actionItem\n")
                }
            }
            hasActionItems = true
        }

        Log.d(
            TAG,
            "Reconstructed streamed format with ${regularChunks.size} bullets and ${actionItemChunks.size} action item chunks"
        )
        return result.toString().trimEnd()
    }

    /**
     * Finalize streaming response and add it to conversation history
     */
    private fun finalizeStreamingResponse() {
        runOnUiThread {
            // Ensure thinking animation is completely stopped
            stopThinkingIndicator()

            // 📊 ENHANCED FINALIZATION LOGGING
            Log.i(TAG, "🏁 FINALIZING STREAMING RESPONSE:")
            Log.i(TAG, "   🔄 Currently streaming: $isCurrentlyStreaming")
            Log.i(TAG, "   📦 Chunks collected: ${streamingChunks.size}")
            
            if (isCurrentlyStreaming && streamingChunks.isNotEmpty()) {
                Log.i(TAG, "✅ PRESERVING REAL-TIME STREAMED DISPLAY:")
                Log.i(TAG, "   📊 Total chunks streamed individually: ${streamingChunks.size}")
                Log.i(TAG, "   🔄 Chunks were displayed in real-time, now preserving for history")
                
                // Log chunks for debugging (they were already displayed individually)
                streamingChunks.forEachIndexed { index, chunk ->
                    Log.i(TAG, "   📦 Chunk ${index + 1} (already displayed): '$chunk'")
                }

                // DON'T combine chunks - preserve the real-time streaming nature
                // The chunks have already been displayed in real-time via addStreamingChunk()
                // Now we just need to preserve the current streamed display for conversation history

                // Get the current displayed content (which shows the real-time streaming result)
                val currentDisplayedContent = responseTextView.text.toString()

                // Extract just the streamed response part (after the last "🤖" header)
                val lastBotIndex = currentDisplayedContent.lastIndexOf("🤖")
                val streamedContent = if (lastBotIndex != -1) {
                    currentDisplayedContent.substring(lastBotIndex)
                } else {
                    currentDisplayedContent
                }

                // Check if the streamed content represents a structured response
                val structuredResponse = parseStructuredResponse(streamedContent)
                
                if (structuredResponse != null) {
                    // Handle structured response - format with action items
                    val formattedMainAnswer =
                        formatMessageWithCollapsibleJson(structuredResponse.mainAnswer)
                    var assistantMsg = "🤖 $formattedMainAnswer"
                    
                    if (structuredResponse.actionItems.isNotEmpty()) {
                        assistantMsg += "\n\n📋 Quick Actions:"
                        structuredResponse.actionItems.forEach { actionItem ->
                            assistantMsg += "\n• $actionItem"
                        }
                    }
                    assistantMsg += "\n\n"
                    
                    // Add to new conversation messages list
                    val conversationMsg = ConversationMessage(
                        text = assistantMsg.removePrefix("🤖 "), // Remove emoji for clean display
                        isUser = false,
                        imageUri = null,
                        attentionOverlayData = currentAttentionOverlayData
                    )
                    conversationMessages.add(conversationMsg)

                    // Create spannable and add to legacy history
                    val spannableMessage = SpannableString(assistantMsg)
                    applyActionItemSpansToText(spannableMessage, structuredResponse.actionItems)
                    conversationHistory.append(spannableMessage)
                } else {
                    // Handle regular response - use the real-time streamed content as-is
                    // No need to reconstruct since we're preserving the actual streamed display

                    // Add to new conversation messages list (use the actual streamed display)
                    val conversationMsg = ConversationMessage(
                        text = streamedContent, // This preserves the actual real-time streamed formatting
                        isUser = false,
                        imageUri = null,
                        attentionOverlayData = currentAttentionOverlayData
                    )
                    conversationMessages.add(conversationMsg)

                    // Add to legacy history
                    conversationHistory.append("$streamedContent\n\n")
                }

                Log.i(TAG, "✅ REAL-TIME STREAMING PRESERVED:")
                Log.i(TAG, "   🔄 Used actual streamed display instead of combining chunks")
                Log.i(TAG, "   💾 Conversation history updated with streamed content")
                Log.i(TAG, "   📊 New conversation history length: ${conversationHistory.length}")
                
                // Clean up streaming state
                val totalChunks = streamingChunks.size
                streamingChunks.clear()
                isCurrentlyStreaming = false

                // Now update conversation display with the new message
                updateConversationDisplay()

                // Render attention overlay image if available
                if (currentAttentionOverlayData != null) {
                    Log.i(TAG, "🎯 RENDERING ATTENTION OVERLAY IMAGE:")
                    Log.i(
                        TAG,
                        "   📊 Base64 data length: ${currentAttentionOverlayData!!.length} characters"
                    )

                    try {
                        val attentionImageView =
                            createAttentionOverlayImageView(currentAttentionOverlayData!!)
                        if (attentionImageView != null) {
                            // Add the image to the conversation container
                            conversationContainer.addView(attentionImageView)

                            Log.i(TAG, "   ✅ Attention overlay image rendered successfully")
                            Log.i(TAG, "   🖼️ Image added to conversation container")
                        } else {
                            Log.e(TAG, "   ❌ Failed to create attention overlay ImageView")
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "   ❌ Error rendering attention overlay: ${e.message}")
                    }

                    // Clear the stored data
                    currentAttentionOverlayData = null
                    Log.i(TAG, "   🧹 Attention overlay data cleared")
                }

                // Ensure user can see the complete response with robust scrolling
                scrollToResponseEnd()
                
                Log.i(TAG, "🧹 STREAMING STATE CLEANUP COMPLETE:")
                Log.i(TAG, "   ✅ Processed ${totalChunks} chunks total")
                Log.i(TAG, "   🔄 Streaming state reset")
                Log.i(TAG, "   💾 Content added to conversation history")
                Log.i(TAG, "   📱 Conversation display updated with new message")
                Log.i(TAG, "   🎯 Bullet point formatting preserved")
                Log.i(TAG, "   🖼️ Attention overlay rendered if available")
                Log.i(TAG, "✅ STREAMING RESPONSE FINALIZED SUCCESSFULLY")

                // Save conversations after finalizing streaming response
                saveConversations()
            } else {
                // Just remove typing indicator if no streaming happened
                Log.i(TAG, "⚠️  NO STREAMING CONTENT TO FINALIZE:")
                Log.i(TAG, "   🔄 Currently streaming: $isCurrentlyStreaming")
                Log.i(TAG, "   📦 Chunks available: ${streamingChunks.size}")
                Log.i(TAG, "   🔧 Just removing typing indicator...")
                removeTypingIndicator()
                Log.i(TAG, "   ✅ Typing indicator removed")
            }
        }
    }


    // Helper function to convert Uri to Base64 String
    @Throws(IOException::class)
    private fun uriToBase64(uri: Uri): String? {
        val inputStream = contentResolver.openInputStream(uri) ?: return null
        val bitmap = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            ImageDecoder.decodeBitmap(ImageDecoder.createSource(contentResolver, uri))
        } else {
            MediaStore.Images.Media.getBitmap(contentResolver, uri)
        }
        val byteArrayOutputStream = ByteArrayOutputStream()
        // Choose format and quality. PNG is lossless, JPEG allows quality adjustment.
        bitmap.compress(
            Bitmap.CompressFormat.JPEG,
            80,
            byteArrayOutputStream
        ) // Adjust quality as needed
        val byteArray = byteArrayOutputStream.toByteArray()
        inputStream.close()
        return Base64.encodeToString(byteArray, Base64.DEFAULT)
    }

    /**
     * Detect if a chunk contains pipe-separated action items
     */
    private fun isPipeSeperatedActionItems(chunk: String): Boolean {
        // 🔍 DETECTION LOGIC for pipe-separated action items
        Log.d(TAG, "🔍 Analyzing chunk for action items: '$chunk'")
        
        // Check if chunk contains pipes and looks like action items
        val containsPipes = chunk.contains("|")
        val hasMultipleParts = chunk.split("|").size > 1
        val partsLookLikeActions = chunk.split("|").all { part ->
            val trimmedPart = part.trim()
            trimmedPart.isNotEmpty() && 
            (trimmedPart.length > 10) && // Action items are usually descriptive
            (trimmedPart.contains(" ")) && // Should contain spaces (multiple words)
            !trimmedPart.startsWith("http") && // Not URLs
            !trimmedPart.contains("...")  // Not typical progress messages
        }
        
        val isActionItems = containsPipes && hasMultipleParts && partsLookLikeActions
        
        Log.d(TAG, "   📊 Analysis results:")
        Log.d(TAG, "      🔗 Contains pipes: $containsPipes")
        Log.d(TAG, "      📄 Multiple parts: $hasMultipleParts")
        Log.d(TAG, "      ✅ Parts look like actions: $partsLookLikeActions")
        Log.d(
            TAG,
            "      🎯 Final decision: ${if (isActionItems) "ACTION ITEMS" else "REGULAR CHUNK"}"
        )
        
        return isActionItems
    }

    private fun fetchChatStreamFromServer(
        message: String,
        imageBase64: String?,
        sessionId: String?
        // text: String? // Add if required in ChatRequestData
    ) {
        showAnimatedThinkingIndicator() // Show animated thinking indicator with dots
        CoroutineScope(Dispatchers.IO).launch {
            try {
                // Get user agricultural profile from preferences
                val userProfile = getUserAgriculturalProfile()

                val requestData = ChatRequestData(
                    message = message,
                    image_b64 = imageBase64,
                    session_id = sessionId,
                    context = mapOf(
                        // Platform information
                        "platform" to "android",
                        "app_version" to "1.0.0",
                        "timestamp" to System.currentTimeMillis(),

                        // Agricultural context for personalized responses
                        "crop_type" to (userProfile["crop_type"] ?: "tomato"),
                        "location" to (userProfile["location"] ?: "Tamil Nadu"),
                        "season" to (userProfile["season"] ?: "summer"),
                        "growth_stage" to (userProfile["growth_stage"] ?: "flowering"),
                        "farming_experience" to (userProfile["farming_experience"] ?: "beginner"),
                        "farm_size" to (userProfile["farm_size"] ?: "small"),

                        // Request preferences
                        "streaming_requested" to true,
                        "detailed_analysis" to true,
                        "include_confidence" to true,
                        "image_source" to "android_camera"
                    ),
                    workflow_action = null // Let planning agent determine workflow automatically
                )

                val response = RetrofitClient.instance.chatStream(requestData)

                if (response.isSuccessful) {
                    val responseBody = response.body()
                    if (responseBody != null) {
                        val inputStream = responseBody.byteStream()
                        val reader = BufferedReader(InputStreamReader(inputStream, Charsets.UTF_8))
                        var line: String?
                        val fullResponse = StringBuilder()
                        // Do NOT remove typing indicator here - thinking should continue until first chunk
                        Log.d(TAG, "🤔 Keeping thinking indicator active until first response chunk")

                        try {
                            Log.i(TAG, "🌊 STARTING STREAM PROCESSING LOOP")
                            Log.i(TAG, "   📖 Reading lines from server stream...")
                            
                            var lineCount = 0

                            // FIXED: Remove dangerous context switching inside loop
                            while (reader.readLine().also { line = it } != null) {
                                val currentLine = line ?: ""
                                lineCount++
                                
                                try {
                                // 📊 COMPREHENSIVE LINE LOGGING
                                Log.i(TAG, "📥 STREAM LINE #$lineCount RECEIVED:")
                                Log.i(TAG, "   🔗 Raw content: '$currentLine'")
                                Log.i(TAG, "   📏 Length: ${currentLine.length}")
                                    Log.i(
                                        TAG,
                                        "   🔍 Is SSE format: ${currentLine.startsWith("data: ")}"
                                    )
                                    Log.i(
                                        TAG,
                                        "   ⏰ Processing timestamp: ${System.currentTimeMillis()}"
                                    )

                                if (currentLine.startsWith("data: ")) {
                                    val actualData = currentLine.substringAfter("data: ").trim()
                                    
                                    // 📊 ENHANCED SERVER-SENT EVENT LOGGING
                                    Log.i(TAG, "📡 SSE DATA RECEIVED:")
                                    Log.i(TAG, "   🔗 Raw line: '$currentLine'")
                                    Log.i(TAG, "   📦 Extracted data: '$actualData'")
                                    Log.i(TAG, "   📏 Data length: ${actualData.length}")
                                    
                                    if (actualData == "[DONE]") {
                                        Log.i(TAG, "🏁 STREAM COMPLETION SIGNAL RECEIVED")
                                        Log.i(TAG, "   ✅ Stream finished by [DONE] signal")
                                        break
                                    }
                                    if (actualData.isNotEmpty()) {
                                        fullResponse.append(actualData).append("\n")
                                        
                                        Log.i(TAG, "🚀 PROCESSING CHUNK FOR DISPLAY:")
                                        Log.i(TAG, "   📤 About to send to addStreamingChunk()")
                                            Log.i(
                                                TAG,
                                                "   🎯 Chunk will be formatted as bullet point"
                                            )
                                        
                                            // FIXED: Safer UI thread dispatch
                                            try {
                                        withContext(Dispatchers.Main) {
                                            addStreamingChunk(actualData)
                                        }
                                                Log.i(TAG, "✅ CHUNK DISPLAYED SUCCESSFULLY")
                                            } catch (e: Exception) {
                                                Log.e(
                                                    TAG,
                                                    "❌ Error displaying chunk: ${e.message}",
                                                    e
                                                )
                                            }
                                    } else {
                                            Log.w(
                                                TAG,
                                                "⚠️  Empty actualData received, skipping display"
                                            )
                                    }
                                } else if (currentLine.isNotEmpty()) {
                                    // Handle plain text chunks if not using SSE "data:" prefix
                                    Log.i(TAG, "📄 PLAIN TEXT CHUNK RECEIVED:")
                                    Log.i(TAG, "   🔗 Raw line: '$currentLine'")
                                    Log.i(TAG, "   📏 Line length: ${currentLine.length}")
                                    
                                    fullResponse.append(currentLine).append("\n")
                                    
                                    Log.i(TAG, "🚀 PROCESSING PLAIN TEXT CHUNK:")
                                    Log.i(TAG, "   📤 About to send to addStreamingChunk()")
                                    
                                        // FIXED: Safer UI thread dispatch
                                        try {
                                    withContext(Dispatchers.Main) {
                                        addStreamingChunk(currentLine)
                                    }
                                            Log.i(TAG, "✅ PLAIN TEXT CHUNK DISPLAYED SUCCESSFULLY")
                                        } catch (e: Exception) {
                                            Log.e(
                                                TAG,
                                                "❌ Error displaying plain text chunk: ${e.message}",
                                                e
                                            )
                                        }
                                    }
                                } catch (e: Exception) {
                                    Log.e(
                                        TAG,
                                        "❌ Error processing line #$lineCount: ${e.message}",
                                        e
                                    )
                                    // Continue processing other lines
                                }
                            }
                            
                            // Handle end of stream - finalize streaming response
                            Log.i(TAG, "🏁 STREAM PROCESSING COMPLETED")
                            Log.i(TAG, "   📊 Total lines processed: $lineCount")
                            Log.i(TAG, "   ✅ Stream finished naturally")
                            Log.i(TAG, "   🔄 About to finalize streaming response...")
                            
                            // FIXED: Proper UI thread dispatch for finalization
                            try {
                                withContext(Dispatchers.Main) {
                                finalizeStreamingResponse()
                            }
                            Log.i(TAG, "✅ STREAM FINALIZATION COMPLETE")
                            } catch (e: Exception) {
                                Log.e(TAG, "❌ Error finalizing stream: ${e.message}", e)
                            }
                        } catch (e: IOException) {
                            Log.e(TAG, "Error reading stream", e)
                            try {
                            withContext(Dispatchers.Main) {
                                finalizeStreamingResponse()
                                addAssistantMessage("⚠️ Error reading stream: ${e.message}")
                                }
                            } catch (ex: Exception) {
                                Log.e(TAG, "❌ Error handling IOException: ${ex.message}", ex)
                            }
                        } finally {
                            try {
                                reader.close()
                                inputStream.close()
                            responseBody.close()
                                Log.d(TAG, "✅ Stream resources closed successfully")
                            } catch (ex: Exception) {
                                Log.e(TAG, "❌ Error closing stream resources: ${ex.message}", ex)
                            }
                        }
                    } else {
                        Log.e(TAG, "Error: Empty response body")
                        try {
                        withContext(Dispatchers.Main) {
                            finalizeStreamingResponse()
                            addAssistantMessage("⚠️ Error: Empty response body")
                            }
                        } catch (ex: Exception) {
                            Log.e(TAG, "❌ Error handling empty response: ${ex.message}", ex)
                        }
                    }
                } else {
                    val errorBody = response.errorBody()?.string() ?: "Unknown error"
                    Log.e(TAG, "Error: ${response.code()} - $errorBody")
                    try {
                    withContext(Dispatchers.Main) {
                        finalizeStreamingResponse()
                        addAssistantMessage("⚠️ Error: ${response.code()} - $errorBody")
                        }
                    } catch (ex: Exception) {
                        Log.e(TAG, "❌ Error handling HTTP error: ${ex.message}", ex)
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Exception in fetchChatStreamFromServer", e)
                try {
                withContext(Dispatchers.Main) {
                    finalizeStreamingResponse()
                    addAssistantMessage("⚠️ Exception: ${e.message}")
                    }
                } catch (ex: Exception) {
                    Log.e(TAG, "❌ Error handling general exception: ${ex.message}", ex)
                }
            }
        }
    }


    // ===== USER AGRICULTURAL PROFILE MANAGEMENT =====

    /**
     * Get user agricultural profile from SharedPreferences
     */
    private fun getUserAgriculturalProfile(): Map<String, String> {
        val prefs = getSharedPreferences("agricultural_profile", Context.MODE_PRIVATE)

        return mapOf(
            "crop_type" to prefs.getString("crop_type", "tomato").orEmpty(),
            "location" to prefs.getString("location", "Tamil Nadu").orEmpty(),
            "season" to prefs.getString("season", "summer").orEmpty(),
            "growth_stage" to prefs.getString("growth_stage", "flowering").orEmpty(),
            "farming_experience" to prefs.getString("farming_experience", "beginner").orEmpty(),
            "farm_size" to prefs.getString("farm_size", "small").orEmpty()
        )
    }

    /**
     * Save user agricultural profile to SharedPreferences
     */
    private fun saveAgriculturalProfile(profile: Map<String, String>) {
        val prefs = getSharedPreferences("agricultural_profile", Context.MODE_PRIVATE)
        val editor = prefs.edit()

        profile.forEach { (key, value) ->
            editor.putString(key, value)
        }

        // Mark profile setup as completed
        editor.putBoolean("profile_setup_completed", true)

        editor.apply()
        Log.d(TAG, "Saved agricultural profile: $profile")
        
        // Update profile button to reflect completed setup
        updateProfileButtonState()
    }

    /**
     * Show dialog to collect/update user agricultural profile
     */
    private fun showAgriculturalProfileDialog() {
        val currentProfile = getUserAgriculturalProfile()

        val dialogView = layoutInflater.inflate(R.layout.dialog_agricultural_profile, null)

        // Get dialog elements (simplified to only state and farm size)
        val stateSpinner = dialogView.findViewById<Spinner>(R.id.stateSpinner)
        val farmSizeSpinner = dialogView.findViewById<Spinner>(R.id.farmSizeSpinner)

        // Set up spinners with current values
        setupProfileSpinner(stateSpinner, getStateOptions(), currentProfile["state"])
        setupProfileSpinner(farmSizeSpinner, getFarmSizeOptions(), currentProfile["farm_size"])

        AlertDialog.Builder(this)
            .setTitle("🌱 Agricultural Profile")
            .setMessage("Help us provide personalized plant advice by sharing your farming details:")
            .setView(dialogView)
            .setPositiveButton("Save") { _, _ ->
                val newProfile = mapOf(
                    "state" to stateSpinner.selectedItem.toString(),
                    "farm_size" to farmSizeSpinner.selectedItem.toString()
                )
                saveAgriculturalProfile(newProfile)
                Toast.makeText(
                    this,
                    "Profile saved! Your recommendations will be tailored to ${stateSpinner.selectedItem}.",
                    Toast.LENGTH_LONG
                ).show()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    /**
     * Setup spinner with options and select current value
     */
    private fun setupProfileSpinner(
        spinner: Spinner,
        options: List<String>,
        currentValue: String?
    ) {
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, options)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        spinner.adapter = adapter

        // Select current value if it exists
        currentValue?.let { value ->
            val position = options.indexOf(value)
            if (position >= 0) {
                spinner.setSelection(position)
            }
        }
    }

    // Options for profile spinners
    private fun getCropOptions() = listOf(
        "Tomato",
        "Potato",
        "Rice",
        "Wheat",
        "Corn",
        "Cotton",
        "Chili",
        "Onion",
        "Brinjal",
        "Okra"
    )

    private fun getStateOptions() = listOf(
        "Tamil Nadu",
        "Karnataka",
        "Kerala",
        "Andhra Pradesh",
        "Telangana",
        "Maharashtra",
        "Gujarat",
        "Rajasthan",
        "Punjab",
        "Haryana",
        "Other"
    )

    private fun getSeasonOptions() = listOf("Summer", "Monsoon", "Winter", "Kharif", "Rabi", "Zaid")
    private fun getGrowthStageOptions() =
        listOf("Seedling", "Vegetative", "Flowering", "Fruiting", "Maturity", "Harvesting")

    private fun getExperienceOptions() = listOf("Beginner", "Intermediate", "Experienced", "Expert")
    private fun getFarmSizeOptions() = listOf(
        "Small (< 1 acre)",
        "Medium (1-5 acres)",
        "Large (5-20 acres)",
        "Commercial (> 20 acres)"
    )

    /**
     * Check if user has set up agricultural profile and prompt if needed
     */
    private fun checkAndPromptAgriculturalProfile() {
        val prefs = getSharedPreferences("agricultural_profile", Context.MODE_PRIVATE)
        val hasSetupProfile = prefs.getBoolean("profile_setup_completed", false)

        if (!hasSetupProfile) {
            // Show welcome dialog encouraging profile setup
            AlertDialog.Builder(this)
                .setTitle("🌱 Welcome to Sasya Chikitsa!")
                .setMessage("Get personalized plant care advice by setting up your agricultural profile. This helps our AI provide recommendations specific to your crop, location, and farming context.\n\n✅ Accurate disease detection\n✅ Location-specific treatments\n✅ Seasonal recommendations\n✅ Experience-appropriate advice")
                .setPositiveButton("Set Up Profile") { _, _ ->
                    showAgriculturalProfileDialog()
                }
                .setNegativeButton("Maybe Later") { _, _ ->
                    // Mark that we've shown the prompt so it doesn't appear again immediately
                    prefs.edit().putBoolean("profile_prompt_shown", true).apply()
                }
                .setCancelable(false)
                .show()
        }
    }
    
    private fun launchFSMMode() {
        try {
            // Use the FSMLauncher to launch the intelligent assistant
//            FSMLauncher.launchFSMDiagnosis(this)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to launch FSM mode", e)
            Toast.makeText(this, "Failed to launch FSM Assistant: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }


    private fun showSimpleSettingsMenu() {
        // Simple fallback menu without AlertDialog
        val options = arrayOf(
            "🌱 Agricultural Profile",
            "🌐 Configure Server URL",
            "🗑️ Clear Conversation History"
        )
        
        // Create a simple selection using Toast and buttons
        android.widget.Toast.makeText(this, 
            "Settings Menu:\n1. Agricultural Profile\n2. Server URL\n3. Clear History", 
            android.widget.Toast.LENGTH_LONG).show()
            
        // You can add individual buttons or use a different approach here
        // For now, just show agricultural profile as default
        showAgriculturalProfileDialog()
    }

    private fun showClearConversationsDialog() {
        val builder = AlertDialog.Builder(this)
        builder.setTitle("🗑️ Clear Conversation History")
        builder.setMessage("Are you sure you want to clear all conversation history? This action cannot be undone.")

        builder.setPositiveButton("Clear All") { _, _ ->
            clearConversations()
        }

        builder.setNegativeButton("Cancel") { dialog, _ ->
            dialog.dismiss()
        }

        builder.show()
    }
    
    private fun showServerUrlDialog() {
        val defaultUrls = ServerConfig.getDefaultUrls()
        val currentUrl = ServerConfig.getServerUrl(this)
        
        val builder = AlertDialog.Builder(this)
        builder.setTitle("Configure Server URL")
        
        // Create a custom layout with spinner and input field
        val layout = layoutInflater.inflate(R.layout.dialog_server_url, null)
        val spinner = layout.findViewById<Spinner>(R.id.urlSpinner)
        val customUrlInput = layout.findViewById<EditText>(R.id.customUrlInput)
        
        // Setup spinner with default URLs
        val urlLabels = defaultUrls.map { it.first }
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, urlLabels)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        spinner.adapter = adapter
        
        // Pre-select current URL if it matches a default
        val currentIndex = defaultUrls.indexOfFirst { it.second == currentUrl }
        if (currentIndex != -1) {
            spinner.setSelection(currentIndex)
        } else {
            // Select "Custom" and populate input field
            spinner.setSelection(defaultUrls.size - 1)
            customUrlInput.setText(currentUrl)
        }
        
        // Show/hide custom input based on selection
        spinner.setOnItemSelectedListener(object :
            android.widget.AdapterView.OnItemSelectedListener {
            override fun onItemSelected(
                parent: android.widget.AdapterView<*>?,
                view: android.view.View?,
                position: Int,
                id: Long
            ) {
                customUrlInput.visibility =
                    if (position == defaultUrls.size - 1) android.view.View.VISIBLE else android.view.View.GONE
            }

            override fun onNothingSelected(parent: android.widget.AdapterView<*>?) {}
        })
        
        builder.setView(layout)
        builder.setPositiveButton("Save") { _, _ ->
            val selectedIndex = spinner.selectedItemPosition
            val newUrl = if (selectedIndex == defaultUrls.size - 1) {
                // Custom URL
                customUrlInput.text.toString().trim().let { url ->
                    if (!url.startsWith("http://") && !url.startsWith("https://")) {
                        "http://$url"
                    } else {
                        url
                    }
                }
            } else {
                defaultUrls[selectedIndex].second
            }
            
            if (newUrl.isNotEmpty() && ServerConfig.isValidUrl(newUrl)) {
                ServerConfig.setServerUrl(this, newUrl)
                RetrofitClient.refreshInstance() // Force recreate with new URL
                // Profile button state remains unchanged for server updates
                Toast.makeText(this, "Server URL updated to: $newUrl", Toast.LENGTH_LONG).show()
                Log.d(TAG, "Server URL updated to: $newUrl")
            } else {
                Toast.makeText(
                    this,
                    "Please enter a valid URL (e.g., http://192.168.1.100:8080/)",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
        builder.setNegativeButton("Cancel", null)
        
        val dialog = builder.create()
        dialog.show()
    }
    
    // Feedback handling methods
    private fun handleThumbsUpFeedback(message: ConversationMessage) {
        Log.d(TAG, "👍 Thumbs up feedback for message: ${message.text.take(50)}...")
        
        // Record feedback using FeedbackManager
        val feedback = com.example.sasya_chikitsa.models.MessageFeedback(
            messageText = message.text,
            feedbackType = com.example.sasya_chikitsa.models.FeedbackType.THUMBS_UP,
            sessionId = getCurrentSessionId(),
            userContext = "User gave positive feedback"
        )
        com.example.sasya_chikitsa.models.FeedbackManager.recordFeedback(feedback)
        
        runOnUiThread {
            android.widget.Toast.makeText(this, "👍 Thanks for your feedback!", android.widget.Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun handleThumbsDownFeedback(message: ConversationMessage) {
        Log.d(TAG, "👎 Thumbs down feedback for message: ${message.text.take(50)}...")
        
        // Record feedback using FeedbackManager
        val feedback = com.example.sasya_chikitsa.models.MessageFeedback(
            messageText = message.text,
            feedbackType = com.example.sasya_chikitsa.models.FeedbackType.THUMBS_DOWN,
            sessionId = getCurrentSessionId(),
            userContext = "User gave negative feedback - needs improvement"
        )
        com.example.sasya_chikitsa.models.FeedbackManager.recordFeedback(feedback)
        
        runOnUiThread {
            android.widget.Toast.makeText(this, "👎 Thanks for your feedback! We'll improve.", android.widget.Toast.LENGTH_SHORT).show()
        }
    }
    
    // Helper method to get current session ID
    private fun getCurrentSessionId(): String? {
        // Return the current session ID if available
        return sessionId
    }
    
    /**
     * Show server configuration dialog
     */
    private fun showSettingsDialog() {
        val dialogView = layoutInflater.inflate(R.layout.dialog_server_url, null)
        val urlSpinner = dialogView.findViewById<Spinner>(R.id.urlSpinner)
        val customUrlInput = dialogView.findViewById<EditText>(R.id.customUrlInput)

        // Server options
        val serverOptions = listOf(
            "Local Development (localhost)",
            "Production Server",
            "Staging Server", 
            "Custom URL"
        )

        // Setup spinner
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, serverOptions)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        urlSpinner.adapter = adapter

        // Get current server configuration
        val currentUrl = ServerConfig.getServerUrl(this)
        val currentIndex = when {
            currentUrl.contains("localhost") || currentUrl.contains("127.0.0.1") -> 0
            currentUrl.contains("production") -> 1
            currentUrl.contains("staging") -> 2
            else -> 3
        }
        urlSpinner.setSelection(currentIndex)

        // Show/hide custom URL input based on selection
        urlSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
                customUrlInput.visibility = if (position == 3) View.VISIBLE else View.GONE
                if (position == 3) {
                    customUrlInput.setText(currentUrl)
                }
            }
            override fun onNothingSelected(parent: AdapterView<*>?) {}
        }

        AlertDialog.Builder(this)
            .setTitle("⚙️ Server Settings")
            .setView(dialogView)
            .setPositiveButton("Save") { _, _ ->
                val selectedPosition = urlSpinner.selectedItemPosition
                val newUrl = when (selectedPosition) {
                    0 -> "http://localhost:8080/"
                    1 -> "https://production-server.com/"
                    2 -> "https://staging-server.com/"
                    3 -> {
                        var customUrl = customUrlInput.text.toString().trim()
                        if (customUrl.isNotEmpty() && !customUrl.endsWith("/")) {
                            customUrl += "/"
                        }
                        customUrl
                    }
                    else -> "http://localhost:8080/"
                }

                if (newUrl.isNotEmpty()) {
                    ServerConfig.setServerUrl(this, newUrl)
                    // Profile button state remains unchanged for server updates
                    Toast.makeText(this, "Server configuration updated to: $newUrl", Toast.LENGTH_LONG).show()
                } else {
                    Toast.makeText(this, "Please enter a valid URL", Toast.LENGTH_SHORT).show()
                }
            }
            .setNeutralButton("Profile") { _, _ ->
                showAgriculturalProfileDialog()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    /**
     * Update profile button based on user's agricultural profile setup status
     */
    private fun updateProfileButtonState() {
        val profileBtn = findViewById<ImageButton>(R.id.profileBtn)
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
                        // Profile button state remains unchanged for server updates
                        
                        val serverName = if (selectedPosition == defaultUrls.size - 1) "Custom Server" else defaultUrls[selectedPosition].first
                        Toast.makeText(this, "✅ Connected to $serverName\n$newUrl", Toast.LENGTH_LONG).show()
                        
                        Log.d(TAG, "Server URL updated to: $newUrl")
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
                        Toast.makeText(this@MainActivity, "✅ Server connection successful!", Toast.LENGTH_LONG).show()
                    } else {
                        Toast.makeText(this@MainActivity, "⚠️ Server responded but may not be fully ready (${response.code()})", Toast.LENGTH_LONG).show()
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    Toast.makeText(this@MainActivity, "❌ Connection failed: ${e.message}", Toast.LENGTH_LONG).show()
                    Log.e(TAG, "Server connection test failed for $url", e)
                }
            }
        }
    }
}