"""
Domain services for business logic.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import asyncio
from collections import OrderedDict

from .entities import (
    AgentSession, MCPServerConfig, AgentConfiguration, ConversationSession
)
from .repositories import SessionRepository, AgentConfigurationRepository


class SessionDomainService:
    """Domain service for session management - legacy, will be removed."""
    
    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository
    
    def create_new_session(self, mcp_servers: List[MCPServerConfig], session_id: Optional[str] = None) -> AgentSession:
        """Create a new session with business rules applied."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if self.session_repository.session_exists(session_id):
            raise ValueError(f"Session {session_id} already exists")
        
        session = self.session_repository.create_session(session_id, mcp_servers)
        return session
    
    def validate_mcp_servers(self, mcp_servers: List[MCPServerConfig]) -> bool:
        """Validate MCP server configurations."""
        if not mcp_servers:
            raise ValueError("At least one MCP server must be configured")
        
        server_names = [server.name for server in mcp_servers]
        if len(server_names) != len(set(server_names)):
            raise ValueError("MCP server names must be unique")
        
        return True


class AgentConfigurationService:
    """Domain service for agent configuration management."""
    
    def __init__(self, config_repository: AgentConfigurationRepository):
        self.config_repository = config_repository
    
    def validate_configuration(self, config: AgentConfiguration) -> None:
        """Validate agent configuration."""
        if not config.name.strip():
            raise ValueError("Configuration name is required")
        
        if not config.mcp_servers:
            raise ValueError("At least one MCP server must be configured")
        
        seen_names = set()
        for server in config.mcp_servers:
            if not server.name or not server.command:
                raise ValueError("MCP server must have name and command")
            if server.name in seen_names:
                raise ValueError(f"Duplicate MCP server name: {server.name}")
            seen_names.add(server.name)
    
    async def create_configuration(self, name: str, mcp_servers: List[MCPServerConfig], 
                                 system_prompt: Optional[str] = None,
                                 model_settings: Optional[Dict[str, Any]] = None) -> AgentConfiguration:
        """Create a new agent configuration."""
        config = AgentConfiguration(
            name=name,
            mcp_servers=mcp_servers,
            system_prompt=system_prompt,
            model_settings=model_settings
        )
        
        self.validate_configuration(config)
        
        config_id = await self.config_repository.create_config(config)
        config.config_id = config_id
        return config


class ConversationService:
    """Domain service for conversation management."""
    
    def create_conversation(self, config_id: str, session_id: Optional[str] = None) -> ConversationSession:
        """Create a new conversation session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        return ConversationSession(
            session_id=session_id,
            config_id=config_id
        )


class AgentInstance:
    """Represents a cached agent instance."""
    
    def __init__(self, config_id: str, agent: Any):
        self.config_id = config_id
        self.agent = agent
        self.created_at = datetime.utcnow()
        self.last_used = datetime.utcnow()
        self.usage_count = 0
    
    def mark_used(self):
        """Mark the agent as recently used."""
        self.last_used = datetime.utcnow()
        self.usage_count += 1
    
    def is_stale(self, max_idle_minutes: int = 30) -> bool:
        """Check if the agent instance is stale and should be evicted."""
        return (datetime.utcnow() - self.last_used) > timedelta(minutes=max_idle_minutes)


class AgentInstanceCache:
    """Cache for managing agent instances with LRU eviction."""
    
    def __init__(self, max_size: int = 50, max_idle_minutes: int = 30):
        self.max_size = max_size
        self.max_idle_minutes = max_idle_minutes
        self._cache: OrderedDict[str, AgentInstance] = OrderedDict()
        self._lock = asyncio.Lock()
    
    async def get_or_create_agent(self, config: AgentConfiguration, agent_factory) -> Any:
        """Get cached agent or create new one."""
        async with self._lock:
            config_id = config.config_id
            
            # Check if agent exists in cache
            if config_id in self._cache:
                instance = self._cache[config_id]
                
                # Check if instance is stale
                if not instance.is_stale(self.max_idle_minutes):
                    # Move to end (most recently used)
                    self._cache.move_to_end(config_id)
                    instance.mark_used()
                    return instance.agent
                else:
                    # Remove stale instance
                    del self._cache[config_id]
            
            # Create new agent instance
            agent = await agent_factory.create_agent_from_config(config)
            instance = AgentInstance(config_id, agent)
            
            # Add to cache
            self._cache[config_id] = instance
            
            # Evict oldest if cache is full
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)  # Remove least recently used
            
            instance.mark_used()
            return agent
    
    async def evict_stale_agents(self):
        """Remove stale agents from cache."""
        async with self._lock:
            stale_keys = [
                config_id for config_id, instance in self._cache.items()
                if instance.is_stale(self.max_idle_minutes)
            ]
            
            for config_id in stale_keys:
                del self._cache[config_id]
    
    async def clear_cache(self):
        """Clear all cached agents."""
        async with self._lock:
            self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'agents': [
                {
                    'config_id': instance.config_id,
                    'created_at': instance.created_at.isoformat(),
                    'last_used': instance.last_used.isoformat(),
                    'usage_count': instance.usage_count
                }
                for instance in self._cache.values()
            ]
        }


# Global agent cache instance
agent_cache = AgentInstanceCache()