#!/usr/bin/env python3
"""
LLaVA Plant Disease Detection - Standalone Script
Supports both Ollama and direct model loading approaches
"""

import base64
import json
import requests
import argparse
from pathlib import Path
from PIL import Image
import io

class LLaVADiseaseDetector:
    def __init__(self, method="ollama", model_name="llava"):
        self.method = method
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434"
        
    def encode_image_to_base64(self, image_path):
        """Convert image to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_with_ollama(self, image_path, custom_prompt=None):
        """Analyze image using local Ollama LLaVA model"""
        
        # Default plant disease detection prompt
        if custom_prompt is None:
            prompt = """Analyze this leaf image for plant diseases. Please provide:

1. **Plant Health Status**: Is this plant healthy or diseased?
2. **Disease Identification**: If diseased, what specific disease do you see?

classification: {
    status: "healthy | diseased | unknown",
    "disease": "name of the disease"
}

Format your response clearly with these sections. Return the result only in the json form above"""
        else:
            prompt = custom_prompt
            
        # Encode image
        image_b64 = self.encode_image_to_base64(image_path)
        
        # Prepare request
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False
        }
        
        try:
            print(f"🔍 Analyzing image: {image_path}")
            print("⏳ Processing with LLaVA model...")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response received')
            else:
                return f"Error: HTTP {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            return f"Connection error: {str(e)}"
    
    def analyze_with_transformers(self, image_path, custom_prompt=None):
        """Analyze image using direct transformers model loading"""
        try:
            from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
            import torch
            from PIL import Image
            
            # Load model and processor
            print("📦 Loading LLaVA model (this may take a while)...")
            model_id = "llava-hf/llava-v1.6-mistral-7b-hf"  # or another LLaVA variant
            
            processor = LlavaNextProcessor.from_pretrained(model_id)
            model = LlavaNextForConditionalGeneration.from_pretrained(
                model_id, 
                torch_dtype=torch.float16, 
                low_cpu_mem_usage=True,
                device_map="auto"
            )
            
            # Load and process image
            image = Image.open(image_path)
            
            # Default plant disease detection prompt
            if custom_prompt is None:
                prompt = """[INST] <image>\nAnalyze this leaf image for plant diseases. Provide:
1. Plant Health Status (Healthy/Diseased)
2. Disease name if present
3. Visible symptoms
4. Severity level
5. Treatment recommendations [/INST]"""
            else:
                prompt = f"[INST] <image>\n{custom_prompt} [/INST]"
            
            print(f"🔍 Analyzing image: {image_path}")
            print("⏳ Processing with local LLaVA model...")
            
            # Process inputs
            inputs = processor(prompt, image, return_tensors="pt").to(model.device)
            
            # Generate response
            with torch.no_grad():
                output = model.generate(**inputs, max_new_tokens=512, do_sample=False)
                
            # Decode response
            response = processor.decode(output[0], skip_special_tokens=True)
            
            # Extract only the generated part (after the prompt)
            generated_text = response.split("[/INST]")[-1].strip()
            
            return generated_text
            
        except ImportError as e:
            return f"Missing dependencies: {str(e)}\nInstall with: pip install transformers torch pillow accelerate"
        except Exception as e:
            return f"Model loading error: {str(e)}"
    
    def analyze_image(self, image_path, custom_prompt=None):
        """Main analysis method - routes to appropriate implementation"""
        if not Path(image_path).exists():
            return f"❌ Error: Image file not found: {image_path}"
        
        print(f"🌿 Plant Disease Analysis using {self.method.upper()}")
        print(f"📸 Image: {image_path}")
        print("=" * 60)
        
        if self.method == "ollama":
            result = self.analyze_with_ollama(image_path, custom_prompt)
        elif self.method == "transformers":
            result = self.analyze_with_transformers(image_path, custom_prompt)
        else:
            return f"❌ Unknown method: {self.method}"
        
        return result

def main():
    parser = argparse.ArgumentParser(description="LLaVA Plant Disease Detection")
    parser.add_argument("image_path", help="Path to the leaf image")
    parser.add_argument("--method", choices=["ollama", "transformers"], 
                       default="ollama", help="Analysis method (default: ollama)")
    parser.add_argument("--model", default="llava", 
                       help="Model name (default: llava)")
    parser.add_argument("--prompt", help="Custom analysis prompt")
    
    args = parser.parse_args()
    
    # Create detector
    detector = LLaVADiseaseDetector(method=args.method, model_name=args.model)
    
    # Analyze image
    result = detector.analyze_image(args.image_path, args.prompt)
    
    # Display result
    print("\n" + "=" * 60)
    print("🔬 ANALYSIS RESULT:")
    print("=" * 60)
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    main()
