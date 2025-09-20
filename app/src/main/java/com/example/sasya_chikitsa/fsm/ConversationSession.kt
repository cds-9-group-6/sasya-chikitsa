package com.example.sasya_chikitsa.fsm

import com.google.gson.annotations.SerializedName
import java.text.SimpleDateFormat
import java.util.*

/**
 * Data models for conversation session management and persistence
 */

/**
 * Represents a complete conversation session with metadata
 */
data class ConversationSession(
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("title") val title: String,
    @SerializedName("created_at") val createdAt: Long = System.currentTimeMillis(),
    @SerializedName("last_updated") var lastUpdated: Long = System.currentTimeMillis(),
    @SerializedName("messages") val messages: MutableList<ChatMessage> = mutableListOf(),
    @SerializedName("fsm_state") var fsmState: FSMSessionState? = null,
    @SerializedName("has_diagnosis") var hasDiagnosis: Boolean = false,
    @SerializedName("plant_type") var plantType: String? = null,
    @SerializedName("disease_name") var diseaseName: String? = null,
    @SerializedName("is_active") var isActive: Boolean = true
) {
    /**
     * Generate user-friendly display title
     */
    fun getDisplayTitle(): String {
        return when {
            title.isNotBlank() -> title
            diseaseName != null -> "🌿 $diseaseName Analysis"
            plantType != null -> "🌱 $plantType Health Check"
            messages.isNotEmpty() -> {
                val firstUserMessage = messages.firstOrNull { it.isUser }?.text?.take(30) ?: "New Session"
                "💬 $firstUserMessage${if (firstUserMessage.length > 30) "..." else ""}"
            }
            else -> "🆕 New Session"
        }
    }

    /**
     * Get formatted timestamp for display
     */
    fun getFormattedTime(): String {
        val formatter = SimpleDateFormat("MMM dd, HH:mm", Locale.getDefault())
        return formatter.format(Date(lastUpdated))
    }

    /**
     * Check if session has meaningful content
     */
    fun hasContent(): Boolean {
        return messages.isNotEmpty() && messages.any { it.text.isNotBlank() }
    }

    /**
     * Get summary for dropdown display
     */
    fun getDropdownSummary(): String {
        val timeStr = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(lastUpdated))
        val summary = when {
            diseaseName != null -> "$diseaseName"
            hasContent() -> {
                val firstMessage = messages.firstOrNull { it.isUser }?.text?.take(20) ?: ""
                if (firstMessage.length > 20) "$firstMessage..." else firstMessage
            }
            else -> "New Session"
        }
        return "$summary • $timeStr"
    }
}


/**
 * Container for all sessions storage
 */
data class SessionStorage(
    @SerializedName("sessions") val sessions: MutableMap<String, ConversationSession> = mutableMapOf(),
    @SerializedName("active_session_id") var activeSessionId: String? = null,
    @SerializedName("last_session_id") var lastSessionId: Int = 0
)
