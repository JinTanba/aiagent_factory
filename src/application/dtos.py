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


# ===== NEW DTOs FOR SEPARATED ARCHITECTURE =====

class CreateConfigurationRequest(BaseModel):
    """Request to create a new agent configuration."""
    name: str = Field(description="Human-readable configuration name")
    mcp_servers: List[MCPServerConfig] = Field(
        description="List of MCP server configurations"
    )
    system_prompt: Optional[str] = Field(
        None, description="System prompt override"
    )
    model_settings: Optional[Dict[str, Any]] = Field(
        None, description="Model-specific settings"
    )


class CreateConfigurationResponse(BaseModel):
    """Response from creating a configuration."""
    config_id: str
    name: str
    message: str
    mcp_servers_count: int
    created_at: datetime


class StartConversationRequest(BaseModel):
    """Request to start a new conversation with a configuration."""
    config_id: str = Field(description="Configuration ID to use")
    session_id: Optional[str] = Field(
        None, description="Optional custom session ID"
    )


class StartConversationResponse(BaseModel):
    """Response from starting a conversation."""
    session_id: str
    config_id: str
    config_name: str
    message: str
    created_at: datetime


class ExecuteConversationRequest(BaseModel):
    """Request to execute a message in a conversation."""
    session_id: str = Field(description="Session ID of the conversation")
    message: str = Field(description="Message to send to the agent")
    stream: bool = Field(False, description="Whether to stream the response")


class ExecuteConversationResponse(BaseModel):
    """Response from executing a conversation message."""
    session_id: str
    response: str
    message_count: int


class ConfigurationSummary(BaseModel):
    """Summary information about an agent configuration."""
    config_id: str
    name: str
    mcp_servers_count: int
    created_at: datetime
    updated_at: datetime


class ListConfigurationsResponse(BaseModel):
    """Response listing all configurations."""
    configurations: List[ConfigurationSummary]


class ConversationSummary(BaseModel):
    """Summary information about a conversation."""
    session_id: str
    config_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ListConversationsResponse(BaseModel):
    """Response listing conversations."""
    conversations: List[ConversationSummary]