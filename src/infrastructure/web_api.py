"""
Web API layer with FastAPI routes for multi-tenant agent system.
"""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from ..application.use_cases import (
    # New use cases
    CreateConfigurationUseCase, StartConversationUseCase, ExecuteConversationUseCase,
    ListConfigurationsUseCase, ListConversationsUseCase, DeleteConversationUseCase,
    GetConversationDetailsUseCase, HealthCheckUseCase,
)
from ..application.dtos import (
    # New DTOs
    CreateConfigurationRequest, CreateConfigurationResponse,
    StartConversationRequest, StartConversationResponse,
    ExecuteConversationRequest, ExecuteConversationResponse,
    ListConfigurationsResponse, ListConversationsResponse,
    DeleteSessionResponse, SessionDetailsResponse, HealthResponse
)
from ..domain.repositories import AgentConfigurationRepository, ConversationRepository
from ..aiagent.agent_factory import AgentFactory


class WebAPI:
    """FastAPI web application for multi-tenant agent system."""
    
    def __init__(self, config_repository: AgentConfigurationRepository,
                 conversation_repository: ConversationRepository,
                 agent_factory: AgentFactory):
        self.config_repository = config_repository
        self.conversation_repository = conversation_repository
        self.agent_factory = agent_factory
        
        # Initialize use cases
        self.create_config_use_case = CreateConfigurationUseCase(config_repository)
        self.start_conversation_use_case = StartConversationUseCase(
            config_repository, conversation_repository
        )
        self.execute_conversation_use_case = ExecuteConversationUseCase(
            config_repository, conversation_repository, agent_factory
        )
        self.list_configs_use_case = ListConfigurationsUseCase(config_repository)
        self.list_conversations_use_case = ListConversationsUseCase(conversation_repository)
        self.delete_conversation_use_case = DeleteConversationUseCase(conversation_repository)
        self.get_conversation_details_use_case = GetConversationDetailsUseCase(conversation_repository)
        self.health_check_use_case = HealthCheckUseCase(conversation_repository)
        
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.router.get("/", tags=["Info"])
        async def root():
            """API information endpoint."""
            return {
                "name": "BlackSwan Multi-Tenant Agent API",
                "version": "2.0.0",
                "description": "Multi-tenant AI agent system with separated configurations and conversations",
                "endpoints": {
                    "/configurations": "Manage agent configurations",
                    "/conversations": "Manage conversations",
                    "/health": "Health check"
                }
            }
        
        # ===== CONFIGURATION ENDPOINTS =====
        
        @self.router.post("/configurations", response_model=CreateConfigurationResponse, tags=["Configurations"])
        async def create_configuration(request: CreateConfigurationRequest):
            """Create a new agent configuration."""
            try:
                return await self.create_config_use_case.execute(request)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        
        @self.router.get("/configurations", response_model=ListConfigurationsResponse, tags=["Configurations"])
        async def list_configurations(active_only: bool = True):
            """List all agent configurations."""
            try:
                return await self.list_configs_use_case.execute(active_only=active_only)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        
        # ===== CONVERSATION ENDPOINTS =====
        
        @self.router.post("/conversations", response_model=StartConversationResponse, tags=["Conversations"])
        async def start_conversation(request: StartConversationRequest):
            """Start a new conversation with an existing configuration."""
            try:
                return await self.start_conversation_use_case.execute(request)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        
        @self.router.post("/conversations/execute", response_model=ExecuteConversationResponse, tags=["Conversations"])
        async def execute_conversation(request: ExecuteConversationRequest):
            """Execute a message in a conversation (non-streaming)."""
            try:
                if request.stream:
                    return StreamingResponse(
                        self._stream_conversation_response(request.session_id, request.message),
                        media_type="application/x-ndjson"
                    )
                else:
                    response, _ = await self.execute_conversation_use_case.execute(request, stream=False)
                    return response
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        
        @self.router.get("/conversations", response_model=ListConversationsResponse, tags=["Conversations"])
        async def list_conversations(config_id: Optional[str] = None, active_only: bool = True):
            """List conversations, optionally filtered by configuration."""
            try:
                return await self.list_conversations_use_case.execute(
                    config_id=config_id, active_only=active_only
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        
        @self.router.get("/conversations/{session_id}", response_model=SessionDetailsResponse, tags=["Conversations"])
        async def get_conversation(session_id: str):
            """Get detailed information about a conversation."""
            try:
                details = await self.get_conversation_details_use_case.execute(session_id)
                if not details:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Conversation {session_id} not found"
                    )
                return details
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        
        @self.router.delete("/conversations/{session_id}", response_model=DeleteSessionResponse, tags=["Conversations"])
        async def delete_conversation(session_id: str):
            """Delete a conversation."""
            try:
                result = await self.delete_conversation_use_case.execute(session_id)
                if not result:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Conversation {session_id} not found"
                    )
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        
        # ===== HEALTH ENDPOINT =====
        
        @self.router.get("/health", response_model=HealthResponse, tags=["Health"])
        async def health_check():
            """Health check endpoint."""
            try:
                return await self.health_check_use_case.execute()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
    
    async def _stream_conversation_response(self, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """Stream conversation response."""
        try:
            request = ExecuteConversationRequest(session_id=session_id, message=message, stream=True)
            response_gen = await self.execute_conversation_use_case.execute(request, stream=True)
            
            async for chunk in response_gen:
                event = {
                    "type": "message",
                    "session_id": session_id,
                    "data": chunk
                }
                yield f"data: {json.dumps(event)}\\n\\n"
            
            # Send completion event
            completion_event = {
                "type": "complete",
                "session_id": session_id
            }
            yield f"data: {json.dumps(completion_event)}\\n\\n"
            
        except ValueError as e:
            error_event = {
                "type": "error",
                "session_id": session_id,
                "error": str(e)
            }
            yield f"data: {json.dumps(error_event)}\\n\\n"
        except Exception as e:
            error_event = {
                "type": "error",
                "session_id": session_id,
                "error": f"Internal error: {str(e)}"
            }
            yield f"data: {json.dumps(error_event)}\\n\\n"
    
    def get_router(self) -> APIRouter:
        """Get the configured router."""
        return self.router


# Legacy router - deprecated but kept for backward compatibility
class AgentAPIRouter:
    """DEPRECATED: Legacy router for agent API endpoints."""
    
    def __init__(self, *args, **kwargs):
        self.router = APIRouter()
        self._setup_legacy_routes()
    
    def _setup_legacy_routes(self):
        """Setup legacy API routes that return deprecation warnings."""
        
        @self.router.post("/agents/create", tags=["Legacy - Deprecated"])
        async def create_agent_legacy():
            """DEPRECATED: Use POST /configurations instead."""
            raise HTTPException(
                status_code=410, 
                detail="This endpoint is deprecated. Use POST /configurations instead."
            )
        
        @self.router.post("/agents/execute", tags=["Legacy - Deprecated"])
        async def execute_agent_legacy():
            """DEPRECATED: Use POST /conversations/execute instead."""
            raise HTTPException(
                status_code=410, 
                detail="This endpoint is deprecated. Use POST /conversations/execute instead."
            )
        
        @self.router.get("/agents/sessions", tags=["Legacy - Deprecated"])
        async def list_sessions_legacy():
            """DEPRECATED: Use GET /conversations instead."""
            raise HTTPException(
                status_code=410, 
                detail="This endpoint is deprecated. Use GET /conversations instead."
            )