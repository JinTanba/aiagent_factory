"""
Data Transfer Objects for the application layer.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from ..domain.entities import MCPServerConfig
from ..domain.value_objects import StreamEventType


class CreateAgentRequest(BaseModel):
    """Request to create a new agent."""
    mcp_servers: List[MCPServerConfig] = Field(
        description="List of MCP server configurations"
    )
    session_id: Optional[str] = Field(
        None, description="Optional custom session ID"
    )


class CreateAgentResponse(BaseModel):
    """Response from creating an agent."""
    session_id: str
    message: str
    mcp_servers_count: int
    created_at: datetime


class ExecuteAgentRequest(BaseModel):
    """Request to execute a message with an agent."""
    session_id: str = Field(description="Session ID of the agent")
    message: str = Field(description="Message to send to the agent")
    stream: bool = Field(False, description="Whether to stream the response")


class ExecuteAgentResponse(BaseModel):
    """Response from executing an agent message."""
    session_id: str
    response: str
    timestamp: datetime


class SessionSummary(BaseModel):
    """Summary information about a session."""
    session_id: str
    created_at: datetime
    mcp_servers_count: int
    message_count: int


class ListSessionsResponse(BaseModel):
    """Response listing all active sessions."""
    sessions: List[SessionSummary]


class SessionDetailsResponse(BaseModel):
    """Detailed information about a specific session."""
    session_id: str
    created_at: datetime
    mcp_servers: List[Dict[str, Any]]
    message_history: List[Dict[str, Any]]


class DeleteSessionResponse(BaseModel):
    """Response from deleting a session."""
    session_id: str
    message: str


class StreamEvent(BaseModel):
    """Streaming event data."""
    type: StreamEventType
    session_id: str
    data: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    active_sessions: int
    timestamp: Optional[datetime] = None