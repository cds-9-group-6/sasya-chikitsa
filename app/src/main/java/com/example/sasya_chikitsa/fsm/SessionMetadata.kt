package com.example.sasya_chikitsa.fsm

import java.text.SimpleDateFormat
import java.util.*

/**
 * Lightweight session metadata for UI display
 */
data class SessionMetadata(
    val sessionId: String,
    val title: String,
    val lastUpdated: Long,
    val messageCount: Int,
    val hasImages: Boolean = false,
    val hasDiagnosis: Boolean = false
) {
    
    /**
     * Format the last updated time for display
     */
    fun getFormattedTime(): String {
        val now = System.currentTimeMillis()
        val diff = now - lastUpdated
        
        return when {
            diff < 60_000 -> "Just now"
            diff < 3600_000 -> "${diff / 60_000}m ago"
            diff < 86400_000 -> "${diff / 3600_000}h ago"
            diff < 604800_000 -> "${diff / 86400_000}d ago"
            else -> SimpleDateFormat("MMM dd", Locale.getDefault()).format(Date(lastUpdated))
        }
    }
    
    /**
     * Get display title with indicators
     */
    fun getDisplayTitle(): String {
        val indicators = mutableListOf<String>()
        if (hasImages) indicators.add("📷")
        if (hasDiagnosis) indicators.add("🔍")
        
        val prefix = if (indicators.isNotEmpty()) "${indicators.joinToString("")} " else ""
        return "$prefix$title"
    }
    
    /**
     * Get subtitle with message count and time
     */
    fun getSubtitle(): String {
        val messages = if (messageCount == 1) "1 message" else "$messageCount messages"
        return "$messages • ${getFormattedTime()}"
    }
}
