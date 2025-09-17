package com.example.sasya_chikitsa.network

import android.content.Context
import com.example.sasya_chikitsa.config.ServerConfig
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {
    private var context: Context? = null
    private var cachedInstance: ApiService? = null
    
    fun initialize(context: Context) {
        this.context = context.applicationContext
        // Clear cached instance when context changes to force recreation with new URL
        cachedInstance = null
    }
    
    val instance: ApiService 
        get() {
            return cachedInstance ?: createInstance().also { cachedInstance = it }
        }
    
    private fun createInstance(): ApiService {
        val currentContext = context ?: throw IllegalStateException("RetrofitClient not initialized. Call initialize(context) first.")
        val baseUrl = ServerConfig.getServerUrl(currentContext)
        
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY // Or Level.BASIC for less verbosity
        }
        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(0, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            // Add a converter factory for your request body if not using a simple one.
            // For the response, you're getting ResponseBody, so a typical JSON converter
            // isn't strictly for deserializing the whole stream at once, but might
            // be needed if your ChatRequestData needs to be serialized to JSON.
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        return retrofit.create(ApiService::class.java)
    }
    
    fun refreshInstance() {
        cachedInstance = null
    }
    
    /**
     * Get ApiService with custom URL for testing connections
     */
    fun getApiService(customUrl: String): ApiService {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC // Less verbose for testing
        }
        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(10, TimeUnit.SECONDS) // Shorter timeout for testing
            .readTimeout(10, TimeUnit.SECONDS)
            .writeTimeout(10, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(customUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        return retrofit.create(ApiService::class.java)
    }
}
