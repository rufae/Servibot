"""
Base Tool Interface
Abstract base class for all ServiBot tools.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel


class ToolParameter(BaseModel):
    """Model for tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


class ToolSchema(BaseModel):
    """Model for tool schema."""
    name: str
    description: str
    parameters: List[ToolParameter]


class BaseTool(ABC):
    """Abstract base class for tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any], user_id: str = "default_user") -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            params: Tool parameters
            user_id: User identifier for OAuth
        
        Returns:
            Tool execution result
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> ToolSchema:
        """
        Get tool schema for LLM.
        
        Returns:
            Tool schema
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate parameters against schema.
        
        Args:
            params: Parameters to validate
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        schema = self.get_schema()
        
        for param_def in schema.parameters:
            if param_def.required and param_def.name not in params:
                raise ValueError(f"Missing required parameter: {param_def.name}")
        
        return True
