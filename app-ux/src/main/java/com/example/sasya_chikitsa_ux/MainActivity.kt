package com.example.sasya_chikitsa_ux

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.provider.MediaStore
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.widget.EditText
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.util.*

class MainActivity : AppCompatActivity() {

    // UI Components
    private lateinit var inputField: EditText
    private lateinit var sendButton: ImageView
    private lateinit var voiceButton: ImageView
    private lateinit var cameraButton: ImageView
    private lateinit var uploadPhotoButton: TextView
    private lateinit var voiceInputButton: TextView
    
    // Sample question TextViews
    private lateinit var question1: TextView
    private lateinit var question2: TextView
    private lateinit var question3: TextView
    private lateinit var question4: TextView

    // Activity result launchers
    private val imagePickerLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) {
            handleSelectedImage(uri)
        }
    }

    private val speechRecognizerLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == RESULT_OK) {
            val results = result.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
            val spokenText = results?.get(0) ?: ""
            inputField.setText(spokenText)
        }
    }

    private val cameraLauncher = registerForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        if (success) {
            // Handle camera capture success
            Toast.makeText(this, "Photo captured successfully!", Toast.LENGTH_SHORT).show()
            // TODO: Process the captured image
        }
    }

    private val permissionLauncher = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { permissions ->
        val audioPermissionGranted = permissions[Manifest.permission.RECORD_AUDIO] ?: false
        val cameraPermissionGranted = permissions[Manifest.permission.CAMERA] ?: false
        
        if (audioPermissionGranted) {
            startVoiceRecognition()
        }
        if (cameraPermissionGranted) {
            openCamera()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        try {
            setContentView(R.layout.activity_main)
            
            initializeViews()
            setupClickListeners()
            
            // Add debugging log
            android.util.Log.d("SasyaUX", "MainActivity onCreate completed successfully")
            Toast.makeText(this, "App loaded successfully!", Toast.LENGTH_SHORT).show()
            
        } catch (e: Exception) {
            android.util.Log.e("SasyaUX", "Error in onCreate: ${e.message}", e)
            Toast.makeText(this, "Error loading app: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun initializeViews() {
        try {
            android.util.Log.d("SasyaUX", "Starting view initialization...")
            
            inputField = findViewById(R.id.inputField)
            android.util.Log.d("SasyaUX", "inputField initialized")
            
            sendButton = findViewById(R.id.sendButton)
            voiceButton = findViewById(R.id.voiceButton)
            cameraButton = findViewById(R.id.cameraButton)
            android.util.Log.d("SasyaUX", "Buttons initialized")
            
            uploadPhotoButton = findViewById(R.id.uploadPhotoButton)
            voiceInputButton = findViewById(R.id.voiceInputButton)
            android.util.Log.d("SasyaUX", "Action buttons initialized")
            
            // Sample questions
            question1 = findViewById(R.id.question1)
            question2 = findViewById(R.id.question2)
            question3 = findViewById(R.id.question3)
            question4 = findViewById(R.id.question4)
            android.util.Log.d("SasyaUX", "Sample questions initialized")
            
            android.util.Log.d("SasyaUX", "All views initialized successfully!")
            
        } catch (e: Exception) {
            android.util.Log.e("SasyaUX", "Error initializing views: ${e.message}", e)
            Toast.makeText(this, "Error initializing UI: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun setupClickListeners() {
        // Send button
        sendButton.setOnClickListener {
            val message = inputField.text.toString().trim()
            if (message.isNotEmpty()) {
                sendMessage(message)
            } else {
                Toast.makeText(this, "Please enter a message", Toast.LENGTH_SHORT).show()
            }
        }

        // Voice recognition buttons
        voiceButton.setOnClickListener { requestVoicePermissionAndStart() }
        voiceInputButton.setOnClickListener { requestVoicePermissionAndStart() }

        // Camera/Photo buttons
        cameraButton.setOnClickListener { requestCameraPermissionAndStart() }
        uploadPhotoButton.setOnClickListener { openImagePicker() }

        // Sample questions
        question1.setOnClickListener { fillInputWithQuestion(question1.text.toString()) }
        question2.setOnClickListener { fillInputWithQuestion(question2.text.toString()) }
        question3.setOnClickListener { fillInputWithQuestion(question3.text.toString()) }
        question4.setOnClickListener { fillInputWithQuestion(question4.text.toString()) }
    }

    private fun sendMessage(message: String) {
        Toast.makeText(this, "Sending: $message", Toast.LENGTH_SHORT).show()
        
        // TODO: Integrate with your AI backend
        // For now, just clear the input
        inputField.text.clear()
        
        // Here you would typically:
        // 1. Show loading indicator
        // 2. Call your Sasya Chikitsa API
        // 3. Handle the response
        // 4. Navigate to results screen or show inline results
    }

    private fun requestVoicePermissionAndStart() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) 
            == PackageManager.PERMISSION_GRANTED) {
            startVoiceRecognition()
        } else {
            permissionLauncher.launch(arrayOf(Manifest.permission.RECORD_AUDIO))
        }
    }

    private fun startVoiceRecognition() {
        if (SpeechRecognizer.isRecognitionAvailable(this)) {
            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
                putExtra(RecognizerIntent.EXTRA_PROMPT, "Tell me about your plant problem...")
            }
            speechRecognizerLauncher.launch(intent)
        } else {
            Toast.makeText(this, "Speech recognition not available", Toast.LENGTH_SHORT).show()
        }
    }

    private fun requestCameraPermissionAndStart() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) 
            == PackageManager.PERMISSION_GRANTED) {
            openCamera()
        } else {
            permissionLauncher.launch(arrayOf(Manifest.permission.CAMERA))
        }
    }

    private fun openCamera() {
        val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        if (intent.resolveActivity(packageManager) != null) {
            // TODO: Create a file to save the photo
            // For now, just show a toast
            Toast.makeText(this, "Camera opened", Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(this, "Camera not available", Toast.LENGTH_SHORT).show()
        }
    }

    private fun openImagePicker() {
        imagePickerLauncher.launch("image/*")
    }

    private fun handleSelectedImage(uri: Uri) {
        Toast.makeText(this, "Image selected: ${uri.lastPathSegment}", Toast.LENGTH_SHORT).show()
        
        // TODO: Process the selected image
        // 1. Convert to base64 or appropriate format
        // 2. Send to your Sasya Chikitsa API
        // 3. Show analysis results
    }

    private fun fillInputWithQuestion(question: String) {
        // Remove the bullet point dot if present
        val cleanQuestion = question.replace("•", "").trim()
        inputField.setText(cleanQuestion)
        inputField.setSelection(cleanQuestion.length) // Move cursor to end
        
        // Optional: Automatically send the question
        // sendMessage(cleanQuestion)
    }
}
