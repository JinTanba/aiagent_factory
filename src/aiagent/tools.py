"""
Built-in tools for the AI agent.
"""

from typing import List, Annotated
from langchain_core.tools import tool, BaseTool


@tool
def add(a: Annotated[int | float, "First number"], b: Annotated[int | float, "Second number"]) -> float:
    """Add two numbers together."""
    return a + b


def get_builtin_tools() -> List[BaseTool]:
    """Get list of builtin tools."""
    return [add]