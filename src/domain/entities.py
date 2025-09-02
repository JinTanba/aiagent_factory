"""
Domain entities representing core business concepts.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage
from enum import Enum


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


class AgentSession(BaseModel):
    """Agent session domain entity."""
    session_id: str
    mcp_servers: List[Dict[str, Any]]
    created_at: datetime
    messages: List[BaseMessage] = Field(default_factory=list)
    message_history: List[MessageHistory] = Field(default_factory=list)
    agent_instance: Optional[Any] = Field(None, exclude=True)  # Store agent, exclude from serialization
    
    class Config:
        arbitrary_types_allowed = True

class AgentExecuteParams(BaseModel):
    """Params to execute Agent"""
    messages: List[BaseMessage] = Field(default_factory=list)
    additional_mcp: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True