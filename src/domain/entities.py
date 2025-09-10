"""
Domain entities representing core business concepts.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage
from enum import Enum
import uuid


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    name: str = Field(description="Unique identifier for the MCP server")
    command: str = Field(description="Command to execute the MCP server")
    args: List[str] = Field(description="Arguments for the command")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    transport: Optional[str] = Field("stdio", description="Transport protocol")


class MessageRole(str, Enum):
    """Message roles for conversation history."""
    HUMAN = "human"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageHistory(BaseModel):
    """Message history entry for logging/API responses."""
    role: MessageRole
    content: str
    timestamp: datetime


class AgentConfiguration(BaseModel):
    """Reusable agent configuration entity."""
    config_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(description="Human-readable configuration name")
    mcp_servers: List[MCPServerConfig] = Field(description="MCP server configurations")
    system_prompt: Optional[str] = Field(None, description="System prompt override")
    model_settings: Optional[Dict[str, Any]] = Field(None, description="Model-specific settings")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(True, description="Whether configuration is active")


class ConversationSession(BaseModel):
    """Conversation session entity - execution results for a specific configuration."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config_id: str = Field(description="References AgentConfiguration")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[BaseMessage] = Field(default_factory=list)
    message_history: List[MessageHistory] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional session metadata")
    active: bool = Field(True, description="Whether session is active")
    
    class Config:
        arbitrary_types_allowed = True


class AgentExecuteParams(BaseModel):
    """Parameters to execute Agent"""
    messages: List[BaseMessage] = Field(default_factory=list)
    config_id: str = Field(description="Configuration ID to use")
    
    class Config:
        arbitrary_types_allowed = True


# Legacy entity for backward compatibility - will be removed later
class AgentSession(BaseModel):
    """Legacy agent session entity - deprecated."""
    session_id: str
    mcp_servers: List[Dict[str, Any]]
    created_at: datetime
    messages: List[BaseMessage] = Field(default_factory=list)
    message_history: List[MessageHistory] = Field(default_factory=list)
    agent_instance: Optional[Any] = Field(None, exclude=True)
    
    class Config:
        arbitrary_types_allowed = True