"""
Domain value objects.
"""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class StreamEventType(str, Enum):
    """Types of streaming events."""
    CONTENT = "content"
    DONE = "done"
    ERROR = "error"


class SessionId(BaseModel):
    """Session identifier value object."""
    value: str
    
    def __str__(self) -> str:
        return self.value