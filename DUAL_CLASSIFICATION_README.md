# CNN + LLaVA Classification System

This document describes the implementation of the enhanced classification system that uses CNN attention models as the primary classifier with LLaVA (Large Language and Vision Assistant) as a fallback expert for uncertain cases.

## Overview

The classification tool uses a dual evaluation approach with simple decision logic:

1. **Dual Evaluation** - Both CNN and LLaVA always analyze the image
2. **Comparison & Logging** - Results are compared and logged for analysis
3. **Simple Decision Logic** - Use CNN unless it returns 'unknown', then use LLaVA
4. **Source Attribution** - Indicates CNN vs SME (expert) source

## Architecture

```
Image (base64) → Classification Tool
                       ↓
              ┌─────────────────────┐
              │   CNN Evaluation    │
              │   LLaVA Evaluation  │ (Both always run)
              └─────────────────────┘
                       ↓
              ┌─────────────────────┐
              │ Compare & Log       │
              │ CNN Unknown?        │
              └─────────────────────┘
                       ↓
            ┌─────────────┬─────────────┐
            │     No      │    Yes      │
            │ Use CNN     │ Use LLaVA   │
            │ source:cnn  │ source:sme  │
            └─────────────┴─────────────┘
```

## Implementation Details

### LLaVA Integration

- **API Endpoint**: `http://localhost:11434/api/generate`
- **Model**: `llava` (via Ollama)
- **Timeout**: 120 seconds
- **Response Format**: Structured JSON with disease_name, confidence, severity, description

### Unknown Detection

The system detects "unknown" CNN classifications by checking if the disease name matches:
- "unknown"
- "uncertain"  
- "unidentified"
- "not_identified"

### Result Logic

| Scenario | CNN Result | LLaVA Consulted | Final Result | Source |
|----------|------------|-----------------|--------------|--------|
| CNN knows disease | Known disease | ❌ | CNN result | `cnn` |
| CNN unknown, LLaVA works | "unknown" | ✅ | LLaVA result | `sme` |
| CNN unknown, LLaVA fails | "unknown" | ❌ (error) | CNN "unknown" | `cnn` |
| CNN error | Error | ❌ | Error returned | N/A |

## Output Format

### Enhanced Response Structure

**Example 1: CNN provides classification (most common)**
```json
{
  "disease_name": "Early_blight",
  "confidence": 0.87,
  "severity": "moderate", 
  "description": "Detected Early_blight with 87% confidence",
  "source": "cnn",
  "attention_overlay": "base64_encoded_image",
  "raw_class_label": "Early_blight", 
  "plant_context": {
    "plant_type": "tomato",
    "location": "greenhouse",
    "season": "summer",
    "growth_stage": "flowering"
  },
  "evaluation_details": {
    "cnn_result": {
      "disease_name": "Early_blight",
      "confidence": 0.87
    },
    "llava_result": {
      "disease_name": "early blight",
      "confidence": 0.89,
      "severity": "moderate",
      "description": "The leaf shows brown spots characteristic of early blight"
    },
    "similarity_score": 0.80,
    "decision_reason": "CNN provided valid classification"
  }
}
```

**Example 2: CNN returns unknown, LLaVA consulted**
```json
{
  "disease_name": "bacterial_spot",
  "confidence": 0.82,
  "severity": "moderate",
  "description": "Detected bacterial_spot with 82% confidence via expert evaluation",
  "source": "sme",
  "attention_overlay": "base64_encoded_image",
  "raw_class_label": "unknown",
  "evaluation_details": {
    "cnn_result": {
      "disease_name": "unknown",
      "confidence": 0.45
    },
    "llava_result": {
      "disease_name": "bacterial_spot",
      "confidence": 0.82,
      "severity": "moderate",
      "description": "The leaf shows small dark spots with yellow halos characteristic of bacterial spot"
    },
    "similarity_score": 0.0,
    "decision_reason": "CNN returned unknown - using LLaVA"
  }
}
```

### Source Field Values

- **`"cnn"`** - CNN provided a known classification (or LLaVA unavailable for unknown)
- **`"sme"`** - CNN returned unknown, using LLaVA as Subject Matter Expert

## Setup Requirements

### Prerequisites

1. **Ollama Installation**:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **LLaVA Model Download**:
   ```bash
   ollama pull llava
   ```

3. **Start Ollama Service**:
   ```bash
   ollama serve
   ```

4. **Verify Setup**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Testing

### Manual Testing

You can test the dual classification system using the existing workflow. The tool will automatically:

1. Run CNN classification
2. Run LLaVA evaluation (always)
3. Compare and log both results
4. Use CNN unless it returns "unknown", then use LLaVA
5. Return results with appropriate source attribution and comparison data

### Error Handling

- **LLaVA Unavailable**: Falls back to CNN-only classification
- **JSON Parsing Errors**: Logs warning and falls back to CNN
- **Network Timeouts**: 120-second timeout with fallback
- **Invalid Base64**: Proper error messages returned

## Logging

Enhanced logging provides visibility into:

- CNN classification results
- Unknown detection triggers
- LLaVA consultation decisions
- Expert evaluation results
- Fallback scenarios and API errors

Example log output:
```
INFO - Disease comparison - CNN: early_blight, LLaVA: early blight, Similarity: 0.80
INFO - Using CNN classification: Early_blight (0.87). LLaVA comparison available.
INFO - Disease comparison - CNN: unknown, LLaVA: bacterial_spot, Similarity: 0.00  
INFO - CNN returned unknown - using LLaVA classification: bacterial_spot (0.82)
WARNING - CNN returned unknown and LLaVA unavailable: LLaVA connection failed
```

## Performance Considerations

- **Dual Evaluation**: Both CNN and LLaVA run for every request (enables comparison analysis)
- **Parallel Analysis**: Valuable for research and model comparison purposes  
- **Caching**: No caching implemented (each request hits both models)
- **Timeout**: 120s timeout prevents hanging requests
- **Analysis Benefits**: Always have both model perspectives for logging and research

## Future Enhancements

- **Caching**: Cache LLaVA results for identical images in unknown cases
- **Confidence Thresholds**: Use confidence scores to determine when CNN is "uncertain"
- **Multiple Unknown Triggers**: Expand unknown detection beyond just disease names
- **LLaVA Model Selection**: Choose different LLaVA models based on plant type
- **Batch Processing**: Support for multiple image evaluation
