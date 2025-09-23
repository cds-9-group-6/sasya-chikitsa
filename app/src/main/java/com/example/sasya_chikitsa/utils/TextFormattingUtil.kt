package com.example.sasya_chikitsa.utils

import android.graphics.Typeface
import android.text.SpannableString
import android.text.SpannableStringBuilder
import android.text.Spanned
import android.text.style.StyleSpan
import java.util.regex.Pattern

object TextFormattingUtil {
    
    // Pre-compiled pattern for performance - compiled once and reused
    private val boldPattern: Pattern = Pattern.compile("\\*\\*(.*?)\\*\\*")
    
    /**
     * Converts WhatsApp-style **bold** text to Android SpannableString with bold formatting
     * @param text The input text containing **bold** patterns
     * @return SpannableString with bold formatting applied
     */
    fun formatWhatsAppStyle(text: String): SpannableString {
        val spannable = SpannableStringBuilder(text)
        
        // Use pre-compiled pattern for better performance
        val matcher = boldPattern.matcher(text)
        
        // Keep track of offset changes as we remove asterisks
        var offset = 0
        
        while (matcher.find()) {
            val start = matcher.start() - offset
            val end = matcher.end() - offset
            val boldText = matcher.group(1) // The text between **
            
            if (boldText != null && boldText.isNotEmpty()) {
                // Remove the ** markers from the spannable text
                spannable.replace(start, end, boldText)
                
                // Apply bold style to the text
                spannable.setSpan(
                    StyleSpan(Typeface.BOLD),
                    start,
                    start + boldText.length,
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                )
                
                // Update offset for next iteration (we removed 4 characters: **)
                offset += 4
            }
        }
        
        return SpannableString(spannable)
    }
}
