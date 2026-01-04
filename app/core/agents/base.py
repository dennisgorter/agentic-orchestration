"""Base agent interface for all domain agents."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.shared.messaging import AgentMessage


class BaseAgent(ABC):
    """
    Base class for all domain agents.
    
    Each domain agent must implement the handle() method to process
    incoming messages and return responses.
    
    Attributes:
        name (str): Unique identifier for this agent (e.g., "pollution_agent")
    """
    
    name: str
    
    @abstractmethod
    async def handle(self, message: 'AgentMessage') -> 'AgentMessage':
        """
        Handle an incoming agent message and return a response.
        
        Args:
            message: AgentMessage containing request data, trace info, and context
            
        Returns:
            AgentMessage with response payload and updated context
            
        Raises:
            Exception: If processing fails, should include trace_id for debugging
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
