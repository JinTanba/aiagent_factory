"""
Web API infrastructure layer.
"""

import json
from datetime import datetime
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..application.dtos import (
    CreateAgentRequest, CreateAgentResponse, ExecuteAgentRequest, ExecuteAgentResponse,
    ListSessionsResponse, DeleteSessionResponse, HealthResponse, StreamEvent, StreamEventType
)
from ..application.use_cases import (
    CreateAgentUseCase, ExecuteAgentUseCase, ListSessionsUseCase,
    GetSessionDetailsUseCase, DeleteSessionUseCase, HealthCheckUseCase
)


class AgentAPIRouter:
    """Router for agent API endpoints."""
    
    def __init__(self, 
                 create_agent_use_case: CreateAgentUseCase,
                 execute_agent_use_case: ExecuteAgentUseCase,
                 list_sessions_use_case: ListSessionsUseCase,
                 get_session_details_use_case: GetSessionDetailsUseCase,
                 delete_session_use_case: DeleteSessionUseCase,
                 health_check_use_case: HealthCheckUseCase):
        self.create_agent_use_case = create_agent_use_case
        self.execute_agent_use_case = execute_agent_use_case
        self.list_sessions_use_case = list_sessions_use_case
        self.get_session_details_use_case = get_session_details_use_case
        self.delete_session_use_case = delete_session_use_case
        self.health_check_use_case = health_check_use_case
        
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.router.get("/", tags=["General"])
        async def root():
            """Root endpoint with API information."""
            return {
                "message": "MCP Agent API",
                "version": "2.0.0",
                "endpoints": {
                    "/agents/create": "Create a new agent with MCP configurations",
                    "/agents/execute": "Execute a message with an existing agent",
                    "/agents/sessions": "List all active sessions",
                    "/agents/sessions/{session_id}": "Get or delete a specific session",
                    "/health": "Health check endpoint",
                },
            }
        
        @self.router.get("/health", response_model=HealthResponse, tags=["Health"])
        async def health_check():
            """Health check endpoint."""
            return self.health_check_use_case.execute()
        
        @self.router.post("/agents/create", response_model=CreateAgentResponse, tags=["Agents"])
        async def create_agent(request: CreateAgentRequest):
            """Create a new agent with the specified MCP server configurations."""
            try:
                return await self.create_agent_use_case.execute(request)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/agents/execute", tags=["Agents"])
        async def execute_agent(request: ExecuteAgentRequest):
            """Execute a message with an existing agent session."""
            try:
                if request.stream:
                    return StreamingResponse(
                        self._stream_agent_response(request.session_id, request.message),
                        media_type="text/event-stream",
                    )
                else:
                    response, session = await self.execute_agent_use_case.execute(request, stream=False)
                    
                    return ExecuteAgentResponse(
                        session_id=request.session_id,
                        response=response,
                        timestamp=datetime.utcnow()
                    )
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/agents/sessions", response_model=ListSessionsResponse, tags=["Sessions"])
        async def list_sessions():
            """List all active agent sessions."""
            return self.list_sessions_use_case.execute()
        
        @self.router.get("/agents/sessions/{session_id}", tags=["Sessions"])
        async def get_session(session_id: str):
            """Get details of a specific session."""
            details = self.get_session_details_use_case.execute(session_id)
            if not details:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Session {session_id} not found"
                )
            return details
        
        @self.router.delete("/agents/sessions/{session_id}", response_model=DeleteSessionResponse, tags=["Sessions"])
        async def delete_session(session_id: str):
            """Delete a specific session."""
            result = self.delete_session_use_case.execute(session_id)
            if not result:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Session {session_id} not found"
                )
            return result
    
    async def _stream_agent_response(self, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """Stream agent response as Server-Sent Events."""
        try:
            request = ExecuteAgentRequest(session_id=session_id, message=message, stream=True)
            response_generator, session = await self.execute_agent_use_case.execute(request, stream=True)
            
            if response_generator is None:
                event_data = json.dumps({
                    "type": StreamEventType.ERROR,
                    "session_id": session_id,
                    "error": f"Session {session_id} not found"
                })
                yield f"data: {event_data}\n\n"
                return
            
            async for content in response_generator:
                event_data = json.dumps({
                    "type": StreamEventType.CONTENT,
                    "session_id": session_id,
                    "data": content
                })
                yield f"data: {event_data}\n\n"
            
            # Send completion event
            event_data = json.dumps({
                "type": StreamEventType.DONE,
                "session_id": session_id
            })
            yield f"data: {event_data}\n\n"
        
        except Exception as e:
            event_data = json.dumps({
                "type": StreamEventType.ERROR,
                "session_id": session_id,
                "error": str(e)
            })
            yield f"data: {event_data}\n\n"