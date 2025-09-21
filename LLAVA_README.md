# 🌿 LLaVA Plant Disease Detection - Standalone

A standalone Python script for analyzing leaf images for plant diseases using local LLaVA (Large Language and Vision Assistant) models.

## 🚀 Quick Start

### Method 1: Ollama (Recommended - Easier Setup)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama service
ollama serve

# 3. Pull LLaVA model
ollama pull llava

# 4. Install Python dependencies
pip install -r requirements_llava.txt

# 5. Test with your leaf image
python llava_disease_detector.py path/to/your/leaf.jpg
```

### Method 2: Direct Model Loading (More Control)

```bash
# 1. Install full dependencies
pip install torch transformers accelerate pillow requests

# 2. Run with transformers method
python llava_disease_detector.py leaf.jpg --method transformers
```

## 📖 Usage Examples

### Basic Analysis
```bash
# Analyze a leaf image
python llava_disease_detector.py leaf.jpg

# Analyze with custom prompt
python llava_disease_detector.py leaf.jpg --prompt "Is this tomato plant diseased?"

# Use different LLaVA model
python llava_disease_detector.py leaf.jpg --model llava:13b
```

### Sample Output
```
🌿 Plant Disease Analysis using OLLAMA
📸 Image: tomato_leaf.jpg
============================================================
⏳ Processing with LLaVA model...

============================================================
🔬 ANALYSIS RESULT:
============================================================
**1. Plant Health Status**: Diseased

**2. Disease Identification**: This appears to be Tomato Late Blight 
(Phytophthora infestans)

**3. Symptoms Observed**: Dark brown/black irregular spots on leaves, 
some with yellow halos. Water-soaked appearance on leaf edges.

**4. Severity Level**: Moderate to Severe

**5. Confidence**: High (85-90%)

**6. Recommended Action**: 
- Remove affected leaves immediately
- Apply copper-based fungicide
- Improve air circulation
- Reduce humidity around plants
- Monitor closely for spread
============================================================
```

## 🧪 Test Suite

Run the test suite to verify everything works:

```bash
# Run comprehensive tests
python test_llava_example.py

# Test with specific image
python test_llava_example.py path/to/leaf.jpg
```

## 🛠️ Script Features

### Core Functionality
- **Dual Method Support**: Ollama (simple) or direct transformers (advanced)
- **Base64 Image Encoding**: Automatic image processing
- **Custom Prompts**: Flexible analysis questions
- **Error Handling**: Comprehensive error messages

### Analysis Capabilities
- **Disease Detection**: Identifies plant diseases from symptoms
- **Severity Assessment**: Rates disease severity levels
- **Treatment Recommendations**: Suggests appropriate actions
- **Confidence Scoring**: Provides reliability estimates

## 📁 File Structure

```
llava_disease_detector.py    # Main analysis script
test_llava_example.py        # Test suite and examples
requirements_llava.txt       # Python dependencies
setup_llava.sh              # Automated setup script
LLAVA_README.md             # This documentation
```

## 🔧 Configuration

### Ollama Configuration
```python
# Default Ollama settings
ollama_url = "http://localhost:11434"  # Change if different host/port
model_name = "llava"                   # Use llava:13b for larger model
```

### Custom Prompts
```python
# Example custom prompts for different use cases
prompts = {
    "quick": "Is this leaf healthy or diseased? One sentence.",
    "detailed": "Provide comprehensive plant disease analysis with treatment plan.",
    "tomato": "Analyze this tomato plant leaf for common tomato diseases.",
    "symptoms": "List all visible disease symptoms in this leaf image."
}
```

## 🚨 Troubleshooting

### Common Issues

**1. Ollama Connection Error**
```bash
# Make sure Ollama is running
ollama serve

# Check if model is installed
ollama list
```

**2. Model Not Found**
```bash
# Install LLaVA model
ollama pull llava

# Or try specific version
ollama pull llava:7b
ollama pull llava:13b
```

**3. Memory Issues with Transformers**
```bash
# Use quantized models for lower memory
# Add to your script:
# load_in_4bit=True
# load_in_8bit=True
```

**4. Image Format Issues**
```python
# Supported formats: JPEG, PNG, BMP
# Convert if needed:
from PIL import Image
img = Image.open('image.webp')
img.save('image.jpg', 'JPEG')
```

## 🎯 Integration Tips

### For Production Use
```python
# Example integration in your app
from llava_disease_detector import LLaVADiseaseDetector

detector = LLaVADiseaseDetector(method="ollama")
result = detector.analyze_image("plant.jpg", 
    "Quick disease check: healthy or diseased?")
```

### Batch Processing
```python
# Analyze multiple images
import glob

detector = LLaVADiseaseDetector()
for image_path in glob.glob("plants/*.jpg"):
    result = detector.analyze_image(image_path)
    print(f"{image_path}: {result[:100]}...")
```

## 📊 Model Comparison

| Method | Setup Complexity | Memory Usage | Speed | Customization |
|--------|-----------------|--------------|--------|---------------|
| Ollama | Easy | Low | Fast | Medium |
| Transformers | Medium | High | Medium | High |

## 🤝 Contributing

Feel free to enhance this script with:
- Additional plant disease prompts
- Better image preprocessing
- Result parsing and structuring
- Integration with plant databases
- Performance optimizations

## 📝 Notes

- **Model Accuracy**: Results depend on image quality and model training
- **Internet**: Ollama method works offline after initial model download
- **Hardware**: GPU recommended but not required
- **Languages**: Supports multiple languages in prompts
