package com.example.sasya_chikitsa.fsm

import android.content.Context
import android.util.Log
import java.text.SimpleDateFormat
import java.util.*

/**
 * In-Memory Session Manager
 * Manages multiple conversation sessions without disk persistence
 */
class SessionManager private constructor(private val context: Context) {
    
    companion object {
        private const val TAG = "SessionManager"
        @Volatile
        private var INSTANCE: SessionManager? = null
        
        fun getInstance(context: Context): SessionManager {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: SessionManager(context.applicationContext).also { INSTANCE = it }
            }
        }
    }
    
    // In-memory storage
    private val sessions = mutableMapOf<String, ConversationSession>()
    private var currentSessionId: String? = null
    
    init {
        Log.d(TAG, "SessionManager initialized with in-memory storage")
        
        // Create first session if none exist
        if (sessions.isEmpty()) {
            val firstSession = createNewSession("🌱 Plant Health Chat")
            currentSessionId = firstSession.sessionId
            Log.d(TAG, "Created initial session: ${firstSession.sessionId}")
        }
    }
    
    /**
     * Creates a new conversation session
     */
    fun createNewSession(title: String = generateSessionTitle()): ConversationSession {
        val sessionId = UUID.randomUUID().toString()
        val session = ConversationSession(
            sessionId = sessionId,
            title = title,
            createdAt = System.currentTimeMillis(),
            lastUpdated = System.currentTimeMillis()
        )
        
        sessions[sessionId] = session
        currentSessionId = sessionId
        
        Log.d(TAG, "Created new session: $sessionId with title: $title")
        return session
    }
    
    /**
     * Auto-create session specifically for new image analysis
     */
    fun createAutoSessionForNewImage(): ConversationSession {
        val title = "🔍 ${SimpleDateFormat("MMM dd, HH:mm", Locale.getDefault()).format(Date())}"
        return createNewSession(title)
    }
    
    /**
     * Switch to a specific session
     */
    fun switchToSession(sessionId: String): ConversationSession? {
        val session = sessions[sessionId]
        if (session != null) {
            currentSessionId = sessionId
            session.lastUpdated = System.currentTimeMillis()
            Log.d(TAG, "Switched to session: $sessionId")
        } else {
            Log.e(TAG, "Session not found: $sessionId")
        }
        return session
    }
    
    /**
     * Get current active session
     */
    fun getCurrentSession(): ConversationSession {
        currentSessionId?.let { sessionId ->
            sessions[sessionId]?.let { return it }
        }
        
        // Fallback: create new session if current doesn't exist
        Log.w(TAG, "Current session not found, creating new one")
        return createNewSession()
    }
    
    /**
     * Get all sessions sorted by last updated (newest first)
     */
    fun getAllSessions(): List<SessionMetadata> {
        return sessions.values
            .sortedByDescending { it.lastUpdated }
            .map { session ->
                SessionMetadata(
                    sessionId = session.sessionId,
                    title = session.title,
                    lastUpdated = session.lastUpdated,
                    messageCount = session.messages.size,
                    hasImages = session.messages.any { !it.imageUri.isNullOrEmpty() },
                    hasDiagnosis = session.hasDiagnosis
                )
            }
    }
    
    /**
     * Add a message to a specific session
     */
    fun addMessageToSession(sessionId: String, message: ChatMessage) {
        sessions[sessionId]?.let { session ->
            session.messages.add(message)
            session.lastUpdated = System.currentTimeMillis()
            
            // Update session metadata based on message content
            if (!message.imageUri.isNullOrEmpty()) {
                // If message has image, assume it might lead to diagnosis
                session.plantType = extractPlantType(message.text)
            }
            
            if (!message.isUser && message.text.contains("PLANT DISEASE ANALYSIS", ignoreCase = true)) {
                session.hasDiagnosis = true
                session.diseaseName = extractDiseaseName(message.text)
            }
            
            Log.d(TAG, "Added message to session $sessionId. Total messages: ${session.messages.size}")
        } ?: Log.e(TAG, "Cannot add message - session not found: $sessionId")
    }
    
    /**
     * Update the last message in a specific session (for WhatsApp-style streaming)
     */
    fun updateLastMessageInSession(sessionId: String, updatedMessage: ChatMessage) {
        sessions[sessionId]?.let { session ->
            if (session.messages.isNotEmpty()) {
                // Replace the last message
                session.messages[session.messages.size - 1] = updatedMessage
                session.lastUpdated = System.currentTimeMillis()
                
                // Update session metadata based on message content
                if (!updatedMessage.isUser && updatedMessage.text.contains("PLANT DISEASE ANALYSIS", ignoreCase = true)) {
                    session.hasDiagnosis = true
                    session.diseaseName = extractDiseaseName(updatedMessage.text)
                }
                
                Log.d(TAG, "Updated last message in session $sessionId")
            } else {
                Log.w(TAG, "Cannot update last message - session $sessionId has no messages")
            }
        } ?: Log.e(TAG, "Cannot update message - session not found: $sessionId")
    }
    
    /**
     * Update FSM state for a session
     */
    fun updateSessionFSMState(sessionId: String, fsmState: FSMSessionState) {
        sessions[sessionId]?.let { session ->
            session.fsmState = fsmState
            session.lastUpdated = System.currentTimeMillis()
            Log.d(TAG, "Updated FSM state for session: $sessionId")
        }
    }
    
    /**
     * Check if we should create a new session for a new image
     * Returns true if current session already has a diagnosis
     */
    fun shouldCreateNewSessionForImage(): Boolean {
        val currentSession = getCurrentSession()
        val shouldCreate = currentSession.hasDiagnosis && currentSession.messages.any { !it.imageUri.isNullOrEmpty() }
        
        Log.d(TAG, "Should create new session for image: $shouldCreate (current has diagnosis: ${currentSession.hasDiagnosis})")
        return shouldCreate
    }
    
    /**
     * Delete a session (optional - for cleanup)
     */
    fun deleteSession(sessionId: String): Boolean {
        val removed = sessions.remove(sessionId) != null
        if (removed) {
            // If we deleted the current session, switch to another
            if (currentSessionId == sessionId) {
                currentSessionId = sessions.keys.firstOrNull()
                if (currentSessionId == null) {
                    // Create new session if all were deleted
                    createNewSession()
                }
            }
            Log.d(TAG, "Deleted session: $sessionId")
        }
        return removed
    }
    
    // Helper methods
    private fun generateSessionTitle(): String {
        val formatter = SimpleDateFormat("MMM dd, HH:mm", Locale.getDefault())
        return "🌱 ${formatter.format(Date())}"
    }
    
    private fun extractPlantType(messageText: String): String? {
        // Simple extraction - can be enhanced with ML
        val lowerText = messageText.lowercase()
        return when {
            lowerText.contains("tomato") -> "Tomato"
            lowerText.contains("potato") -> "Potato"
            lowerText.contains("rice") -> "Rice"
            lowerText.contains("wheat") -> "Wheat"
            lowerText.contains("corn") -> "Corn"
            else -> null
        }
    }
    
    private fun extractDiseaseName(responseText: String): String? {
        // Extract disease name from response - simple pattern matching
        val patterns = listOf(
            "Your plant has: \\*\\*(.*?)\\*\\*",
            "Disease: \\*\\*(.*?)\\*\\*",
            "Condition: \\*\\*(.*?)\\*\\*"
        )
        
        for (pattern in patterns) {
            val regex = Regex(pattern)
            val match = regex.find(responseText)
            if (match != null) {
                return match.groupValues[1].trim()
            }
        }
        return null
    }
    
    // Get session count for debugging
    fun getSessionCount(): Int = sessions.size
    
    // Clear all sessions (for testing/reset)
    fun clearAllSessions() {
        sessions.clear()
        currentSessionId = null
        createNewSession() // Always keep at least one session
        Log.d(TAG, "Cleared all sessions and created fresh one")
    }
}