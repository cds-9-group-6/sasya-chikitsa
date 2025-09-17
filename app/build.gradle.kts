plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.example.sasya_chikitsa"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.example.sasya_chikitsa"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
        viewBinding = true
    }
    buildToolsVersion = "34.0.0"
}

dependencies {
    // FSM Module dependency

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.androidx.cardview)
    implementation("androidx.cardview:cardview:1.0.0")
    implementation("com.google.android.material:material:1.9.0")
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)
    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)
    // For JSON processing
    implementation("com.squareup.retrofit2:retrofit:2.11.0") // Latest stable version
    implementation("com.squareup.retrofit2:converter-gson:2.11.0") // Latest stable version
    // For handling streaming responses, especially Server-Sent Events (SSE)
    implementation("com.squareup.okhttp3:okhttp:4.12.0") // Latest stable version
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0") // For debugging

    // Additional UI Components for FSM integration
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    implementation("androidx.recyclerview:recyclerview:1.3.1")

    // JSON processing
    implementation("com.google.code.gson:gson:2.10.1")

    // Image handling
    implementation("com.github.bumptech.glide:glide:4.15.1")

    // Coroutines for FSM streaming
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.1")
}