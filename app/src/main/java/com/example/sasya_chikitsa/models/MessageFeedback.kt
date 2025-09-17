package com.example.sasya_chikitsa.models

/**
 * Data class for storing user feedback on assistant messages
 */
data class MessageFeedback(
    val messageId: String? = null,              // Unique identifier for the message
    val messageText: String,                    // The actual assistant message text
    val feedbackType: FeedbackType,             // Thumbs up or down
    val timestamp: Long = System.currentTimeMillis(), // When feedback was given
    val sessionId: String? = null,              // Session context
    val messageNode: String? = null,            // Which node generated this message (e.g., "classification", "prescription")
    val userContext: String? = null             // Additional context about what the user was asking
)

/**
 * Types of feedback users can provide
 */
enum class FeedbackType {
    THUMBS_UP,
    THUMBS_DOWN
}

/**
 * Simple feedback manager for storing and retrieving feedback
 */
object FeedbackManager {
    private val feedbackList = mutableListOf<MessageFeedback>()
    
    /**
     * Record user feedback for a message
     */
    fun recordFeedback(feedback: MessageFeedback) {
        feedbackList.add(feedback)
        // TODO: Send to backend analytics service
        // TODO: Store in local database for offline capability
        android.util.Log.d("FeedbackManager", "Recorded ${feedback.feedbackType} feedback: ${feedback.messageText.take(50)}...")
    }
    
    /**
     * Get all feedback for analytics
     */
    fun getAllFeedback(): List<MessageFeedback> = feedbackList.toList()
    
    /**
     * Get feedback statistics
     */
    fun getFeedbackStats(): FeedbackStats {
        val totalFeedback = feedbackList.size
        val thumbsUp = feedbackList.count { it.feedbackType == FeedbackType.THUMBS_UP }
        val thumbsDown = feedbackList.count { it.feedbackType == FeedbackType.THUMBS_DOWN }
        
        return FeedbackStats(
            totalFeedback = totalFeedback,
            thumbsUpCount = thumbsUp,
            thumbsDownCount = thumbsDown,
            positiveRatio = if (totalFeedback > 0) thumbsUp.toDouble() / totalFeedback else 0.0
        )
    }
    
    /**
     * Clear all feedback (for testing/reset)
     */
    fun clearAllFeedback() {
        feedbackList.clear()
    }
}

/**
 * Feedback statistics
 */
data class FeedbackStats(
    val totalFeedback: Int,
    val thumbsUpCount: Int,
    val thumbsDownCount: Int,
    val positiveRatio: Double  // Between 0.0 and 1.0
)
