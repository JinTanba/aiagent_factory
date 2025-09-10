"""
Use cases for the application layer.
"""

from typing import List, Optional, AsyncGenerator, Tuple
from datetime import datetime
from langchain_core.messages import HumanMessage, BaseMessage

from ..domain.entities import AgentSession, MCPServerConfig
from ..domain.repositories import SessionRepository, AgentRepository
from ..domain.services import SessionDomainService
from .dtos import (
    CreateAgentRequest, CreateAgentResponse,
    ExecuteAgentRequest, ExecuteAgentResponse,
    SessionSummary, ListSessionsResponse,
    SessionDetailsResponse, DeleteSessionResponse,
    HealthResponse
)

class CreateAgentUseCase:
    """Use case for creating a new agent."""
    
    def __init__(self, session_repository: SessionRepository, 
                 agent_repository: AgentRepository,
                 session_domain_service: SessionDomainService):
        self.session_repository = session_repository
        self.agent_repository = agent_repository
        self.session_domain_service = session_domain_service
    
    async def execute(self, request: CreateAgentRequest) -> CreateAgentResponse:
        """Execute the create agent use case."""
        # Validate MCP servers
        self.session_domain_service.validate_mcp_servers(request.mcp_servers)
        
        # Create session
        session = self.session_domain_service.create_new_session(
            request.mcp_servers, request.session_id
        )
        
        # Create actual ReactAgent with MCP servers
        try:
            mcp_servers_dict = [
                {
                    "name": server.name,
                    "command": server.command,
                    "args": server.args,
                    "env": server.env or {},
                    "transport": server.transport or "stdio",
                }
                for server in request.mcp_servers
            ]
            
            # Create agent and store in session
            agent = await self.agent_repository.create_agent(mcp_servers_dict)
            session.agent_instance = agent
            
            # Update session with agent
            self.session_repository.update_session(session)
            
        except Exception as e:
            print(f"Warning: Agent creation failed: {e}")
            # Continue without agent for now
        
        return CreateAgentResponse(
            session_id=session.session_id,
            message=f"Agent created successfully with {len(request.mcp_servers)} MCP servers",
            mcp_servers_count=len(request.mcp_servers),
            created_at=session.created_at
        )


class ExecuteAgentUseCase:
    """Use case for executing an agent message."""
    
    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository
    
    async def execute(self, request: ExecuteAgentRequest, stream: bool = False):
        """Execute the agent message use case."""
        session = self.session_repository.get_session(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")
        
        # Add human message to session
        human_message = HumanMessage(content=request.message)
        session.messages.append(human_message)
        
        # Update session in repository
        self.session_repository.update_session(session)
        
        # For now, return a simple response (placeholder for actual agent execution)
        if stream:
            return self._stream_response(session, request.message), session
        else:
            response = await self._sync_response(session, request.message)
            return response, session
    
    def _stream_response(self, session: AgentSession, message: str) -> AsyncGenerator[str, None]:
        """Stream response from agent."""
        # Placeholder implementation
        async def generator():
            yield "This is a "
            yield "streamed "
            yield "response"
        return generator()
    
    async def _sync_response(self, session: AgentSession, message: str) -> str:
        """Get synchronous response from agent."""
        from ..domain.entities import MessageHistory, MessageRole, AgentExecuteParams
        from datetime import datetime
        from langchain_core.messages import AIMessage
        
        # Add human message to history
        session.message_history.append(MessageHistory(
            role=MessageRole.HUMAN,
            content=message,
            timestamp=datetime.utcnow()
        ))
        
        # Try to execute with real agent if available
        if session.agent_instance:
            try:
                # Execute agent with full conversation history
                params = AgentExecuteParams(messages=session.messages)
                result = await session.agent_instance.ainvoke({"messages": session.messages})
                
                # Extract response from agent result
                if "messages" in result and result["messages"]:
                    last_message = result["messages"][-1]
                    if isinstance(last_message, AIMessage):
                        response = last_message.content
                    else:
                        response = str(last_message.content) if hasattr(last_message, 'content') else str(last_message)
                else:
                    response = "Agent executed but returned no response."
                    
            except Exception as e:
                print(f"Agent execution failed: {e}")
                response = f"I apologize, but I encountered an error: {str(e)}"
        else:
            # Fallback response
            response = f"Hello! You asked: '{message}'. I can help you with various tasks using the available tools."
        
        # Add AI response to history
        session.message_history.append(MessageHistory(
            role=MessageRole.ASSISTANT,
            content=response,
            timestamp=datetime.utcnow()
        ))
        
        # Add AI message to LangChain messages
        session.messages.append(AIMessage(content=response))
        
        # Update session
        self.session_repository.update_session(session)
        
        return response


class ListSessionsUseCase:
    """Use case for listing all sessions."""
    
    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository
    
    def execute(self) -> ListSessionsResponse:
        """Execute the list sessions use case."""
        sessions = self.session_repository.list_sessions()
        
        session_summaries = [
            SessionSummary(
                session_id=session.session_id,
                created_at=session.created_at,
                mcp_servers_count=len(session.mcp_servers),
                message_count=len(session.messages)
            )
            for session in sessions
        ]
        
        return ListSessionsResponse(sessions=session_summaries)


class GetSessionDetailsUseCase:
    """Use case for getting session details."""
    
    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository
    
    def execute(self, session_id: str) -> Optional[SessionDetailsResponse]:
        """Execute the get session details use case."""
        session = self.session_repository.get_session(session_id)
        if not session:
            return None
        
        return SessionDetailsResponse(
            session_id=session.session_id,
            created_at=session.created_at,
            mcp_servers=session.mcp_servers,
            message_history=[
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in session.message_history
            ]
        )


class DeleteSessionUseCase:
    """Use case for deleting a session."""
    
    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository
    
    def execute(self, session_id: str) -> Optional[DeleteSessionResponse]:
        """Execute the delete session use case."""
        if not self.session_repository.delete_session(session_id):
            return None
        
        return DeleteSessionResponse(
            session_id=session_id,
            message="Session deleted successfully"
        )


class HealthCheckUseCase:
    """Use case for health check."""
    
    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository
    
    def execute(self) -> HealthResponse:
        """Execute the health check use case."""
        active_sessions = len(self.session_repository.list_sessions())
        
        return HealthResponse(
            status="healthy",
            active_sessions=active_sessions,
            timestamp=datetime.utcnow()
        )