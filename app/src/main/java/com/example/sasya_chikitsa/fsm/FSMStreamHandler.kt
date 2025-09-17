package com.example.sasya_chikitsa.fsm

import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonSyntaxException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.ResponseBody
import java.io.BufferedReader
import java.io.IOException
import java.io.InputStreamReader

/**
 * Handler for FSM agent streaming responses (Server-Sent Events)
 */
class FSMStreamHandler {
    
    private val gson = Gson()
    private val TAG = "FSMStreamHandler"
    
    interface StreamCallback {
        fun onStateUpdate(stateUpdate: FSMStateUpdate)
        fun onMessage(message: String)
        fun onFollowUpItems(items: List<String>)
        fun onAttentionOverlay(overlayData: AttentionOverlayData)
        fun onError(error: String)
        fun onStreamComplete()
    }
    
    /**
     * Process streaming response from FSM agent
     */
    suspend fun processStream(responseBody: ResponseBody, callback: StreamCallback) {
        withContext(Dispatchers.IO) {
            try {
                val reader = BufferedReader(InputStreamReader(responseBody.byteStream()))
                var line: String?
                var currentEvent = ""
                var currentData = ""
                
                while (reader.readLine().also { line = it } != null) {
                    line?.let { currentLine ->
                        Log.d(TAG, "Received line: $currentLine")
                        
                        when {
                            currentLine.startsWith("event: ") -> {
                                currentEvent = currentLine.substringAfter("event: ").trim()
                            }
                            
                            currentLine.startsWith("data: ") -> {
                                currentData = currentLine.substringAfter("data: ").trim()
                            }
                            
                            currentLine.isEmpty() -> {
                                // End of event, process it
                                if (currentEvent.isNotEmpty() && currentData.isNotEmpty()) {
                                    processEvent(currentEvent, currentData, callback)
                                }
                                // Reset for next event
                                currentEvent = ""
                                currentData = ""
                            }
                        }
                    }
                }
                
                withContext(Dispatchers.Main) {
                    callback.onStreamComplete()
                }
                
            } catch (e: IOException) {
                Log.e(TAG, "Error processing stream", e)
                withContext(Dispatchers.Main) {
                    callback.onError("Stream processing error: ${e.message}")
                }
            } finally {
                responseBody.close()
            }
        }
    }
    
    /**
     * Process individual SSE events
     */
    private suspend fun processEvent(event: String, data: String, callback: StreamCallback) {
        Log.d(TAG, "Processing event: $event, data: $data")
        
        withContext(Dispatchers.Main) {
            try {
                when (event) {
                    "state_update" -> {
                        val stateUpdate = gson.fromJson(data, FSMStateUpdate::class.java)
                        callback.onStateUpdate(stateUpdate)
                        
                        // Handle specific parts of state update
                        stateUpdate.assistantResponse?.let { message ->
                            if (message.isNotBlank()) {
                                callback.onMessage(message)
                            }
                        }
                        
                        stateUpdate.followUpItems?.let { items ->
                            if (items.isNotEmpty()) {
                                callback.onFollowUpItems(items)
                            }
                        }
                        
                        stateUpdate.error?.let { error ->
                            callback.onError(error)
                        }
                    }
                    
                    "assistant_response" -> {
                        // FIXED: Handle new assistant_response events from modular architecture
                        try {
                            val responseData = gson.fromJson(data, AssistantResponseData::class.java)
                            responseData.assistant_response?.let { message ->
                                if (message.isNotBlank()) {
                                    callback.onMessage(message)
                                }
                            }
                        } catch (e: Exception) {
                            // Fallback: treat as plain text if JSON parsing fails
                            Log.w(TAG, "Failed to parse assistant_response as JSON, treating as plain text: ${e.message}")
                            callback.onMessage(data)
                        }
                    }
                    
                    "message" -> {
                        callback.onMessage(data)
                    }
                    
                    "error" -> {
                        callback.onError(data)
                    }
                    
                    "attention_overlay" -> {
                        try {
                            val overlayData = gson.fromJson(data, AttentionOverlayData::class.java)
                            callback.onAttentionOverlay(overlayData)
                        } catch (e: Exception) {
                            Log.e(TAG, "Error parsing attention overlay data: ${e.message}")
                            callback.onError("Failed to parse attention overlay: ${e.message}")
                        }
                    }
                    
                    "complete" -> {
                        callback.onStreamComplete()
                    }
                    
                    else -> {
                        Log.d(TAG, "Unknown event type: $event")
                    }
                }
                
            } catch (e: JsonSyntaxException) {
                Log.e(TAG, "Error parsing JSON: $data", e)
                callback.onError("Failed to parse server response: ${e.message}")
            } catch (e: Exception) {
                Log.e(TAG, "Error processing event: $event", e)
                callback.onError("Error processing event: ${e.message}")
            }
        }
    }
    
    /**
     * Create a properly formatted chat request
     */
    fun createChatRequest(
        message: String,
        imageBase64: String? = null,
        sessionId: String? = null,
        context: Map<String, Any>? = null
    ): FSMChatRequest {
        return FSMChatRequest(
            sessionId = sessionId,
            message = message,
            imageB64 = imageBase64,
            context = context
        )
    }
    
    /**
     * Parse follow-up items from state update
     */
    fun parseFollowUpItems(stateUpdate: FSMStateUpdate): List<FollowUpItem> {
        return stateUpdate.followUpItems?.map { text ->
            FollowUpItem(text = text, isClicked = false)
        } ?: emptyList()
    }
    
    /**
     * Get current state display name
     */
    fun getStateDisplayName(currentNode: String?): String {
        return when (currentNode) {
            "initial" -> "Ready"
            "classifying" -> "Analyzing Plant..."
            "prescribing" -> "Generating Treatment..."
            "vendor_query" -> "Finding Vendors..."
            "show_vendors" -> "Vendor Information"
            "completed" -> "Diagnosis Complete"
            else -> currentNode?.replaceFirstChar { 
                if (it.isLowerCase()) it.titlecase() else it.toString() 
            } ?: "Processing..."
        }
    }
}
