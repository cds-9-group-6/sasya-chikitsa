"""
Classification Metrics Utilities

This module provides utilities for calculating various metrics for the 
dual CNN+LLaVA classification system.
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from scipy import stats
import math

logger = logging.getLogger(__name__)


class ClassificationMetrics:
    """
    Utilities for calculating classification metrics
    """
    
    @staticmethod
    def calculate_entropy(confidence: float) -> float:
        """
        Calculate entropy from confidence score
        
        Args:
            confidence: Confidence score between 0 and 1
            
        Returns:
            Entropy value (0.0 to 1.0, where 1.0 is maximum uncertainty)
        """
        try:
            # Clamp confidence to valid range
            confidence = max(0.001, min(0.999, confidence))
            
            # Convert to probability distribution [confidence, 1-confidence]
            probs = np.array([confidence, 1.0 - confidence])
            
            # Calculate entropy: -sum(p * log2(p))
            entropy = stats.entropy(probs, base=2)
            
            return float(entropy)
            
        except Exception as e:
            logger.error(f"Error calculating entropy: {e}")
            return 0.0
    
    @staticmethod
    def calculate_prediction_margin(cnn_confidence: float, llava_confidence: float) -> Dict[str, float]:
        """
        Calculate prediction margin and related metrics between CNN and LLaVA
        
        Args:
            cnn_confidence: CNN confidence score
            llava_confidence: LLaVA confidence score
            
        Returns:
            Dictionary with margin metrics
        """
        try:
            # Absolute difference
            margin = abs(cnn_confidence - llava_confidence)
            
            # Relative difference
            avg_confidence = (cnn_confidence + llava_confidence) / 2.0
            relative_margin = margin / max(avg_confidence, 0.001)  # Avoid division by zero
            
            # Confidence ratio
            confidence_ratio = cnn_confidence / max(llava_confidence, 0.001)
            
            # Agreement strength (lower margin = higher agreement)
            agreement_strength = 1.0 - margin
            
            # Disagreement level (categorized)
            if margin < 0.1:
                disagreement_level = "low"
            elif margin < 0.3:
                disagreement_level = "medium"
            else:
                disagreement_level = "high"
            
            return {
                "prediction_margin": margin,
                "relative_margin": relative_margin,
                "confidence_ratio": confidence_ratio,
                "agreement_strength": agreement_strength,
                "disagreement_level": disagreement_level,
                "cnn_higher": 1.0 if cnn_confidence > llava_confidence else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating prediction margin: {e}")
            return {
                "prediction_margin": 0.0,
                "relative_margin": 0.0,
                "confidence_ratio": 1.0,
                "agreement_strength": 0.0,
                "disagreement_level": "unknown",
                "cnn_higher": 0.0
            }
    
    @staticmethod
    def calculate_uncertainty_metrics(confidence: float) -> Dict[str, float]:
        """
        Calculate various uncertainty metrics from confidence score
        
        Args:
            confidence: Confidence score between 0 and 1
            
        Returns:
            Dictionary with uncertainty metrics
        """
        try:
            # Basic uncertainty (1 - confidence)
            uncertainty = 1.0 - confidence
            
            # Entropy-based uncertainty
            entropy = ClassificationMetrics.calculate_entropy(confidence)
            
            # Calibrated uncertainty (sigmoid-like transformation)
            calibrated_uncertainty = 1.0 / (1.0 + math.exp(5 * (confidence - 0.5)))
            
            # Uncertainty category
            if uncertainty < 0.2:
                uncertainty_level = "low"
            elif uncertainty < 0.5:
                uncertainty_level = "medium"
            else:
                uncertainty_level = "high"
            
            return {
                "uncertainty": uncertainty,
                "entropy_uncertainty": entropy,
                "calibrated_uncertainty": calibrated_uncertainty,
                "uncertainty_level": uncertainty_level,
                "is_confident": 1.0 if confidence > 0.8 else 0.0,
                "is_uncertain": 1.0 if confidence < 0.5 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating uncertainty metrics: {e}")
            return {
                "uncertainty": 1.0,
                "entropy_uncertainty": 1.0,
                "calibrated_uncertainty": 1.0,
                "uncertainty_level": "high",
                "is_confident": 0.0,
                "is_uncertain": 1.0
            }
    
    @staticmethod
    def calculate_decision_metrics(cnn_result: Dict[str, Any], 
                                 llava_result: Dict[str, Any], 
                                 final_result: Dict[str, Any],
                                 similarity_score: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive decision metrics for the classification
        
        Args:
            cnn_result: CNN classification results
            llava_result: LLaVA classification results  
            final_result: Final classification decision
            similarity_score: Disease name similarity score
            
        Returns:
            Dictionary with comprehensive metrics
        """
        try:
            metrics = {}
            
            # Basic availability metrics
            cnn_available = not cnn_result.get("error", True)
            llava_available = not llava_result.get("error", True)
            
            metrics["cnn_available"] = 1.0 if cnn_available else 0.0
            metrics["llava_available"] = 1.0 if llava_available else 0.0
            metrics["both_available"] = 1.0 if (cnn_available and llava_available) else 0.0
            
            # Decision source metrics
            source = final_result.get("source", "unknown")
            metrics["used_cnn"] = 1.0 if source == "cnn" else 0.0
            metrics["used_sme"] = 1.0 if source == "sme" else 0.0
            metrics["cnn_unknown_trigger"] = 1.0 if source == "sme" else 0.0
            
            # Confidence metrics
            final_confidence = final_result.get("confidence", 0.0)
            metrics["final_confidence"] = final_confidence
            
            if cnn_available:
                cnn_confidence = cnn_result.get("confidence", 0.0)
                metrics["cnn_confidence"] = cnn_confidence
                
                # CNN uncertainty metrics
                cnn_uncertainty = ClassificationMetrics.calculate_uncertainty_metrics(cnn_confidence)
                for key, value in cnn_uncertainty.items():
                    metrics[f"cnn_{key}"] = value
            
            if llava_available:
                llava_confidence = llava_result.get("confidence", 0.0)
                metrics["llava_confidence"] = llava_confidence
                
                # Prediction margin metrics (only if both available)
                if cnn_available:
                    margin_metrics = ClassificationMetrics.calculate_prediction_margin(
                        cnn_result.get("confidence", 0.0), 
                        llava_confidence
                    )
                    metrics.update(margin_metrics)
            
            # Similarity metrics
            if similarity_score is not None:
                metrics["disease_name_similarity"] = similarity_score
                metrics["high_similarity"] = 1.0 if similarity_score >= 0.6 else 0.0
                metrics["low_similarity"] = 1.0 if similarity_score < 0.3 else 0.0
                
                # Similarity confidence interaction
                if cnn_available and llava_available:
                    # High similarity + high confidence = very reliable
                    avg_confidence = (cnn_result.get("confidence", 0.0) + llava_confidence) / 2.0
                    reliability_score = (similarity_score * avg_confidence + 
                                       similarity_score + avg_confidence) / 3.0
                    metrics["reliability_score"] = reliability_score
            
            # Decision quality metrics
            if source == "sme" and llava_available:
                # SME was used - how much better is it than CNN?
                llava_conf = llava_result.get("confidence", 0.0)
                cnn_conf = cnn_result.get("confidence", 0.0) if cnn_available else 0.0
                metrics["sme_confidence_gain"] = llava_conf - cnn_conf
            
            # System performance metrics
            if cnn_available and llava_available:
                metrics["system_coverage"] = 1.0  # Both systems working
            elif cnn_available or llava_available:
                metrics["system_coverage"] = 0.5  # Partial coverage
            else:
                metrics["system_coverage"] = 0.0  # No coverage
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating decision metrics: {e}")
            return {"calculation_error": 1.0}
    
    @staticmethod
    def get_metric_summary(metrics: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of metrics
        
        Args:
            metrics: Dictionary of calculated metrics
            
        Returns:
            String summary of key metrics
        """
        try:
            summary_parts = []
            
            # Decision source
            if metrics.get("used_cnn", 0) == 1:
                summary_parts.append("Used CNN")
            elif metrics.get("used_sme", 0) == 1:
                summary_parts.append("Used SME (LLaVA)")
            
            # Confidence
            final_conf = metrics.get("final_confidence", 0)
            summary_parts.append(f"Confidence: {final_conf:.2%}")
            
            # Uncertainty level
            if "cnn_uncertainty_level" in metrics:
                summary_parts.append(f"CNN Uncertainty: {metrics['cnn_uncertainty_level']}")
            
            # Prediction margin
            if "disagreement_level" in metrics:
                summary_parts.append(f"Agreement: {metrics['disagreement_level']} disagreement")
            
            # Similarity
            if "disease_name_similarity" in metrics:
                sim = metrics["disease_name_similarity"]
                summary_parts.append(f"Name Similarity: {sim:.2f}")
            
            # System coverage
            if "system_coverage" in metrics:
                coverage = metrics["system_coverage"]
                if coverage == 1.0:
                    summary_parts.append("Full System Coverage")
                elif coverage == 0.5:
                    summary_parts.append("Partial System Coverage") 
                else:
                    summary_parts.append("Limited System Coverage")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating metric summary: {e}")
            return "Metric summary unavailable"

