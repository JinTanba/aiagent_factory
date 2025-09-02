"""
Simple MCP client for integrating with external MCP servers.
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient


class MCPClientService:
    """Simple service for managing MCP client connections and tools."""
    
    def __init__(self):
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.tools: List[BaseTool] = []
    
    async def get_tools_from_servers(self, mcp_servers: List[Dict[str, Any]]) -> List[BaseTool]:
        """Initialize and get tools from MCP servers."""
        if not mcp_servers:
            return []
        
        try:
            # Convert list to dict format expected by MultiServerMCPClient
            servers_dict = {
                server["name"]: {
                    "command": server["command"],
                    "args": server["args"],
                    "env": server.get("env", {}),
                    "transport": server.get("transport", "stdio")
                }
                for server in mcp_servers
            }
            
            # Initialize MCP client
            self.mcp_client = MultiServerMCPClient(servers_dict)
            
            # Get tools from all servers
            self.tools = await self.mcp_client.get_tools()
            return self.tools
            
        except Exception as e:
            print(f"Warning: Failed to initialize MCP servers: {e}")
            return []  # Return empty list on failure, don't crash
    
    async def close(self):
        """Close MCP client connections."""
        if self.mcp_client:
            # Cleanup if needed
            pass