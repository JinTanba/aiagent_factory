"""
Simple implementation of agent repository using LangChain types.
"""

from typing import Any, Dict, List, Optional

from ..domain.entities import AgentExecuteParams
from ..domain.repositories import AgentRepository
from .agent_factory import AgentFactory


class LangChainAgentRepository(AgentRepository):
    """Simple LangChain implementation of the agent repository."""
    
    def __init__(self):
        self.agent_factory = AgentFactory()
        self.agent_instance: Optional[Any] = None
        
    async def create_agent(self, mcp_servers: List[Dict[str, Any]]) -> Any:
        """Create a new ReactAgent with MCP servers."""
        try:
            self.agent_instance = await self.agent_factory.create_agent(mcp_servers)
            return self.agent_instance
        except Exception as e:
            print(f"Agent creation error: {e}")
            raise RuntimeError(f"Failed to create agent: {str(e)}") from e
    
    async def ainvoke(self, params: AgentExecuteParams):
        """Execute ReactAgent with messages."""
        if not self.agent_instance:
            raise RuntimeError("Agent not created. Call create_agent first.")
        
        # Use LangGraph's ainvoke with proper message format
        result = await self.agent_instance.ainvoke({"messages": params.messages})
        return result

