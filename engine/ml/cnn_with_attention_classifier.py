import base64
import numpy as np
import cv2
import os
import time
from tensorflow.keras.models import load_model
from keras.layers import Layer
import tensorflow as tf

# from engine.ml.label_mappings import LABEL_MAPPINGS
from engine.ml.label_mappings import LABEL_MAPPINGS

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
        print("[INFO] Model loaded successfully.")

    @staticmethod
    def load_model():
        ml_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(ml_dir)
        resources_dir = os.path.join(parent_dir, "resources")
        binary_model_path = os.path.join(resources_dir, "leaf_classification_attention_cnn_model.h5")
        print(f"[INFO] Loading binary leaf presence model from {binary_model_path}...")
        # return None
        return load_model(binary_model_path, custom_objects={'ReshapeLayer': ReshapeLayer})


    def predict_leaf_classification(self, image_bytes, input_text=""):
        """
        Predicts whether an image contains a leaf using the trained classification model.

        Args:
            image_bytes (str): Base64-encoded image bytes.
            input_text (str): Optional additional text.
        Yields:
            str: Intermediate output strings.
        """
        if self.loaded_model is None:
            yield "Error: Model is not loaded.\n"
            return

        if image_bytes is None:
            yield "Error: Mandatory argument 'image_bytes' is missing.\n"
            return

        try:
            image_decoded = base64.b64decode(image_bytes)
            nparr = np.frombuffer(image_decoded, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        except Exception as e:
            yield f"Error: Could not decode base64 image ({str(e)})\n"
            return
        if image is None:
            yield "Error: Could not load image from bytes.\n"
            return

        image_resized = cv2.resize(image, TARGET_IMG_SIZE)
        yield f"Resized image, normalizing and preprocessing...\n"
        time.sleep(1.5)  # Allow user to see preprocessing step

        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        is_success, img_buffer = cv2.imencode(".png", image_gray)
        # yield img_buffer.tobytes()

        yield f"Preparing image for neural network analysis...\n"
        time.sleep(1.0)  # Show preparation step

        image_preprocessed = image_resized.astype(np.float32) / 255.0
        image_for_prediction = np.expand_dims(image_preprocessed, axis=0)

        yield f"Running CNN model inference...\n"
        time.sleep(1.0)  # Brief pause before prediction

        prediction = self.loaded_model.predict(image_for_prediction)
        yield f"Analyzing prediction results...\n"
        time.sleep(1.0)  # Give time to see analysis step

        predicted_class_index = np.argmax(prediction)
        predicted_class_label = MODEL_LABEL_CLASSES[predicted_class_index]
        prediction_probability = prediction[0][predicted_class_index]
        # Transform it to Kisan CC label
        kissan_cc_class_label = LABEL_MAPPINGS[predicted_class_label]
        
        yield f"Finalizing diagnosis...\n"
        time.sleep(1.0)  # Brief pause before final result
        
        yield (f"Diagnosis Complete! Health Status: {predicted_class_label} with confidence {prediction_probability:.2f}")
        return
