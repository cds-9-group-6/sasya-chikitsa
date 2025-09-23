"""
Base node class for FSM Agent workflow nodes
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

try:
    from ..workflow_state import WorkflowState, update_state_node
except ImportError:
    from engine.fsm_agent.core.workflow_state import WorkflowState, update_state_node

logger = logging.getLogger(__name__)


class BaseNode(ABC):
    """Base class for all workflow nodes"""
    
    def __init__(self, tools: Dict[str, Any], llm: Any, mlflow_manager=None):
        """
        Initialize the node
        
        Args:
            tools: Dictionary of available tools
            llm: The language model instance
            mlflow_manager: Optional MLflow manager instance for metrics tracking
        """
        self.tools = tools
        self.llm = llm
        self.mlflow_manager = mlflow_manager
        self.logger = logger
    
    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        pass
    
    @property
    @abstractmethod
    def node_name(self) -> str:
        """Return the name of this node"""
        pass
    
    def update_node_state(self, state: WorkflowState) -> None:
        """Update the state to reflect this node is executing"""
        self.logger.info(f"Executing {self.node_name} node for session {state['session_id']}")
        update_state_node(state, self.node_name)

