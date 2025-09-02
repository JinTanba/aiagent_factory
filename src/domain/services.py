"""
Domain services containing business logic.
"""

from typing import List, Optional
from .entities import AgentSession, MCPServerConfig
from .repositories import SessionRepository
import uuid
from datetime import datetime


class SessionDomainService:
    """Domain service for session-related business logic."""
    
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