package com.example.sasya_chikitsa.config

import android.content.Context
import android.content.SharedPreferences

/**
 * Server configuration management for the Sasya Chikitsa app.
 * 
 * Common scenarios:
 * - Android Emulator: Use 10.0.2.2:8001 (maps to host's localhost:8001 - Planning Agent)
 * - Physical Device on same network: Use 192.168.x.x:8001 (find with `ipconfig` or `ifconfig`)
 * - Custom deployment: Use your server's public IP or domain
 */
object ServerConfig {
    private const val PREF_NAME = "sasya_chikitsa_config"
    private const val SERVER_URL_KEY = "server_url"
    
    // Default URLs for common scenarios (FSM Agent on port 8080)
    const val DEFAULT_EMULATOR_URL = "http://10.0.2.2:8080/"
    const val DEFAULT_LOCALHOST_URL = "http://localhost:8080/"
    const val DEFAULT_LOCAL_IP_URL = "http://192.168.1.100:8080/"
    const val DEFAULT_STAGING_URL = "https://your-staging-server.com/api/"
    const val DEFAULT_PRODUCTION_URL = "http://engine-sasya-chikitsa.apps.cluster-6twrd.6twrd.sandbox1818.opentlc.com/"
    
    private fun getPreferences(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }
    
    fun getServerUrl(context: Context): String {
        val prefs = getPreferences(context)
        return prefs.getString(SERVER_URL_KEY, DEFAULT_EMULATOR_URL) ?: DEFAULT_EMULATOR_URL
    }
    
    fun setServerUrl(context: Context, url: String) {
        val prefs = getPreferences(context)
        prefs.edit().putString(SERVER_URL_KEY, url).apply()
    }
    
    fun getDefaultUrls(): List<Pair<String, String>> {
        return listOf(
            "Android Emulator" to DEFAULT_EMULATOR_URL,
            "Localhost" to DEFAULT_LOCALHOST_URL, 
            "Local Network (192.168.1.x)" to DEFAULT_LOCAL_IP_URL,
            "Staging Server" to DEFAULT_STAGING_URL,
            "Production Server" to DEFAULT_PRODUCTION_URL,
            "Custom URL" to ""
        )
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
