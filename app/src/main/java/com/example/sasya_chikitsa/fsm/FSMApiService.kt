package com.example.sasya_chikitsa.fsm

import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.http.*

/**
 * FSM Agent API Service interface for Retrofit
 */
interface FSMApiService {
    
    /**
     * Standard chat endpoint (non-streaming)
     */
    @POST("sasya-chikitsa/chat")
    @Headers("Content-Type: application/json")
    fun chat(@Body request: FSMChatRequest): Call<FSMChatResponse>
    
    /**
     * Streaming chat endpoint for real-time FSM agent responses
     * Returns Server-Sent Events (SSE) stream
     */
    @POST("sasya-chikitsa/chat-stream")
    @Headers(
        "Accept: text/event-stream",
        "Content-Type: application/json",
        "Cache-Control: no-cache"
    )
    @Streaming
    fun chatStream(@Body request: FSMChatRequest): Call<ResponseBody>
    
    /**
     * Health check endpoint
     */
    @GET("health")
    fun healthCheck(): Call<Map<String, Any>>
    
    /**
     * Session info endpoint
     */
    @GET("sasya-chikitsa/session/{sessionId}")
    fun getSessionInfo(@Path("sessionId") sessionId: String): Call<Map<String, Any>>
    
    /**
     * Cleanup session endpoint
     */
    @POST("sasya-chikitsa/cleanup")
    fun cleanupSession(@Body sessionData: Map<String, String>): Call<Map<String, Any>>
    
    /**
     * Agent stats endpoint
     */
    @GET("sasya-chikitsa/stats")
    fun getAgentStats(): Call<Map<String, Any>>
}
