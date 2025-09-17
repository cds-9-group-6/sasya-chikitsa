package com.example.sasya_chikitsa.fsm

import com.google.gson.annotations.SerializedName

/**
 * Data models for FSM Agent communication
 * Based on the FSM agent's API structure
 */

// Request models
data class FSMChatRequest(
    @SerializedName("session_id") val sessionId: String? = null,
    @SerializedName("message") val message: String,
    @SerializedName("image_b64") val imageB64: String? = null,
    @SerializedName("context") val context: Map<String, Any>? = null
)

// Response models
data class FSMChatResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("messages") val messages: List<Any>,
    @SerializedName("state") val state: String? = null
)

// Streaming event models
data class FSMStateUpdate(
    @SerializedName("current_node") val currentNode: String? = null,
    @SerializedName("previous_node") val previousNode: String? = null,
    @SerializedName("messages") val messages: List<FSMMessage>? = null,
    @SerializedName("assistant_response") val assistantResponse: String? = null,
    @SerializedName("follow_up_items") val followUpItems: List<String>? = null,
    @SerializedName("is_complete") val isComplete: Boolean? = null,
    @SerializedName("error") val error: String? = null,
    @SerializedName("classification_result") val classificationResult: Map<String, Any>? = null,
    @SerializedName("prescription_details") val prescriptionDetails: Map<String, Any>? = null,
    @SerializedName("vendor_details") val vendorDetails: Map<String, Any>? = null
)

// Message models
data class FSMMessage(
    @SerializedName("role") val role: String, // "user" or "assistant"
    @SerializedName("content") val content: String,
    @SerializedName("timestamp") val timestamp: String? = null
)

// Chat message for UI display
data class ChatMessage(
    val text: String,
    val isUser: Boolean,
    val imageUri: String? = null,
    val timestamp: Long = System.currentTimeMillis(),
    val followUpItems: List<String>? = null,
    val state: String? = null,
    val attentionOverlayBase64: String? = null,
    val diseaseName: String? = null,
    val confidence: Double? = null
)

// Follow-up item for UI
data class FollowUpItem(
    val text: String,
    val isClicked: Boolean = false
)

// FSM session state
data class FSMSessionState(
    var sessionId: String? = null,
    var currentNode: String = "initial",
    var previousNode: String? = null,
    var isComplete: Boolean = false,
    val messages: MutableList<ChatMessage> = mutableListOf()
)

// Server event wrapper
data class ServerEvent(
    val event: String,
    val data: String
)

// Assistant response data for dedicated assistant_response events
data class AssistantResponseData(
    @SerializedName("assistant_response") val assistant_response: String? = null
)

// Attention overlay data for visualization
data class AttentionOverlayData(
    @SerializedName("attention_overlay") val attentionOverlay: String? = null,
    @SerializedName("disease_name") val diseaseName: String? = null,
    @SerializedName("confidence") val confidence: Double? = null,
    @SerializedName("source_node") val sourceNode: String? = null
)
