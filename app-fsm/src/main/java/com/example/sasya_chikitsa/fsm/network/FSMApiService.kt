package com.example.sasya_chikitsa.fsm.network

import com.example.sasya_chikitsa.fsm.data.FSMChatRequest
import com.example.sasya_chikitsa.fsm.data.FSMChatResponse
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.*

/**
 * API interface for FSM agent communication
 */
interface FSMApiService {
    
    /**
     * Send chat message with streaming response (SSE)
     */
    @Streaming
    @POST("sasya-chikitsa/chat-stream")
    suspend fun chatStream(
        @Body request: FSMChatRequest,
        @Header("Accept") acceptHeader: String = "text/event-stream",
        @Header("Cache-Control") cacheControl: String = "no-cache"
    ): Response<ResponseBody>
    
    /**
     * Send chat message with JSON response (non-streaming)
     */
    @POST("sasya-chikitsa/chat")
    suspend fun chat(
        @Body request: FSMChatRequest
    ): Response<FSMChatResponse>
    
    /**
     * Get session information
     */
    @GET("sasya-chikitsa/session/{sessionId}")
    suspend fun getSession(
        @Path("sessionId") sessionId: String
    ): Response<Map<String, Any>>
    
    /**
     * Get conversation history for a session
     */
    @GET("sasya-chikitsa/session/{sessionId}/history")
    suspend fun getSessionHistory(
        @Path("sessionId") sessionId: String
    ): Response<List<Map<String, Any>>>
    
    /**
     * Get classification results for a session
     */
    @GET("sasya-chikitsa/session/{sessionId}/classification")
    suspend fun getClassificationResults(
        @Path("sessionId") sessionId: String
    ): Response<Map<String, Any>>
    
    /**
     * Get prescription data for a session
     */
    @GET("sasya-chikitsa/session/{sessionId}/prescription")
    suspend fun getPrescriptionData(
        @Path("sessionId") sessionId: String
    ): Response<Map<String, Any>>
    
    /**
     * Delete/end a session
     */
    @DELETE("sasya-chikitsa/session/{sessionId}")
    suspend fun endSession(
        @Path("sessionId") sessionId: String
    ): Response<Map<String, Any>>
    
    /**
     * Health check
     */
    @GET("health")
    suspend fun healthCheck(): Response<Map<String, Any>>
    
    /**
     * Get agent statistics
     */
    @GET("sasya-chikitsa/stats")
    suspend fun getStats(): Response<Map<String, Any>>
}
