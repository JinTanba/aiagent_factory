"""
Usage examples for the clean architecture AI Agent system.
"""

import asyncio
from typing import List

from .infrastructure.repositories import InMemorySessionRepository
from .aiagent.agent_repository import LangChainAgentRepository
from .domain.services import SessionDomainService
from .domain.entities import MCPServerConfig
from .application.use_cases import CreateAgentUseCase, ExecuteAgentUseCase
from .application.dtos import CreateAgentRequest, ExecuteAgentRequest


async def example_usage():
    """Example of how to use the clean architecture system."""
    
    # Setup dependencies
    session_repository = InMemorySessionRepository()
    agent_repository = LangChainAgentRepository()
    session_domain_service = SessionDomainService(session_repository)
    
    # Create use cases
    create_agent_use_case = CreateAgentUseCase(
        session_repository, 
        agent_repository, 
        session_domain_service
    )
    execute_agent_use_case = ExecuteAgentUseCase(session_repository)
    
    # Example MCP server configuration
    mcp_servers = [
        MCPServerConfig(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={
                "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
            }
        )
    ]
    
    # Create agent
    create_request = CreateAgentRequest(mcp_servers=mcp_servers)
    create_response = await create_agent_use_case.execute(create_request)
    print(f"Created agent with session ID: {create_response.session_id}")
    
    # Execute message
    execute_request = ExecuteAgentRequest(
        session_id=create_response.session_id,
        message="What tools are available?",
        stream=False
    )
    
    response, session = await execute_agent_use_case.execute(execute_request)
    print(f"Agent response: {response}")


if __name__ == "__main__":
    asyncio.run(example_usage())