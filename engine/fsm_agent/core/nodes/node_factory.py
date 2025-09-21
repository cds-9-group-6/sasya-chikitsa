"""
Node Factory for FSM Agent workflow
Manages creation and registry of all workflow nodes
"""

import logging
from typing import Dict, Any

from .base_node import BaseNode
from .initial_node import InitialNode
from .classifying_node import ClassifyingNode
from .prescribing_node import PrescribingNode
from .vendor_query_node import VendorQueryNode
from .show_vendors_node import ShowVendorsNode
from .order_booking_node import OrderBookingNode
from .followup_node import FollowupNode
from .completed_node import CompletedNode
from .session_end_node import SessionEndNode
from .error_node import ErrorNode

logger = logging.getLogger(__name__)


class NodeFactory:
    """Factory class for creating and managing workflow nodes"""
    
    def __init__(self, tools: Dict[str, Any], llm: Any, mlflow_manager=None):
        """
        Initialize the node factory
        
        Args:
            tools: Dictionary of available tools
            llm: The language model instance
            mlflow_manager: Optional MLflow manager instance for metrics tracking
        """
        self.tools = tools
        self.llm = llm
        self.mlflow_manager = mlflow_manager
        self.nodes = {}
        self._create_nodes()
    
    def _create_nodes(self) -> None:
        """Create all node instances"""
        node_classes = {
            "initial": InitialNode,
            "classifying": ClassifyingNode,
            "prescribing": PrescribingNode,
            "vendor_query": VendorQueryNode,
            "show_vendors": ShowVendorsNode,
            "order_booking": OrderBookingNode,
            "followup": FollowupNode,
            "completed": CompletedNode,
            "session_end": SessionEndNode,
            "error": ErrorNode
        }
        
        for node_name, node_class in node_classes.items():
            try:
                self.nodes[node_name] = node_class(self.tools, self.llm, self.mlflow_manager)
                logger.debug(f"Created node: {node_name}")
            except Exception as e:
                logger.error(f"Failed to create node {node_name}: {str(e)}")
                raise
        
        logger.info(f"Successfully created {len(self.nodes)} workflow nodes")
    
    def get_node(self, node_name: str) -> BaseNode:
        """
        Get a node instance by name
        
        Args:
            node_name: Name of the node to retrieve
            
        Returns:
            Node instance
            
        Raises:
            KeyError: If node name is not found
        """
        if node_name not in self.nodes:
            raise KeyError(f"Node '{node_name}' not found. Available nodes: {list(self.nodes.keys())}")
        
        return self.nodes[node_name]
    
    def get_all_nodes(self) -> Dict[str, BaseNode]:
        """
        Get all node instances
        
        Returns:
            Dictionary of node name to node instance mappings
        """
        return self.nodes.copy()
    
    def list_node_names(self) -> list:
        """
        Get list of all available node names
        
        Returns:
            List of node names
        """
        return list(self.nodes.keys())
    
    async def execute_node(self, node_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific node
        
        Args:
            node_name: Name of the node to execute
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        node = self.get_node(node_name)
        return await node.execute(state)
