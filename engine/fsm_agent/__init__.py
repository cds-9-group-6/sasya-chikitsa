"""
Dynamic Planning Agent for Leaf Disease Diagnosis and Prescription

This module implements a dynamic, prompt-driven finite state machine (FSM) 
for plant disease diagnosis and treatment prescription, guided by user input 
and Ollama LLM through LangChain.

The agent uses a modular, extensible architecture with plug-and-play tools
for classification, prescription, vendor integration, and more.
"""

__version__ = "1.0.0"
__author__ = "Sasya Chikitsa Team"

from fsm_agent.core.fsm_agent import DynamicPlanningAgent
from fsm_agent.server.fsm_server import FSMServer

__all__ = [
    "DynamicPlanningAgent",
    "FSMServer"
]


