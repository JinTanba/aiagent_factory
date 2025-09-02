"""
Repository interfaces for domain layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import AgentSession, MCPServerConfig,AgentExecuteParams


class SessionRepository(ABC):
    """Repository interface for managing agent sessions."""
    
    @abstractmethod
    def create_session(self, session_id: str, mcp_servers: List[MCPServerConfig]) -> AgentSession:
        """Create a new agent session."""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Retrieve a session by ID."""
        pass
    
    @abstractmethod
    def update_session(self, session: AgentSession) -> bool:
        """Update an existing session."""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        pass
    
    @abstractmethod
    def list_sessions(self) -> List[AgentSession]:
        """List all active sessions."""
        pass
    
    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        pass


class AgentRepository(ABC):
    """Repository interface for managing AI agents."""
    
    @abstractmethod
    async def create_agent(self, mcp_servers: List[Dict[str, Any]]):
        """Create a new AI agent with MCP servers."""
        pass

    @abstractmethod
    async def ainvoke(self, params: AgentExecuteParams):
        """execute AI Agent"""
        pass