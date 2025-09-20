#!/bin/bash

# Validation script for release build configuration
# This script validates that the build configuration is correctly set up

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

echo -e "${BLUE}🔍 Sasya Chikitsa Build Configuration Validation${NC}"
echo -e "${BLUE}Project: ${PROJECT_ROOT}${NC}"
echo ""

# Function to check if file exists
check_file() {
    local file="$1"
    local description="$2"
    
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ ${description}${NC}"
        return 0
    else
        echo -e "${RED}❌ ${description} - File not found: ${file}${NC}"
        return 1
    fi
}

# Function to check if content exists in file
check_content() {
    local file="$1"
    local pattern="$2"
    local description="$3"
    
    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✅ ${description}${NC}"
        return 0
    else
        echo -e "${RED}❌ ${description} - Pattern not found in ${file}${NC}"
        return 1
    fi
}

echo -e "${YELLOW}📋 Checking Build Configuration Files...${NC}"
echo ""

# Check main build files
check_file "${PROJECT_ROOT}/app/build.gradle.kts" "Main build.gradle.kts exists"
check_file "${PROJECT_ROOT}/app/build-release-variants.gradle" "Custom release variants script exists"
check_file "${PROJECT_ROOT}/app/src/main/java/com/example/sasya_chikitsa/config/ServerConfig.kt" "ServerConfig.kt exists"

echo ""
echo -e "${YELLOW}🔧 Checking Build Configuration Content...${NC}"
echo ""

# Check product flavors configuration
check_content "${PROJECT_ROOT}/app/build.gradle.kts" "flavorDimensions.*server" "Product flavor dimensions configured"
check_content "${PROJECT_ROOT}/app/build.gradle.kts" 'create("gpu")' "GPU product flavor configured"
check_content "${PROJECT_ROOT}/app/build.gradle.kts" 'create("nongpu")' "Non-GPU product flavor configured"
check_content "${PROJECT_ROOT}/app/build.gradle.kts" "buildConfig.*true" "BuildConfig feature enabled"

# Check server URLs
check_content "${PROJECT_ROOT}/app/build.gradle.kts" "cluster-mqklc.mqklc.sandbox601.opentlc.com" "GPU cluster URL configured"
check_content "${PROJECT_ROOT}/app/build.gradle.kts" "cluster-6twrd.6twrd.sandbox1818.opentlc.com" "Non-GPU cluster URL configured"

# Check ServerConfig.kt updates
check_content "${PROJECT_ROOT}/app/src/main/java/com/example/sasya_chikitsa/config/ServerConfig.kt" "BuildConfig" "ServerConfig uses BuildConfig"
check_content "${PROJECT_ROOT}/app/src/main/java/com/example/sasya_chikitsa/config/ServerConfig.kt" "GPU_CLUSTER_URL" "GPU cluster URL property exists"
check_content "${PROJECT_ROOT}/app/src/main/java/com/example/sasya_chikitsa/config/ServerConfig.kt" "NON_GPU_CLUSTER_URL" "Non-GPU cluster URL property exists"

# Check custom build tasks
check_content "${PROJECT_ROOT}/app/build-release-variants.gradle" "buildGpuRelease" "Custom GPU build task configured"
check_content "${PROJECT_ROOT}/app/build-release-variants.gradle" "buildNonGpuRelease" "Custom Non-GPU build task configured"
check_content "${PROJECT_ROOT}/app/build-release-variants.gradle" "buildAllReleaseVariants" "Combined build task configured"

echo ""
echo -e "${YELLOW}📚 Checking Documentation...${NC}"
echo ""

check_file "${PROJECT_ROOT}/docs/RELEASE_BUILD_CONFIGURATION.md" "Build configuration documentation exists"

echo ""
echo -e "${YELLOW}🏗️  Testing Gradle Task Recognition...${NC}"
echo ""

cd "$PROJECT_ROOT"

# Check if Gradle can recognize the tasks
if ./gradlew tasks --all | grep -q "buildGpuRelease"; then
    echo -e "${GREEN}✅ Custom GPU build task recognized by Gradle${NC}"
else
    echo -e "${RED}❌ Custom GPU build task not recognized by Gradle${NC}"
fi

if ./gradlew tasks --all | grep -q "buildNonGpuRelease"; then
    echo -e "${GREEN}✅ Custom Non-GPU build task recognized by Gradle${NC}"
else
    echo -e "${RED}❌ Custom Non-GPU build task not recognized by Gradle${NC}"
fi

if ./gradlew tasks --all | grep -q "buildAllReleaseVariants"; then
    echo -e "${GREEN}✅ Combined build task recognized by Gradle${NC}"
else
    echo -e "${RED}❌ Combined build task not recognized by Gradle${NC}"
fi

echo ""
echo -e "${YELLOW}🎯 Configuration Summary:${NC}"
echo ""

echo -e "${BLUE}📱 Product Flavors:${NC}"
echo -e "   🔹 GPU Variant: com.example.sasya_chikitsa.gpu"
echo -e "   🔹 Non-GPU Variant: com.example.sasya_chikitsa.nongpu"
echo ""

echo -e "${BLUE}🌐 Server URLs:${NC}"
echo -e "   🔹 GPU Cluster: http://engine-sasya-chikitsa.apps.cluster-mqklc.mqklc.sandbox601.opentlc.com/"
echo -e "   🔹 Non-GPU Cluster: http://engine-sasya-chikitsa.apps.cluster-6twrd.6twrd.sandbox1818.opentlc.com/"
echo ""

echo -e "${BLUE}🛠️  Build Commands:${NC}"
echo -e "   🔹 ./gradlew buildGpuRelease"
echo -e "   🔹 ./gradlew buildNonGpuRelease"
echo -e "   🔹 ./gradlew buildAllReleaseVariants"
echo -e "   🔹 ./gradlew copyReleasesToDistribution"
echo ""

echo -e "${GREEN}🎉 Build configuration validation completed!${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo -e "   1. Run: ./gradlew buildAllReleaseVariants"
echo -e "   2. Check: app/build/outputs/apk/{gpu,nongpu}/release/"
echo -e "   3. Test: Install both APKs and verify server connectivity"
echo ""
echo -e "${BLUE}📖 For detailed instructions, see:${NC}"
echo -e "   docs/RELEASE_BUILD_CONFIGURATION.md"
