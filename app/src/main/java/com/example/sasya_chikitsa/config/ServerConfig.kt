package com.example.sasya_chikitsa.config

import android.content.Context
import android.content.SharedPreferences
import com.example.sasya_chikitsa.BuildConfig

/**
 * Server configuration management for the Sasya Chikitsa app.
 * 
 * This configuration supports multiple build variants:
 * - GPU Variant: Configured for GPU-enabled cluster
 * - Non-GPU Variant: Configured for standard processing cluster
 * - Debug: Uses local development server (emulator/localhost)
 * 
 * Production URLs:
 * - GPU Cluster: http://engine-sasya-chikitsa.apps.cluster-mqklc.mqklc.sandbox601.opentlc.com/
 * - Non-GPU Cluster: http://engine-sasya-chikitsa.apps.cluster-6twrd.6twrd.sandbox1818.opentlc.com/
 */
object ServerConfig {
    private const val PREF_NAME = "sasya_chikitsa_config"
    private const val SERVER_URL_KEY = "server_url"
    private const val SERVER_TYPE_KEY = "server_type"
    
    // Default URLs for development scenarios
    const val DEFAULT_EMULATOR_URL = "http://10.0.2.2:8080/"
    const val DEFAULT_LOCALHOST_URL = "http://localhost:8080/"
    const val DEFAULT_LOCAL_IP_URL = "http://192.168.1.100:8080/"
    
    // Production URLs from BuildConfig (set by product flavors)
    val GPU_CLUSTER_URL: String get() = BuildConfig.SERVER_URL_GPU
    val NON_GPU_CLUSTER_URL: String get() = BuildConfig.SERVER_URL_NON_GPU
    val DEFAULT_SERVER_TYPE: String get() = BuildConfig.DEFAULT_SERVER_TYPE
    val APP_VARIANT: String get() = BuildConfig.APP_VARIANT
    
    // Server type constants
    const val SERVER_TYPE_GPU = "GPU"
    const val SERVER_TYPE_NON_GPU = "NON_GPU"
    const val SERVER_TYPE_CUSTOM = "CUSTOM"
    
    private fun getPreferences(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }
    
    fun getServerUrl(context: Context): String {
        val prefs = getPreferences(context)
        val savedUrl = prefs.getString(SERVER_URL_KEY, null)
        
        // If user has set a custom URL, use it
        if (!savedUrl.isNullOrEmpty()) {
            return savedUrl
        }
        
        // Otherwise, use the default URL based on build variant and server type
        val serverType = getServerType(context)
        return when (serverType) {
            SERVER_TYPE_GPU -> GPU_CLUSTER_URL
            SERVER_TYPE_NON_GPU -> NON_GPU_CLUSTER_URL
            else -> getDefaultUrlForVariant()
        }
    }
    
    fun setServerUrl(context: Context, url: String) {
        val prefs = getPreferences(context)
        prefs.edit().putString(SERVER_URL_KEY, url).apply()
    }
    
    fun getServerType(context: Context): String {
        val prefs = getPreferences(context)
        return prefs.getString(SERVER_TYPE_KEY, DEFAULT_SERVER_TYPE) ?: DEFAULT_SERVER_TYPE
    }
    
    fun setServerType(context: Context, serverType: String) {
        val prefs = getPreferences(context)
        prefs.edit().putString(SERVER_TYPE_KEY, serverType).apply()
    }
    
    private fun getDefaultUrlForVariant(): String {
        return when (DEFAULT_SERVER_TYPE) {
            SERVER_TYPE_GPU -> GPU_CLUSTER_URL
            SERVER_TYPE_NON_GPU -> NON_GPU_CLUSTER_URL
            "DEBUG" -> DEFAULT_EMULATOR_URL
            else -> DEFAULT_EMULATOR_URL
        }
    }
    
    fun getDefaultUrls(): List<Pair<String, String>> {
        val urls = mutableListOf<Pair<String, String>>()
        
        // Add development URLs
        urls.add("Android Emulator" to DEFAULT_EMULATOR_URL)
        urls.add("Localhost" to DEFAULT_LOCALHOST_URL)
        urls.add("Local Network (192.168.1.x)" to DEFAULT_LOCAL_IP_URL)
        
        // Add production URLs
        urls.add("GPU Cluster (Production)" to GPU_CLUSTER_URL)
        urls.add("Non-GPU Cluster (Production)" to NON_GPU_CLUSTER_URL)
        
        // Add custom URL option
        urls.add("Custom URL" to "")
        
        return urls
    }
    
    fun getServerDisplayName(context: Context): String {
        val currentUrl = getServerUrl(context)
        val serverType = getServerType(context)
        
        return when {
            currentUrl == GPU_CLUSTER_URL -> "GPU Cluster"
            currentUrl == NON_GPU_CLUSTER_URL -> "Non-GPU Cluster"
            currentUrl == DEFAULT_EMULATOR_URL -> "Android Emulator"
            currentUrl == DEFAULT_LOCALHOST_URL -> "Localhost"
            currentUrl == DEFAULT_LOCAL_IP_URL -> "Local Network"
            serverType == SERVER_TYPE_CUSTOM -> "Custom Server"
            else -> "Unknown Server"
        }
    }
    
    fun resetToDefault(context: Context) {
        val prefs = getPreferences(context)
        prefs.edit()
            .remove(SERVER_URL_KEY)
            .remove(SERVER_TYPE_KEY)
            .apply()
    }
    
    fun isValidUrl(url: String): Boolean {
        return try {
            url.isNotEmpty() && 
            (url.startsWith("http://") || url.startsWith("https://")) &&
            url.contains(":")
        } catch (e: Exception) {
            false
        }
    }
}
