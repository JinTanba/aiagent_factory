"""
Main entry point for the clean architecture AI Agent system.
"""

from fastapi import FastAPI
import uvicorn

from .infrastructure.repositories import InMemorySessionRepository
from .infrastructure.web_api import AgentAPIRouter
from .infrastructure.config import config

from .aiagent.agent_repository import LangChainAgentRepository

from .domain.services import SessionDomainService

from .application.use_cases import (
    CreateAgentUseCase, ExecuteAgentUseCase, ListSessionsUseCase,
    GetSessionDetailsUseCase, DeleteSessionUseCase, HealthCheckUseCase
)


class DIContainer:
    """Dependency Injection Container."""
    
    def __init__(self):
        # Infrastructure Layer
        self.session_repository = InMemorySessionRepository()
        self.agent_repository = LangChainAgentRepository()
        
        # Domain Layer
        self.session_domain_service = SessionDomainService(self.session_repository)
        
        # Application Layer
        self.create_agent_use_case = CreateAgentUseCase(
            self.session_repository, 
            self.agent_repository, 
            self.session_domain_service
        )
        self.execute_agent_use_case = ExecuteAgentUseCase(self.session_repository)
        self.list_sessions_use_case = ListSessionsUseCase(self.session_repository)
        self.get_session_details_use_case = GetSessionDetailsUseCase(self.session_repository)
        self.delete_session_use_case = DeleteSessionUseCase(self.session_repository)
        self.health_check_use_case = HealthCheckUseCase(self.session_repository)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MCP Agent API",
        description="AI Agent system with MCP server integration",
        version="2.0.0",
    )
    
    # Initialize DI container
    container = DIContainer()
    
    # Create API router
    api_router = AgentAPIRouter(
        create_agent_use_case=container.create_agent_use_case,
        execute_agent_use_case=container.execute_agent_use_case,
        list_sessions_use_case=container.list_sessions_use_case,
        get_session_details_use_case=container.get_session_details_use_case,
        delete_session_use_case=container.delete_session_use_case,
        health_check_use_case=container.health_check_use_case
    )
    
    # Include router
    app.include_router(api_router.router)
    
    return app


def main():
    """Main entry point."""
    app = create_app()
    
    uvicorn.run(
        app, 
        host=config.host, 
        port=config.port, 
        reload=config.debug
    )


if __name__ == "__main__":
    main()