"""
Repository interfaces for domain layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import (
    AgentSession, MCPServerConfig, AgentExecuteParams,
    AgentConfiguration, ConversationSession
)


class AgentConfigurationRepository(ABC):
    """Repository interface for managing agent configurations."""
    
    @abstractmethod
    async def create_config(self, config: AgentConfiguration) -> str:
        """Create a new agent configuration and return config_id."""
        pass
    
    @abstractmethod
    async def get_config(self, config_id: str) -> Optional[AgentConfiguration]:
        """Retrieve a configuration by ID."""
        pass
    
    @abstractmethod
    async def update_config(self, config: AgentConfiguration) -> bool:
        """Update an existing configuration."""
        pass
    
    @abstractmethod
    async def delete_config(self, config_id: str) -> bool:
        """Delete a configuration."""
        pass
    
    @abstractmethod
    async def list_configs(self, active_only: bool = True) -> List[AgentConfiguration]:
        """List all configurations."""
        pass
    
    @abstractmethod
    async def config_exists(self, config_id: str) -> bool:
        """Check if a configuration exists."""
        pass


class ConversationRepository(ABC):
    """Repository interface for managing conversation sessions."""
    
    @abstractmethod
    async def create_session(self, session: ConversationSession) -> str:
        """Create a new conversation session and return session_id."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve a session by ID."""
        pass
    
    @abstractmethod
    async def update_session(self, session: ConversationSession) -> bool:
        """Update an existing session."""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        pass
    
    @abstractmethod
    async def list_sessions(self, config_id: Optional[str] = None, active_only: bool = True) -> List[ConversationSession]:
        """List sessions, optionally filtered by config_id."""
        pass
    
    @abstractmethod
    async def list_sessions_for_config(self, config_id: str) -> List[ConversationSession]:
        """List all sessions for a specific configuration."""
        pass
    
    @abstractmethod
    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        pass


class AgentRepository(ABC):
    """Repository interface for managing AI agents."""
    
    @abstractmethod
    async def create_agent(self, config: AgentConfiguration):
        """Create a new AI agent from configuration."""
        pass

    @abstractmethod
    async def ainvoke(self, params: AgentExecuteParams):
        """Execute AI Agent with given parameters."""
        pass


# Legacy repository for backward compatibility - will be removed later
class SessionRepository(ABC):
    """Legacy repository interface for managing agent sessions - deprecated."""
    
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