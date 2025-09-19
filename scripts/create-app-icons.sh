#!/bin/bash

# Script to create Android app icons from the Sasya Chikitsa logo
# Creates icons for both GPU and Non-GPU variants

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="/Users/aathalye/dev/sasya-chikitsa"
LOGO_SOURCE="$PROJECT_ROOT/resources/Sasya-Chikitsa-app-logo.jpeg"
TEMP_DIR="$PROJECT_ROOT/temp_icons"

# Android launcher icon sizes (density:size)
ICON_DENSITIES="mdpi:48 hdpi:72 xhdpi:96 xxhdpi:144 xxxhdpi:192"

echo -e "${BLUE}🎨 Creating Android App Icons for Sasya Chikitsa${NC}"
echo -e "${BLUE}Logo source: $LOGO_SOURCE${NC}"
echo ""

# Check if logo exists
if [[ ! -f "$LOGO_SOURCE" ]]; then
    echo -e "${RED}❌ Logo file not found: $LOGO_SOURCE${NC}"
    exit 1
fi

# Create temp directory
mkdir -p "$TEMP_DIR"

echo -e "${YELLOW}📐 Creating base icons...${NC}"

# Convert JPEG to PNG and create a high-res base icon
sips -s format png "$LOGO_SOURCE" --out "$TEMP_DIR/logo_base.png" > /dev/null 2>&1

# Create a square 512x512 base icon (standard Android icon size)
sips -z 512 512 "$TEMP_DIR/logo_base.png" --out "$TEMP_DIR/logo_512.png" > /dev/null 2>&1

echo -e "${GREEN}✅ Base icon created (512x512)${NC}"

# Function to create icons for a variant
create_variant_icons() {
    local variant=$1
    local variant_name=$2
    local badge_text=$3
    
    echo -e "${YELLOW}📱 Creating $variant_name icons...${NC}"
    
    # Create directories
    local base_path="$PROJECT_ROOT/app/src/$variant/res"
    
    # Create icons for each density
    for density_size in $ICON_DENSITIES; do
        local density=$(echo "$density_size" | cut -d: -f1)
        local size=$(echo "$density_size" | cut -d: -f2)
        local output_dir="$base_path/mipmap-$density"
        
        # Create launcher icon
        sips -z $size $size "$TEMP_DIR/logo_512.png" --out "$output_dir/ic_launcher.png" > /dev/null 2>&1
        
        # Create round launcher icon (same as regular for now)
        cp "$output_dir/ic_launcher.png" "$output_dir/ic_launcher_round.png"
        
        echo -e "${GREEN}✅ Created $variant_name icons for $density ($size x $size)${NC}"
    done
}

# Create GPU variant icons
create_variant_icons "gpu" "GPU" "GPU"

# Create Non-GPU variant icons  
create_variant_icons "nongpu" "Non-GPU" ""

echo ""
echo -e "${YELLOW}🏷️  Creating variant-specific resources...${NC}"

# Create strings.xml for GPU variant
mkdir -p "$PROJECT_ROOT/app/src/gpu/res/values"
cat > "$PROJECT_ROOT/app/src/gpu/res/values/strings.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Sasya Chikitsa (GPU)</string>
    <string name="app_variant">GPU</string>
    <string name="app_description">Agricultural AI Assistant - GPU Enhanced</string>
</resources>
EOF

# Create strings.xml for Non-GPU variant
mkdir -p "$PROJECT_ROOT/app/src/nongpu/res/values"
cat > "$PROJECT_ROOT/app/src/nongpu/res/values/strings.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Sasya Chikitsa (Non-GPU)</string>
    <string name="app_variant">Non-GPU</string>
    <string name="app_description">Agricultural AI Assistant - Standard</string>
</resources>
EOF

echo -e "${GREEN}✅ Created variant-specific resource files${NC}"

# Clean up temp directory
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}🎉 App icons created successfully!${NC}"
echo ""
echo -e "${BLUE}📁 Icon locations:${NC}"
echo -e "   GPU Variant: app/src/gpu/res/mipmap-*/"
echo -e "   Non-GPU Variant: app/src/nongpu/res/mipmap-*/"
echo ""
echo -e "${BLUE}📋 Icon sizes created:${NC}"
for density_size in $ICON_DENSITIES; do
    density=$(echo "$density_size" | cut -d: -f1)
    size=$(echo "$density_size" | cut -d: -f2)
    echo -e "   $density: ${size}x${size}px"
done
echo ""
echo -e "${YELLOW}🔄 Next steps:${NC}"
echo -e "   1. Build both APK variants"
echo -e "   2. Install and verify launcher icons"
echo -e "   3. Test on different device densities"
echo ""
echo -e "${GREEN}✅ Ready to build APKs with custom logos!${NC}"
