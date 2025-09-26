#!/usr/bin/env python3
"""
Simple test example for LLaVA Plant Disease Detection
"""

from llava_disease_detector import LLaVADiseaseDetector
import sys
from pathlib import Path

def test_leaf_analysis():
    """Test leaf disease analysis with sample prompts"""
    
    # Check if test image exists
    test_images = [
        "leaf_test.jpg",
        "plant_image.jpg", 
        "disease_leaf.png",
        "healthy_leaf.jpg"
    ]
    
    image_path = None
    for img in test_images:
        if Path(img).exists():
            image_path = img
            break
    
    if not image_path:
        print("❌ No test images found. Please add a leaf image file:")
        for img in test_images:
            print(f"   - {img}")
        print("\nOr specify image path as argument:")
        print(f"   python {sys.argv[0]} path/to/your/leaf.jpg")
        return
    
    # Use command line argument if provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    
    print(f"🧪 Testing with image: {image_path}")
    
    # Initialize detector
    detector = LLaVADiseaseDetector(method="ollama")
    
    # Test 1: General disease analysis
    print("\n" + "="*50)
    print("🔬 TEST 1: General Disease Analysis")
    print("="*50)
    
    result1 = detector.analyze_image(image_path)
    print(result1)
    
    # Test 2: Specific plant analysis
    print("\n" + "="*50)
    print("🔬 TEST 2: Specific Plant Analysis")
    print("="*50)
    
    specific_prompt = """Look at this leaf image and determine:
1. What type of plant is this?
2. Are there any signs of disease?
3. If diseased, what specific symptoms do you see?
4. What's your confidence level in this diagnosis?
5. What would you recommend for treatment?"""
    
    result2 = detector.analyze_image(image_path, specific_prompt)
    print(result2)
    
    # Test 3: Quick health check
    print("\n" + "="*50)
    print("🔬 TEST 3: Quick Health Check")
    print("="*50)
    
    quick_prompt = "Is this leaf healthy or diseased? Give a brief one-sentence answer with confidence level."
    
    result3 = detector.analyze_image(image_path, quick_prompt)
    print(result3)

def test_multiple_images():
    """Test analysis of multiple images if available"""
    
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    current_dir = Path('.')
    
    image_files = []
    for ext in image_extensions:
        image_files.extend(current_dir.glob(f'*{ext}'))
        image_files.extend(current_dir.glob(f'*{ext.upper()}'))
    
    if len(image_files) <= 1:
        print("ℹ️  Only one image found. Skipping batch test.")
        return
    
    print(f"\n🔄 Found {len(image_files)} images for batch testing")
    
    detector = LLaVADiseaseDetector(method="ollama")
    quick_prompt = "Healthy or diseased? One sentence with confidence."
    
    for i, img_path in enumerate(image_files[:3], 1):  # Test max 3 images
        print(f"\n📸 Image {i}: {img_path.name}")
        result = detector.analyze_image(str(img_path), quick_prompt)
        # Show only first 200 characters for batch test
        print(result[:200] + "..." if len(result) > 200 else result)

if __name__ == "__main__":
    print("🌿 LLaVA Plant Disease Detection - Test Suite")
    print("=" * 55)
    
    try:
        test_leaf_analysis()
        test_multiple_images()
        
        print("\n✅ Testing complete!")
        print("\nTo test with your own image:")
        print(f"   python {sys.argv[0]} path/to/your/leaf.jpg")
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        print("Make sure Ollama is running and LLaVA model is installed:")
        print("   ollama serve")
        print("   ollama pull llava")
