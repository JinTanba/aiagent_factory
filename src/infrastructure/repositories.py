"""
Concrete implementations of repository interfaces.
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid

from ..domain.entities import AgentSession, MCPServerConfig
from ..domain.repositories import SessionRepository, AgentRepository
from ..domain.value_objects import SessionId

class InMemorySessionRepository(SessionRepository):
    """In-memory implementation of session repository."""
    
    def __init__(self):
        self._sessions: Dict[str, AgentSession] = {}
    
    def create_session(self, session_id: str, mcp_servers: List[MCPServerConfig]) -> AgentSession:
        """Create a new agent session."""
        mcp_servers_dict = [
            {
                "name": server.name,
                "command": server.command,
                "args": server.args,
                "env": server.env or {},
                "transport": server.transport or "stdio",
            }
            for server in mcp_servers
        ]
        
        session = AgentSession(
            session_id=session_id,
            mcp_servers=mcp_servers_dict,
            created_at=datetime.utcnow()
        )
        
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)
    
    def update_session(self, session: AgentSession) -> bool:
        """Update an existing session."""
        if session.session_id in self._sessions:
            self._sessions[session.session_id] = session
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[AgentSession]:
        """List all active sessions."""
        return list(self._sessions.values())
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self._sessions
    
    def get_session_count(self) -> int:
        """Get the total number of active sessions."""
        return len(self._sessions)
    
    def delete_all_sessions(self) -> int:
        """Delete all sessions and return the count."""
        count = len(self._sessions)
        self._sessions.clear()
        return count