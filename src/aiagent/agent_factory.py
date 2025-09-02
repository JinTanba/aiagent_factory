"""
Simple factory for creating ReactAgents with MCP integration.
"""

from typing import Any, Dict, List
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool
# from langgraph.graph.graph import CompiledGraph

from .mcp_client import MCPClientService
from .tools import get_builtin_tools
from ..infrastructure.config import config


class AgentFactory:
    """Simple factory for creating ReactAgents."""
    
    def __init__(self):
        self.mcp_client_service = MCPClientService()
    
    async def create_agent(self, mcp_servers: List[Dict[str, Any]]) -> Any:
        """Create a ReactAgent with MCP server tools."""
        # Get MCP tools
        mcp_tools = await self.mcp_client_service.get_tools_from_servers(mcp_servers)
        
        # Get builtin tools  
        builtin_tools = get_builtin_tools()
        
        # Combine all tools
        all_tools: List[BaseTool] = mcp_tools + builtin_tools
        
        # Create LLM
        llm = ChatOpenAI(
            model=config.openai_model,
            api_key=config.openai_api_key,
            temperature=0
        )
        
        # Create ReactAgent (simple approach)
        agent = create_react_agent(
            model=llm,
            tools=all_tools
        )
        
        return agent