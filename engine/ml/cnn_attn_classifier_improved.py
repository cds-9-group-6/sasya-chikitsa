import base64
import numpy as np
import cv2
import os
import time
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
from tensorflow.keras.models import load_model, Model
from keras.layers import Layer
import tensorflow as tf

from ml.label_mappings import LABEL_MAPPINGS

MODEL_LABEL_CLASSES = [
    'Apple_scab', 'Bacterial_spot', 'Black_rot', 'Cedar_apple_rust',
    'Cercospora_leaf_spot Gray_leaf_spot', 'Common_rust', 'Early_blight',
    'Esca_(Black_Measles)', 'Haunglongbing_(Citrus_greening)', 'Late_blight',
    'Leaf_Mold', 'Leaf_blight_(Isariopsis_Leaf_Spot)', 'Leaf_scorch',
    'Northern_Leaf_Blight', 'Powdery_mildew', 'Septoria_leaf_spot',
    'Spider_mites Two-spotted_spider_mite', 'Target_Spot',
    'Tomato_Yellow_Leaf_Curl_Virus', 'Tomato_mosaic_virus', 'Unknown', 'healthy'
]

TARGET_IMG_SIZE = (64, 64)

# Define the custom layer needed for loading the model
class ReshapeLayer(Layer):
    def __init__(self, target_shape, **kwargs):
        super(ReshapeLayer, self).__init__(**kwargs)
        self.target_shape = target_shape

    def call(self, inputs):
        return tf.reshape(inputs, self.target_shape)

    def get_config(self):
        config = super(ReshapeLayer, self).get_config()
        config.update({
            'target_shape': self.target_shape,
        })
        return config

class CNNWithAttentionClassifier(Layer):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loaded_model = CNNWithAttentionClassifier.load_model()
        self.attention_model = CNNWithAttentionClassifier.create_attention_model(self.loaded_model)
        print("[INFO] Model with attention visualization loaded successfully.")

    @staticmethod
    def load_model():
        ml_dir = os.path.dirname(__file__)
        # parent_dir = os.path.dirname(ml_dir)
        # resources_dir = os.path.join(parent_dir, "resources")
        binary_model_path = os.path.join(ml_dir, "basic_self_attention_cnn_model_final.keras")
        print(f"[INFO] Loading attention CNN model from {binary_model_path}...")
        
        custom_objects = {
            'ReshapeLayer': ReshapeLayer,
            'Attention': tf.keras.layers.Attention,
            'GlobalAveragePooling2D': tf.keras.layers.GlobalAveragePooling2D,
            'Dense': tf.keras.layers.Dense,
            'Input': tf.keras.layers.Input,
            'Add': tf.keras.layers.Add,
            'Multiply': tf.keras.layers.multiply,
            'Permute': tf.keras.layers.Permute
        }
        
        return load_model(binary_model_path, custom_objects=custom_objects)

    @staticmethod
    def create_attention_model(base_model):
        """Create a model that outputs both predictions and attention weights."""
        attention_layer = None
        for layer in base_model.layers:
            if isinstance(layer, tf.keras.layers.Attention):
                attention_layer = layer
                break
        
        if attention_layer:
            attention_model = Model(
                inputs=base_model.input,
                outputs=[base_model.output, attention_layer.output]
            )
            print("[INFO] Attention model with weights output created successfully.")
            return attention_model
        else:
            print("[WARNING] Attention layer not found in the loaded model. Falling back to base model.")
            return base_model

    def visualize_self_attention_overlay(self, image, target_size=(64, 64)):
        """
        Generate attention overlay visualization and return as base64 encoded image.

        Args:
            image (np.ndarray): Input image array
            target_size (tuple): Target size for processing
            
        Yields:
            str: Base64 encoded attention overlay image or error message
        """
        try:
            yield "Generating attention visualization...\n"
            time.sleep(0.5)
            
            # Prepare image for attention model
            processed_image = cv2.resize(image, target_size)
            processed_image = processed_image.astype(np.float32) / 255.0
            processed_image = np.expand_dims(processed_image, axis=0)
            
            # Get predictions and attention weights
            if self.attention_model:
                predictions = self.attention_model.predict(processed_image)
                
                if isinstance(predictions, list) and len(predictions) > 1:
                    final_output = predictions[0]
                    attention_weights = predictions[1]
                    
                    yield "Processing attention weights...\n"
                    time.sleep(0.3)
                    
                    # Process attention weights to create heatmap
                    sequence_length = attention_weights.shape[1]
                    original_spatial_size = int(np.sqrt(sequence_length))
                    
                    if original_spatial_size * original_spatial_size == sequence_length:
                        # Reshape attention weights to spatial dimensions
                        batch_size = attention_weights.shape[0]
                        features = attention_weights.shape[2]
                        spatial_attention = np.reshape(
                            attention_weights, 
                            (batch_size, original_spatial_size, original_spatial_size, features)
                        )
                        
                        # Aggregate attention across features
                        attention_map = np.mean(spatial_attention, axis=-1)
                        attention_map = np.squeeze(attention_map, axis=0)
                        
                        # Resize to original image dimensions
                        original_image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        resized_attention = cv2.resize(
                            attention_map, 
                            (original_image_rgb.shape[1], original_image_rgb.shape[0]),
                            interpolation=cv2.INTER_CUBIC
                        )
                        
                        # Normalize attention map
                        min_att = np.min(resized_attention)
                        max_att = np.max(resized_attention)
                        if max_att - min_att > 1e-6:
                            normalized_attention = (resized_attention - min_att) / (max_att - min_att)
                        else:
                            normalized_attention = np.zeros_like(resized_attention)
                        
                        yield "Creating attention heatmap overlay...\n"
                        time.sleep(0.3)
                        
                        # Create heatmap overlay
                        heatmap = cv2.applyColorMap(
                            np.uint8(255 * normalized_attention),
                            cv2.COLORMAP_VIRIDIS
                        )
                        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

                        # Blend with original image
                        original_float = original_image_rgb.astype(np.float32) / 255.0
                        heatmap_float = heatmap_rgb.astype(np.float32) / 255.0
                        alpha = np.expand_dims(normalized_attention, axis=-1)
                        alpha = np.repeat(alpha, 3, axis=-1)

                        overlay = (1 - alpha) * original_float + alpha * heatmap_float
                        overlay = np.clip(overlay, 0, 1)
                        
                        # Convert to image and encode as base64
                        plt.figure(figsize=(10, 5))
                        
                        plt.subplot(1, 2, 1)
                        plt.imshow(original_image_rgb)
                        plt.title("Original Image")
                        plt.axis('off')
                        
                        plt.subplot(1, 2, 2)
                        plt.imshow(overlay)
                        plt.title("Attention Overlay")
                        plt.axis('off')
                        
                        plt.tight_layout()
                        
                        # Save to bytes buffer
                        buffer = io.BytesIO()
                        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
                        plt.close()
                        
                        buffer.seek(0)
                        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                        
                        yield f"Attention visualization completed! Generated overlay showing model focus areas.\n"
                        yield f"ATTENTION_OVERLAY_BASE64:{image_base64}\n"
                        
                    else:
                        yield "Warning: Could not process attention weights due to spatial dimension mismatch.\n"
                else:
                    yield "Warning: Could not extract attention weights from model output.\n"
            else:
                yield "Warning: Attention model not available for visualization.\n"
                
        except Exception as e:
            yield f"Error generating attention visualization: {str(e)}\n"

    def predict_leaf_classification_complete(self, image_bytes, input_text=""):
        """
        Predicts plant disease with attention visualization - returns complete results.

        Args:
            image_bytes (str): Base64-encoded image bytes.
            input_text (str): Optional additional text.
        
        Returns:
            dict: Complete classification results including attention overlay
        """
        if self.loaded_model is None:
            return {"error": "Model is not loaded"}

        if image_bytes is None:
            return {"error": "Mandatory argument 'image_bytes' is missing"}

        try:
            # Clean the base64 string - remove whitespace and potential prefixes
            clean_image_bytes = image_bytes.strip()
            
            # Remove data URL prefix if present (data:image/jpeg;base64,)
            if clean_image_bytes.startswith('data:'):
                clean_image_bytes = clean_image_bytes.split(',', 1)[1]
            
            # Remove any whitespace/newlines
            clean_image_bytes = ''.join(clean_image_bytes.split())
            
            # Decode base64
            image_decoded = base64.b64decode(clean_image_bytes)
            nparr = np.frombuffer(image_decoded, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        except Exception as e:
            return {
                "error": f"Could not decode base64 image ({str(e)})",
                "debug_info": {
                    "base64_length": len(image_bytes) if image_bytes else 0,
                    "first_100_chars": image_bytes[:100] if image_bytes else 'None'
                }
            }
        
        if image is None:
            return {"error": "Could not load image from bytes"}

        try:
            # Image preprocessing
            image_resized = cv2.resize(image, TARGET_IMG_SIZE)
            image_preprocessed = image_resized.astype(np.float32) / 255.0
            image_for_prediction = np.expand_dims(image_preprocessed, axis=0)

            # Run CNN model inference
            prediction = self.loaded_model.predict(image_for_prediction)

            # Get prediction results
            predicted_class_index = np.argmax(prediction)
            predicted_class_label = MODEL_LABEL_CLASSES[predicted_class_index]
            prediction_probability = prediction[0][predicted_class_index]

            # Transform to Kisan CC label
            kissan_cc_class_label = LABEL_MAPPINGS.get(predicted_class_label, predicted_class_label)
            
            # Generate attention visualization (synchronously)
            attention_overlay_b64 = self._generate_attention_overlay_sync(image, TARGET_IMG_SIZE)
            
            # Return complete results
            return {
                "success": True,
                "disease_name": kissan_cc_class_label,
                "confidence": float(prediction_probability),
                "raw_class_label": predicted_class_label,
                "attention_overlay": attention_overlay_b64,
                "input_context": input_text,
                "processing_status": "complete"
            }
            
        except Exception as e:
            return {"error": f"Classification failed: {str(e)}"}

    def _generate_attention_overlay_sync(self, image, target_size=(64, 64)):
        """
        Generate attention overlay synchronously and return as base64 string.
        
        Args:
            image (np.ndarray): Input image array
            target_size (tuple): Target size for processing
            
        Returns:
            str: Base64 encoded attention overlay image or None if failed
        """
        try:
            # Prepare image for attention model
            processed_image = cv2.resize(image, target_size)
            processed_image = processed_image.astype(np.float32) / 255.0
            processed_image = np.expand_dims(processed_image, axis=0)
            
            # Get predictions and attention weights
            if self.attention_model:
                predictions = self.attention_model.predict(processed_image)
                
                if isinstance(predictions, list) and len(predictions) > 1:
                    attention_weights = predictions[1]
                    
                    # Process attention weights to create heatmap
                    sequence_length = attention_weights.shape[1]
                    original_spatial_size = int(np.sqrt(sequence_length))
                    
                    if original_spatial_size * original_spatial_size == sequence_length:
                        # Reshape attention weights to spatial dimensions
                        batch_size = attention_weights.shape[0]
                        features = attention_weights.shape[2]
                        spatial_attention = np.reshape(
                            attention_weights, 
                            (batch_size, original_spatial_size, original_spatial_size, features)
                        )
                        
                        # Aggregate attention across features
                        attention_map = np.mean(spatial_attention, axis=-1)
                        attention_map = np.squeeze(attention_map, axis=0)
                        
                        # Resize to original image dimensions
                        original_image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        resized_attention = cv2.resize(
                            attention_map, 
                            (original_image_rgb.shape[1], original_image_rgb.shape[0]),
                            interpolation=cv2.INTER_CUBIC
                        )
                        
                        # Normalize attention map
                        min_att = np.min(resized_attention)
                        max_att = np.max(resized_attention)
                        if max_att - min_att > 1e-6:
                            normalized_attention = (resized_attention - min_att) / (max_att - min_att)
                        else:
                            normalized_attention = np.zeros_like(resized_attention)
                        
                        # Create heatmap overlay
                        heatmap = cv2.applyColorMap(
                            np.uint8(255 * normalized_attention),
                            cv2.COLORMAP_VIRIDIS
                        )
                        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

                        # Blend with original image
                        original_float = original_image_rgb.astype(np.float32) / 255.0
                        heatmap_float = heatmap_rgb.astype(np.float32) / 255.0
                        alpha = np.expand_dims(normalized_attention, axis=-1)
                        alpha = np.repeat(alpha, 3, axis=-1)

                        overlay = (1 - alpha) * original_float + alpha * heatmap_float
                        overlay = np.clip(overlay, 0, 1)
                        
                        # Convert to image and encode as base64
                        plt.figure(figsize=(10, 5))
                        
                        plt.subplot(1, 2, 1)
                        plt.imshow(original_image_rgb)
                        plt.title("Original Image")
                        plt.axis('off')
                        
                        plt.subplot(1, 2, 2)
                        plt.imshow(overlay)
                        plt.title("Attention Overlay")
                        plt.axis('off')
                        
                        plt.tight_layout()
                        
                        # Save to bytes buffer
                        buffer = io.BytesIO()
                        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
                        plt.close()
                        
                        buffer.seek(0)
                        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                        
                        return image_base64
                        
            return None
                
        except Exception as e:
            print(f"Error generating attention overlay: {str(e)}")
            return None

    def predict_leaf_classification(self, image_bytes, input_text=""):
        """
        Legacy method - kept for backward compatibility.
        Now uses the new complete method and yields the results.
        """
        result = self.predict_leaf_classification_complete(image_bytes, input_text)
        
        if result.get("error"):
            yield f"Error: {result['error']}\n"
            return
            
        # Yield status messages for streaming compatibility
        yield "Resized image, normalizing and preprocessing...\n"
        yield "Preparing image for neural network analysis...\n"
        yield "Running CNN model inference...\n"
        yield "Analyzing prediction results...\n"
        yield "Finalizing diagnosis...\n"
        
        # Generate attention visualization messages
        if result.get("attention_overlay"):
            yield "Generating attention visualization...\n"
            yield "Processing attention weights...\n"
            yield "Creating attention heatmap overlay...\n"
            yield "Attention visualization completed! Generated overlay showing model focus areas.\n"
            yield f"ATTENTION_OVERLAY_BASE64:{result['attention_overlay']}\n"
        
        yield f"Diagnosis Complete! Health Status: {result['disease_name']} with confidence {result['confidence']:.2f}\n"
        return