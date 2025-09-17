package com.example.sasya_chikitsa.network

import com.example.sasya_chikitsa.network.request.ChatRequestData
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.GET
import retrofit2.http.Query
import retrofit2.http.Streaming // Important for streaming

interface ApiService {

    @Streaming // Indicate that this is a streaming response
    @POST("planning/chat-stream")
    suspend fun chatStream(
        @Body requestBody: ChatRequestData,
        @Query("format") format: String? = null, // For the optional query parameter
        @Header("Accept") acceptHeader: String = "text/event-stream" // Default to SSE
    ): Response<ResponseBody> // ResponseBody allows you to read the raw stream
    
    @GET("health")
    suspend fun testConnection(): Response<ResponseBody>
}