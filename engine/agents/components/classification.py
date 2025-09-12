"""
Component 3: Classification Step

ML model or LLM detects and classifies disease using the leaf image.
Results are presented with confidence score; user feedback or corrections are supported.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from .base_component import BaseComponent, ComponentResult

logger = logging.getLogger(__name__)

class ClassificationComponent(BaseComponent):
    """
    Handles disease classification using CNN model with attention visualization.
    
    This component:
    - Processes leaf images using the trained CNN model
    - Generates attention visualization showing AI focus areas  
    - Presents results with confidence scores
    - Allows user feedback and corrections
    - Validates classification quality and reliability
    - Provides alternative classifications if confidence is low
    """
    
    def __init__(self):
        super().__init__()
        # Import CNN model here to avoid circular imports
        from ml.cnn_attn_classifier_improved import CNNWithAttentionClassifier
        self.cnn_model = CNNWithAttentionClassifier()
        
        # Confidence thresholds for result quality
        self.confidence_thresholds = {
            'high': 0.85,
            'medium': 0.65,
            'low': 0.45
        }
        
        # Common disease mappings for user-friendly names
        self.disease_mappings = {
            'early_blight': 'Early Blight',
            'late_blight': 'Late Blight', 
            'bacterial_spot': 'Bacterial Spot',
            'target_spot': 'Target Spot',
            'mosaic_virus': 'Mosaic Virus',
            'leaf_mold': 'Leaf Mold',
            'septoria_leaf_spot': 'Septoria Leaf Spot',
            'healthy': 'Healthy Plant'
        }

    async def execute(
        self,
        session_id: str,
        user_input: str,
        image_data: Optional[str],
        session_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ComponentResult:
        """
        Execute disease classification on uploaded image.
        
        Args:
            session_id: Session identifier
            user_input: User's input (may contain corrections/feedback)
            image_data: Base64 encoded leaf image
            session_data: Current session data
            context: Additional context including any image handle
            
        Returns:
            ComponentResult with classification results
        """
        user_profile = session_data.get('user_profile', {})
        logger.info(f"🧠 Classification component received user_profile: {user_profile}")
        logger.debug(f"   Full session_data keys: {list(session_data.keys())}")
        
        # Check if user is providing feedback on previous classification
        if self._is_feedback_input(user_input, session_data):
            return await self._handle_user_feedback(user_input, session_data)
        
        # Get image data - either from current request or session
        image_b64 = self._get_image_for_classification(image_data, session_data, context)
        
        if not image_b64:
            return self.create_error_result(
                "No image available for classification. Please upload a clear image of the affected leaves.",
                "I need an image to analyze. Could you please upload a clear photo of the affected plant leaves?"
            )
        
        # Perform classification using CNN model
        classification_result = await self._perform_cnn_classification(
            session_data, image_b64, user_profile, session_id
        )
        
        # Process and validate results
        processed_result = self._process_classification_result(
            classification_result, user_profile
        )
        
        # Generate user-friendly response
        response = self._generate_classification_response(processed_result, user_profile)
        
        # Prepare session data update
        session_update = {
            'classification_results': processed_result,
            'has_classification': True,
            'classification_timestamp': asyncio.get_event_loop().time()
        }
        
        # Determine if user input is needed (for feedback/confirmation)
        requires_input = processed_result.get('confidence_level') in ['low', 'medium']
        next_suggestions = self._generate_classification_suggestions(processed_result)
        
        logger.info(f"🔬 Classification completed: {processed_result.get('disease_name', 'unknown')}")
        logger.debug(f"   Confidence: {processed_result.get('confidence', 0.0):.2f}")
        logger.debug(f"   Quality: {processed_result.get('confidence_level', 'unknown')}")
        
        return self.create_success_result(
            response=response,
            session_data=session_update,
            requires_user_input=requires_input,
            next_suggestions=next_suggestions
        )

    def _is_feedback_input(self, user_input: str, session_data: Dict[str, Any]) -> bool:
        """
        Check if user input is feedback on previous classification.
        
        Args:
            user_input: User's input
            session_data: Session data
            
        Returns:
            True if input appears to be feedback
        """
        if not user_input or not session_data.get('classification_results'):
            return False
        
        feedback_indicators = [
            'incorrect', 'wrong', 'not right', 'disagree', 'different', 
            'actually', 'correction', 'mistake', 'error', 'reclassify'
        ]
        
        confirmation_indicators = [
            'correct', 'right', 'yes', 'accurate', 'agree', 'confirmed',
            'looks right', 'that\'s it'
        ]
        
        user_input_lower = user_input.lower()
        
        return any(indicator in user_input_lower for indicator in feedback_indicators + confirmation_indicators)

    async def _handle_user_feedback(
        self,
        user_input: str,
        session_data: Dict[str, Any]
    ) -> ComponentResult:
        """
        Handle user feedback on classification results.
        
        Args:
            user_input: User's feedback
            session_data: Current session data
            
        Returns:
            ComponentResult with updated classification or next steps
        """
        previous_result = session_data.get('classification_results', {})
        user_input_lower = user_input.lower()
        
        # Check if user confirms the classification
        if any(word in user_input_lower for word in ['correct', 'right', 'yes', 'accurate', 'agree']):
            response = f"Great! I'm glad the classification of {previous_result.get('disease_name', 'the disease')} was accurate. "
            response += "Now I can provide specific treatment recommendations for this condition."
            
            # Update confidence based on user confirmation
            updated_result = {**previous_result, 'user_confirmed': True, 'confidence': min(1.0, previous_result.get('confidence', 0.5) + 0.1)}
            
            return self.create_success_result(
                response=response,
                session_data={'classification_results': updated_result},
                requires_user_input=False,
                next_suggestions=['proceed_to_prescription', 'ask_questions']
            )
        
        # Check if user disagrees or provides correction
        elif any(word in user_input_lower for word in ['incorrect', 'wrong', 'not right', 'different', 'actually']):
            response = "I understand the classification may not be accurate. "
            
            # Check if user provided a specific disease name
            suggested_disease = self._extract_disease_from_feedback(user_input)
            if suggested_disease:
                response += f"You're suggesting it might be {suggested_disease}. "
                response += "Let me update the diagnosis and provide treatment accordingly. "
                response += "Would you like me to proceed with this correction?"
                
                # Create corrected result
                corrected_result = {
                    'disease_name': suggested_disease,
                    'confidence': 0.8,  # User-provided, so reasonably confident
                    'confidence_level': 'high',
                    'user_corrected': True,
                    'original_classification': previous_result.get('disease_name'),
                    'correction_source': 'user_feedback'
                }
                
                return self.create_success_result(
                    response=response,
                    session_data={'classification_results': corrected_result},
                    requires_user_input=True,
                    next_suggestions=['confirm_correction', 'provide_more_details', 'reclassify']
                )
            else:
                response += "Could you tell me what you think the disease is, or would you like me to try reclassifying with different parameters?"
                
                return self.create_success_result(
                    response=response,
                    session_data={},
                    requires_user_input=True,
                    next_suggestions=['specify_disease', 'reclassify', 'describe_symptoms']
                )
        
        # Handle request for reclassification
        elif 'reclassify' in user_input_lower or 'try again' in user_input_lower:
            response = "I'll reclassify the image with adjusted parameters. "
            response += "Please wait while I reanalyze the leaf image..."
            
            return self.create_success_result(
                response=response,
                session_data={'request_reclassification': True},
                requires_user_input=False,
                next_suggestions=['wait_for_results']
            )
        
        else:
            # Generic feedback response
            response = "I'd like to ensure the classification is accurate. "
            response += "Could you tell me if the diagnosis seems correct, or if you think it might be a different disease?"
            
            return self.create_success_result(
                response=response,
                session_data={},
                requires_user_input=True,
                next_suggestions=['confirm_diagnosis', 'suggest_correction', 'describe_symptoms']
            )

    def _get_image_for_classification(
        self,
        image_data: Optional[str],
        session_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get image data for classification from various sources.
        
        Args:
            image_data: Direct image data
            session_data: Session data that may contain image
            context: Context that may contain image handle
            
        Returns:
            Base64 image data or None
        """
        # Check direct image data first
        if image_data:
            return image_data
        
        # Check if there's an image handle in context (from existing agent system)
        if 'image_handle' in context:
            # Try to get from image store (would need access to agent core)
            logger.debug(f"Found image handle in context: {context['image_handle']}")
            # This would integrate with existing image store system
        
        # Check session data for stored image
        if session_data.get('has_image'):
            logger.debug("Session indicates image available but no direct access")
        
        return None

    async def _perform_cnn_classification(
        self,
        session_data: Dict[str, Any],
        image_b64: str,
        user_profile: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Perform CNN classification with attention visualization.
        
        Args:
            image_b64: Base64 encoded image
            user_profile: User profile for context
            session_id: Session identifier
            
        Returns:
            Raw classification results
        """
        try:
            logger.info(f"🧠 Starting CNN classification for session {session_id}")
            
            # Prepare context for classification
            context_text = self._build_classification_context(user_profile)
            
            # Collect all chunks from the CNN model
            classification_chunks = []
            attention_overlay_b64 = None
            
            logger.debug("🔬 Invoking CNN model for classification...")
            
            # Call the improved CNN model
            for chunk in self.cnn_model.predict_leaf_classification(image_b64, context_text):
                chunk_str = str(chunk).rstrip("\n")
                
                # Handle attention visualization chunks
                if chunk_str.startswith("ATTENTION_OVERLAY_BASE64:"):
                    attention_overlay_b64 = chunk_str.replace("ATTENTION_OVERLAY_BASE64:", "")
                    logger.debug(f"🎯 Captured attention overlay: {len(attention_overlay_b64)} chars")
                    # Store the attention overlay data in session results
                    session_data.setdefault('attention_overlay_data', attention_overlay_b64)
                    # Also add to chunks for streaming
                    classification_chunks.append(chunk_str)
                else:
                    classification_chunks.append(chunk_str)
            
            # Get the final diagnosis result (should be the last chunk)
            final_result = classification_chunks[-1] if classification_chunks else "Classification failed"
            
            # Parse the result to extract structured information
            parsed_result = self._parse_cnn_result(final_result)
            
            # Add attention overlay if available
            if attention_overlay_b64:
                parsed_result['attention_overlay'] = attention_overlay_b64
                parsed_result['has_attention_visualization'] = True
            
            logger.info(f"✅ CNN classification completed: {parsed_result.get('disease_name', 'unknown')}")
            return parsed_result
            
        except Exception as e:
            logger.error(f"❌ CNN classification failed: {e}")
            return {
                'error': str(e),
                'disease_name': 'unknown',
                'confidence': 0.0,
                'confidence_level': 'error'
            }

    def _build_classification_context(self, user_profile: Dict[str, Any]) -> str:
        """
        Build context string for CNN classification.
        
        Args:
            user_profile: User profile data
            
        Returns:
            Context string for classification
        """
        context_parts = []
        
        if user_profile.get('crop_type'):
            context_parts.append(f"Crop: {user_profile['crop_type']}")
        
        if user_profile.get('location'):
            context_parts.append(f"Location: {user_profile['location']}")
        
        if user_profile.get('season'):
            context_parts.append(f"Season: {user_profile['season']}")
        
        if user_profile.get('problem_description'):
            context_parts.append(f"Symptoms: {user_profile['problem_description']}")
        
        return " | ".join(context_parts) if context_parts else ""

    def _parse_cnn_result(self, result_text: str) -> Dict[str, Any]:
        """
        Parse CNN model result into structured format.
        
        Args:
            result_text: Raw result text from CNN
            
        Returns:
            Structured classification result
        """
        import re
        
        # Expected format: "Diagnosis Complete! Health Status: disease_name with confidence X.XX"
        # Or: "Diagnosis Complete! Class: disease_name | Health Status: disease_name | Confidence: X.XX"
        
        result = {
            'raw_result': result_text,
            'disease_name': 'unknown',
            'confidence': 0.0,
            'confidence_level': 'low'
        }
        
        try:
            # Extract confidence score
            confidence_match = re.search(r'confidence[:\s]+(\d+\.?\d*)', result_text.lower())
            if confidence_match:
                confidence = float(confidence_match.group(1))
                # If confidence is > 1, it might be a percentage
                if confidence > 1:
                    confidence = confidence / 100
                result['confidence'] = confidence
            
            # Extract disease name
            health_status_match = re.search(r'health status[:\s]+([a-zA-Z_]+)', result_text.lower())
            if health_status_match:
                disease_name = health_status_match.group(1).strip()
                result['disease_name'] = disease_name
            
            # If no health status, try class
            elif 'class:' in result_text.lower():
                class_match = re.search(r'class[:\s]+([a-zA-Z_]+)', result_text.lower())
                if class_match:
                    result['disease_name'] = class_match.group(1).strip()
            
            # Determine confidence level
            confidence = result['confidence']
            if confidence >= self.confidence_thresholds['high']:
                result['confidence_level'] = 'high'
            elif confidence >= self.confidence_thresholds['medium']:
                result['confidence_level'] = 'medium'
            else:
                result['confidence_level'] = 'low'
                
        except Exception as e:
            logger.warning(f"Failed to parse CNN result: {e}")
        
        return result

    def _process_classification_result(
        self,
        raw_result: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process and enhance classification result.
        
        Args:
            raw_result: Raw classification result
            user_profile: User profile for context
            
        Returns:
            Processed classification result
        """
        processed = {**raw_result}
        
        # Convert disease name to user-friendly format
        disease_key = processed.get('disease_name', '').lower().replace(' ', '_')
        friendly_name = self.disease_mappings.get(disease_key, disease_key.replace('_', ' ').title())
        processed['friendly_disease_name'] = friendly_name
        
        # Add severity assessment based on confidence and disease type
        if processed.get('disease_name') != 'healthy':
            confidence = processed.get('confidence', 0.0)
            if confidence >= 0.8:
                processed['severity_assessment'] = 'Confident diagnosis - treatment recommended'
            elif confidence >= 0.6:
                processed['severity_assessment'] = 'Probable diagnosis - monitor and treat if symptoms persist'
            else:
                processed['severity_assessment'] = 'Uncertain diagnosis - additional observation or expert consultation recommended'
        else:
            processed['severity_assessment'] = 'Plant appears healthy'
        
        # Add context-specific recommendations
        if user_profile.get('is_urgent'):
            processed['urgency_note'] = 'Given the urgent nature, consider immediate treatment if diagnosis confidence is medium or higher.'
        
        return processed

    def _generate_classification_response(
        self,
        result: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> str:
        """
        Generate user-friendly response for classification results.
        
        Args:
            result: Processed classification result
            user_profile: User profile
            
        Returns:
            Response message
        """
        friendly_name = result.get('friendly_disease_name', 'Unknown condition')
        confidence = result.get('confidence', 0.0)
        confidence_level = result.get('confidence_level', 'low')
        
        # Main diagnosis
        response = f"🔬 **Disease Classification Results**\n\n"
        response += f"**Diagnosis:** {friendly_name}\n"
        response += f"**Confidence:** {confidence:.1%} ({confidence_level})\n"
        
        # Add severity assessment
        if result.get('severity_assessment'):
            response += f"**Assessment:** {result['severity_assessment']}\n"
        
        # Add attention visualization note
        if result.get('has_attention_visualization'):
            response += f"\n🎯 **AI Focus Areas:** I've generated a visualization showing which parts of the leaf I focused on during analysis.\n"
            # response += result.get('attention_overlay')
            response += "\n"
        
        # Add confidence-based guidance
        if confidence_level == 'high':
            response += f"\n✅ I'm confident in this diagnosis. Proceeding with treatment recommendations"
        elif confidence_level == 'medium':
            response += f"\n⚠️ This is a probable diagnosis. Does it match what you're observing? I can provide treatment options or reclassify if needed."
        else:
            response += f"\n❓ The diagnosis has low confidence. Could you provide more details about symptoms or upload additional images? I can also try reclassifying."
        
        # Add urgency note if applicable
        if result.get('urgency_note'):
            response += f"\n\n🚨 **Urgency Note:** {result['urgency_note']}"
        
        return response

    def _generate_classification_suggestions(self, result: Dict[str, Any]) -> list:
        """
        Generate suggestions based on classification results.
        
        Args:
            result: Classification result
            
        Returns:
            List of suggestions
        """
        confidence_level = result.get('confidence_level', 'low')
        suggestions = []
        
        if confidence_level == 'high':
            suggestions.extend(['proceed_to_treatment', 'ask_about_diagnosis', 'get_prescription'])
        elif confidence_level == 'medium':
            suggestions.extend(['confirm_diagnosis', 'provide_more_symptoms', 'proceed_with_caution', 'reclassify'])
        else:
            suggestions.extend(['provide_more_details', 'upload_clearer_image', 'reclassify', 'expert_consultation'])
        
        # Always available options
        suggestions.extend(['ask_questions', 'modify_information'])
        
        return suggestions

    def _extract_disease_from_feedback(self, user_input: str) -> Optional[str]:
        """
        Extract disease name from user feedback.
        
        Args:
            user_input: User's feedback text
            
        Returns:
            Extracted disease name or None
        """
        user_input_lower = user_input.lower()
        
        # Check for direct disease mentions
        for disease_key, friendly_name in self.disease_mappings.items():
            if disease_key in user_input_lower or friendly_name.lower() in user_input_lower:
                return friendly_name
        
        # Check for common disease terms
        common_diseases = ['blight', 'spot', 'virus', 'mold', 'rust', 'wilt', 'rot']
        for disease in common_diseases:
            if disease in user_input_lower:
                return disease.title()
        
        return None
