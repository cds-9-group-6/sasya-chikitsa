# Release Build Configuration for Multiple Server Clusters

## Overview

The Sasya Chikitsa Android app now supports building separate APK variants for different production server clusters:

- **GPU Cluster APK**: Configured for GPU-enabled processing cluster
- **Non-GPU Cluster APK**: Configured for standard processing cluster

This setup allows deploying optimized APKs for different server environments without manual configuration changes.

## Server URLs

### Production Clusters
- **GPU Cluster**: `http://engine-sasya-chikitsa.apps.cluster-mqklc.mqklc.sandbox601.opentlc.com/`
- **Non-GPU Cluster**: `http://engine-sasya-chikitsa.apps.cluster-6twrd.6twrd.sandbox1818.opentlc.com/`

### Development
- **Debug builds**: `http://10.0.2.2:8080/` (Android Emulator default)

## Build Variants

### Product Flavors

#### 1. GPU Variant (`gpu`)
```kotlin
applicationId = "com.example.sasya_chikitsa.gpu"
versionName = "1.0-gpu"
appName = "Sasya Chikitsa (GPU)"
defaultServerType = "GPU"
```

#### 2. Non-GPU Variant (`nongpu`)
```kotlin
applicationId = "com.example.sasya_chikitsa.nongpu"
versionName = "1.0-nongpu"
appName = "Sasya Chikitsa (Non-GPU)"
defaultServerType = "NON_GPU"
```

## Building APKs

### Quick Build Commands

#### Build GPU Release APK
```bash
# Navigate to project root
cd /path/to/sasya-chikitsa

# Build GPU variant
./gradlew buildGpuRelease
```

#### Build Non-GPU Release APK
```bash
# Build Non-GPU variant
./gradlew buildNonGpuRelease
```

#### Build Both Variants
```bash
# Build both GPU and Non-GPU variants
./gradlew buildAllReleaseVariants
```

#### Build and Copy to Releases Directory
```bash
# Build both variants and copy to releases/ folder with descriptive names
./gradlew copyReleasesToDistribution
```

### Standard Gradle Commands

#### Build Individual Variants
```bash
# Build GPU release
./gradlew assembleGpuRelease

# Build Non-GPU release
./gradlew assembleNongpuRelease

# Build both release variants
./gradlew assembleRelease
```

#### Build Debug Variants (for testing)
```bash
# Build GPU debug
./gradlew assembleGpuDebug

# Build Non-GPU debug
./gradlew assembleNongpuDebug
```

## APK Output Locations

### Default Gradle Output
```
app/build/outputs/apk/
├── gpu/
│   ├── debug/
│   │   └── app-gpu-debug.apk
│   └── release/
│       └── app-gpu-release.apk
└── nongpu/
    ├── debug/
    │   └── app-nongpu-debug.apk
    └── release/
        └── app-nongpu-release.apk
```

### Distribution Directory (after running `copyReleasesToDistribution`)
```
releases/
├── sasya-chikitsa-gpu-cluster-v1.0.apk
└── sasya-chikitsa-nongpu-cluster-v1.0.apk
```

## Configuration Details

### Build Configuration

The configuration is managed through:

1. **`app/build.gradle.kts`**: Defines product flavors with BuildConfig fields
2. **`app/src/main/java/com/example/sasya_chikitsa/config/ServerConfig.kt`**: Handles server URL resolution
3. **`app/build-release-variants.gradle`**: Provides convenient build tasks

### Server URL Resolution Logic

1. **User Custom URL**: If user has configured a custom server URL in app settings, it takes priority
2. **Build Variant Default**: Otherwise, uses the default URL based on the build variant:
   - GPU variant → GPU cluster URL
   - Non-GPU variant → Non-GPU cluster URL
   - Debug builds → Local development server

### App Features

Each variant includes:
- ✅ Different app names in launcher ("Sasya Chikitsa (GPU)" vs "Sasya Chikitsa (Non-GPU)")
- ✅ Different application IDs (can install both variants side by side)
- ✅ Pre-configured server URLs for respective clusters
- ✅ Server switching capability in app settings
- ✅ All agricultural AI features (CNN classification, RAG, attention overlays)

## Usage Scenarios

### Development Team
```bash
# Build both variants for testing
./gradlew buildAllReleaseVariants

# Copy to releases folder for distribution
./gradlew copyReleasesToDistribution
```

### CI/CD Pipeline
```bash
# In your CI/CD script
./gradlew copyReleasesToDistribution

# Upload both APKs to distribution platform
# GPU APK for GPU cluster deployment
# Non-GPU APK for standard cluster deployment
```

### Manual Testing
```bash
# Build specific variant for testing
./gradlew buildGpuRelease

# Install on device for testing
adb install app/build/outputs/apk/gpu/release/app-gpu-release.apk
```

## Deployment Strategy

### GPU Cluster Deployment
1. Use `sasya-chikitsa-gpu-cluster-v*.apk`
2. Deploy to devices that will connect to GPU-enabled processing
3. Optimal for: High-performance image classification, complex attention overlay generation

### Non-GPU Cluster Deployment
1. Use `sasya-chikitsa-nongpu-cluster-v*.apk`
2. Deploy to devices that will connect to standard processing cluster
3. Optimal for: Standard image classification, basic agricultural consultations

## Troubleshooting

### Build Issues
```bash
# Clean and rebuild
./gradlew clean
./gradlew buildAllReleaseVariants
```

### APK Installation Issues
```bash
# Uninstall existing versions first
adb uninstall com.example.sasya_chikitsa
adb uninstall com.example.sasya_chikitsa.gpu
adb uninstall com.example.sasya_chikitsa.nongpu

# Install new APK
adb install path/to/your/apk-file.apk
```

### Server Connectivity Testing
Each APK includes a "Test Connection" feature in the app settings to verify server connectivity before deployment.

## Advanced Configuration

### Customizing Server URLs
To change the server URLs, modify the `buildConfigField` values in `app/build.gradle.kts`:

```kotlin
buildConfigField("String", "SERVER_URL_GPU", "\"https://your-gpu-cluster.com/\"")
buildConfigField("String", "SERVER_URL_NON_GPU", "\"https://your-standard-cluster.com/\"")
```

### Adding New Variants
To add additional server environments (e.g., staging), add new product flavors:

```kotlin
create("staging") {
    dimension = "server"
    applicationIdSuffix = ".staging"
    versionNameSuffix = "-staging"
    buildConfigField("String", "SERVER_URL_GPU", "\"https://staging-gpu.com/\"")
    buildConfigField("String", "SERVER_URL_NON_GPU", "\"https://staging-standard.com/\"")
    // ... other configuration
}
```

## Summary

This configuration provides:
- ✅ **Automated** server URL configuration per build variant
- ✅ **Flexible** user override capability in app settings
- ✅ **Convenient** build tasks for different deployment scenarios
- ✅ **Clear** APK naming and organization
- ✅ **Side-by-side** installation capability for testing
- ✅ **Production-ready** setup for multiple cluster deployments

The setup is ready to build both GPU and Non-GPU cluster APKs without any manual configuration changes.
