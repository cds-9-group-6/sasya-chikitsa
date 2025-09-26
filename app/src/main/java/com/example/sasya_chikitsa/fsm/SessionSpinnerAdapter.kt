package com.example.sasya_chikitsa.fsm

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.BaseAdapter
import android.widget.TextView
import com.example.sasya_chikitsa.R

/**
 * Custom adapter for session selector spinner
 */
class SessionSpinnerAdapter(
    private val context: Context,
    private var sessions: List<SessionMetadata>
) : BaseAdapter() {
    
    private var currentSessionId: String? = null
    
    private val inflater = LayoutInflater.from(context)
    
    override fun getCount(): Int = sessions.size
    
    override fun getItem(position: Int): SessionMetadata = sessions[position]
    
    override fun getItemId(position: Int): Long = position.toLong()
    
    /**
     * Get the main spinner view (closed state)
     */
    override fun getView(position: Int, convertView: View?, parent: ViewGroup?): View {
        val view = convertView ?: inflater.inflate(R.layout.session_spinner_item, parent, false)
        val session = getItem(position)
        
        val titleText = view.findViewById<TextView>(R.id.sessionTitle)
        val subtitleText = view.findViewById<TextView>(R.id.sessionSubtitle)
        
        titleText.text = session.getDisplayTitle()
        subtitleText.text = session.getSubtitle()
        
        return view
    }
    
    /**
     * Get the dropdown view (open state)
     */
    override fun getDropDownView(position: Int, convertView: View?, parent: ViewGroup?): View {
        val view = convertView ?: inflater.inflate(R.layout.session_spinner_dropdown_item, parent, false)
        val session = getItem(position)
        
        val titleText = view.findViewById<TextView>(R.id.sessionTitle)
        val subtitleText = view.findViewById<TextView>(R.id.sessionSubtitle)
        val indicatorText = view.findViewById<TextView>(R.id.sessionIndicator)
        val currentIndicator = view.findViewById<TextView>(R.id.currentSessionIndicator)
        
        titleText.text = session.title
        subtitleText.text = session.getSubtitle()
        
        // Set indicators
        val indicators = mutableListOf<String>()
        if (session.hasImages) indicators.add("📷")
        if (session.hasDiagnosis) indicators.add("🔍")
        
        indicatorText.text = indicators.joinToString(" ")
        indicatorText.visibility = if (indicators.isNotEmpty()) View.VISIBLE else View.GONE
        
        // Highlight current session
        val isCurrentSession = session.sessionId == currentSessionId
        if (isCurrentSession) {
            // Highlight current session
            view.setBackgroundColor(context.getColor(R.color.light_green_bg))
            titleText.setTextColor(context.getColor(R.color.forest_green_dark))
            subtitleText.setTextColor(context.getColor(R.color.forest_green))
            currentIndicator.visibility = View.VISIBLE
            currentIndicator.text = "●"
            currentIndicator.setTextColor(context.getColor(R.color.forest_green_dark))
        } else {
            // Normal session appearance
            view.setBackgroundColor(android.graphics.Color.TRANSPARENT)
            titleText.setTextColor(context.getColor(R.color.forest_green))
            subtitleText.setTextColor(context.getColor(android.R.color.darker_gray))
            currentIndicator.visibility = View.GONE
        }
        
        return view
    }
    
    /**
     * Update sessions list and notify adapter
     */
    fun updateSessions(newSessions: List<SessionMetadata>) {
        sessions = newSessions
        notifyDataSetChanged()
    }
    
    /**
     * Set the current active session ID for highlighting
     */
    fun setCurrentSessionId(sessionId: String?) {
        currentSessionId = sessionId
        notifyDataSetChanged()
    }
    
    /**
     * Update sessions and set current session in one call
     */
    fun updateSessionsWithCurrent(newSessions: List<SessionMetadata>, currentId: String?) {
        sessions = newSessions
        currentSessionId = currentId
        notifyDataSetChanged()
    }
    
    /**
     * Find position of session by ID
     */
    fun findPositionById(sessionId: String): Int {
        return sessions.indexOfFirst { it.sessionId == sessionId }
    }
}