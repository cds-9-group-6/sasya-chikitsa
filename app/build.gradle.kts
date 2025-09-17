plugins {
    id("com.android.application")
    id("kotlin-android")
}

android {
    namespace = "com.example.sasya_chikitsa"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.example.sasya_chikitsa"
        minSdk = 24
        targetSdk = 34
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

    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.8.2")
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.cardview:cardview:1.0.0")
    implementation("androidx.cardview:cardview:1.0.0")
    implementation("com.google.android.material:material:1.9.0")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2024.02.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
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