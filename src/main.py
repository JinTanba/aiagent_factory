"""
Main entry point for the multi-tenant AI Agent system.
"""

import asyncio
from fastapi import FastAPI
import uvicorn

from .infrastructure.mongodb_repositories import mongodb
from .infrastructure.web_api import WebAPI
from .infrastructure.config import config
from .aiagent.agent_factory import AgentFactory


class DIContainer:
    """Dependency Injection Container for multi-tenant architecture."""
    
    def __init__(self):
        # Infrastructure Layer - MongoDB repositories
        self.config_repository = None  # Will be set after MongoDB connection
        self.conversation_repository = None  # Will be set after MongoDB connection
        
        # AI Agent Layer
        self.agent_factory = AgentFactory()
        
        # Web API Layer
        self.web_api = None  # Will be set after repositories are initialized
    
    async def initialize(self):
        """Initialize all dependencies including MongoDB connection."""
        # Connect to MongoDB
        await mongodb.connect()
        
        # Set repositories
        self.config_repository = mongodb.config_repository
        self.conversation_repository = mongodb.conversation_repository
        
        # Initialize Web API with repositories
        self.web_api = WebAPI(
            self.config_repository,
            self.conversation_repository,
            self.agent_factory
        )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="BlackSwan Multi-Tenant Agent API",
        description="Multi-tenant AI agent system with separated configurations and conversations",
        version="2.0.0",
    )
    
    # Initialize DI container
    container = DIContainer()
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize dependencies on startup."""
        await container.initialize()
        
        # Include the API router after initialization
        app.include_router(container.web_api.get_router())
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        await mongodb.disconnect()
    
    return app


def main():
    """Main entry point."""
    # Validate configuration
    if not config.mongodb_url:
        print("ERROR: MongoDB URL not configured. Please set MONGODB_URL environment variable.")
        print("Example: export MONGODB_URL='mongodb://localhost:27017'")
        return
    
    if not config.openai_api_key:
        print("ERROR: OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        return
    
    print(f"Starting BlackSwan Multi-Tenant Agent API...")
    print(f"MongoDB: {config.mongodb_database}")
    print(f"OpenAI Model: {config.openai_model}")
    print(f"Server: http://{config.host}:{config.port}")
    
    app = create_app()
    
    uvicorn.run(
        app, 
        host=config.host, 
        port=config.port, 
        reload=config.debug
    )


if __name__ == "__main__":
    main()