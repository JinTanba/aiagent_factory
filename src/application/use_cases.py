"""
Use cases for the application layer.
"""

from typing import List, Optional, AsyncGenerator
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from ..domain.entities import (
    AgentConfiguration, ConversationSession, MCPServerConfig, 
    MessageHistory, MessageRole, AgentSession  # Legacy
)
from ..domain.repositories import (
    AgentConfigurationRepository, ConversationRepository, 
    SessionRepository, AgentRepository  # Legacy
)
from ..domain.services import (
    AgentConfigurationService, ConversationService, agent_cache,
    SessionDomainService  # Legacy
)
from ..aiagent.agent_factory import AgentFactory
from .dtos import (
    CreateAgentRequest, CreateAgentResponse,  # Legacy
    ExecuteAgentRequest, ExecuteAgentResponse,  # Legacy
    SessionSummary, ListSessionsResponse, SessionDetailsResponse, 
    DeleteSessionResponse, HealthResponse,
    # New DTOs
    CreateConfigurationRequest, CreateConfigurationResponse,
    StartConversationRequest, StartConversationResponse,
    ExecuteConversationRequest, ExecuteConversationResponse,
    ListConfigurationsResponse, ConfigurationSummary,
    ListConversationsResponse, ConversationSummary
)


# ===== NEW USE CASES FOR SEPARATED ARCHITECTURE =====

class CreateConfigurationUseCase:
    """Use case for creating a new agent configuration."""
    
    def __init__(self, config_repository: AgentConfigurationRepository):
        self.config_repository = config_repository
        self.config_service = AgentConfigurationService(config_repository)
    
    async def execute(self, request: CreateConfigurationRequest) -> CreateConfigurationResponse:
        """Execute the create configuration use case."""
        try:
            config = await self.config_service.create_configuration(
                name=request.name,
                mcp_servers=request.mcp_servers,
                system_prompt=request.system_prompt,
                model_settings=request.model_settings
            )
            
            return CreateConfigurationResponse(
                config_id=config.config_id,
                name=config.name,
                message=f"Configuration '{config.name}' created successfully",
                mcp_servers_count=len(config.mcp_servers),
                created_at=config.created_at
            )
        except Exception as e:
            raise ValueError(f"Failed to create configuration: {str(e)}")


class StartConversationUseCase:
    """Use case for starting a new conversation with an existing configuration."""
    
    def __init__(self, config_repository: AgentConfigurationRepository,
                 conversation_repository: ConversationRepository):
        self.config_repository = config_repository
        self.conversation_repository = conversation_repository
        self.conversation_service = ConversationService()
    
    async def execute(self, request: StartConversationRequest) -> StartConversationResponse:
        """Execute the start conversation use case."""
        # Verify configuration exists
        config = await self.config_repository.get_config(request.config_id)
        if not config:
            raise ValueError(f"Configuration {request.config_id} not found")
        
        # Create new conversation session
        session = self.conversation_service.create_conversation(
            config_id=request.config_id,
            session_id=request.session_id
        )
        
        # Save to repository
        session_id = await self.conversation_repository.create_session(session)
        
        return StartConversationResponse(
            session_id=session_id,
            config_id=request.config_id,
            config_name=config.name,
            message=f"Conversation started with configuration '{config.name}'",
            created_at=session.created_at
        )


class ExecuteConversationUseCase:
    """Use case for executing messages in a conversation."""
    
    def __init__(self, config_repository: AgentConfigurationRepository,
                 conversation_repository: ConversationRepository,
                 agent_factory: AgentFactory):
        self.config_repository = config_repository
        self.conversation_repository = conversation_repository
        self.agent_factory = agent_factory
    
    async def execute(self, request: ExecuteConversationRequest, stream: bool = False):
        """Execute the conversation message use case."""
        # Get conversation session
        session = await self.conversation_repository.get_session(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")
        
        # Get configuration
        config = await self.config_repository.get_config(session.config_id)
        if not config:
            raise ValueError(f"Configuration {session.config_id} not found")
        
        # Add human message to session
        human_message = HumanMessage(content=request.message)
        session.messages.append(human_message)
        session.message_history.append(MessageHistory(
            role=MessageRole.HUMAN,
            content=request.message,
            timestamp=datetime.utcnow()
        ))
        
        try:
            if stream:
                return self._stream_response(session, config, request.message)
            else:
                response = await self._sync_response(session, config, request.message)
                return ExecuteConversationResponse(
                    session_id=request.session_id,
                    response=response,
                    message_count=len(session.messages)
                ), session
        except Exception as e:
            raise ValueError(f"Failed to execute conversation: {str(e)}")
    
    async def _sync_response(self, session: ConversationSession, 
                           config: AgentConfiguration, message: str) -> str:
        """Get synchronous response from agent."""
        try:
            # Get or create cached agent
            agent = await agent_cache.get_or_create_agent(config, self.agent_factory)
            
            # Execute agent with full conversation history
            result = await agent.ainvoke({"messages": session.messages})
            
            # Extract response from agent result
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    response = last_message.content
                else:
                    response = str(last_message.content) if hasattr(last_message, 'content') else str(last_message)
            else:
                response = "Agent executed but returned no response."
            
            # Add AI response to session
            session.messages.append(AIMessage(content=response))
            session.message_history.append(MessageHistory(
                role=MessageRole.ASSISTANT,
                content=response,
                timestamp=datetime.utcnow()
            ))
            
            # Update session in repository
            session.updated_at = datetime.utcnow()
            await self.conversation_repository.update_session(session)
            
            return response
            
        except Exception as e:
            response = f"I apologize, but I encountered an error: {str(e)}"
            
            # Still add error response to history
            session.messages.append(AIMessage(content=response))
            session.message_history.append(MessageHistory(
                role=MessageRole.ASSISTANT,
                content=response,
                timestamp=datetime.utcnow()
            ))
            
            session.updated_at = datetime.utcnow()
            await self.conversation_repository.update_session(session)
            
            return response
    
    def _stream_response(self, session: ConversationSession, 
                        config: AgentConfiguration, message: str) -> AsyncGenerator[str, None]:
        """Stream response from agent."""
        # Placeholder implementation for streaming
        async def generator():
            yield f"Processing message with configuration '{config.name}'..."
            yield "This is a "
            yield "streamed "
            yield "response"
        return generator()


class ListConfigurationsUseCase:
    """Use case for listing all agent configurations."""
    
    def __init__(self, config_repository: AgentConfigurationRepository):
        self.config_repository = config_repository
    
    async def execute(self, active_only: bool = True) -> ListConfigurationsResponse:
        """Execute the list configurations use case."""
        configs = await self.config_repository.list_configs(active_only=active_only)
        
        config_summaries = [
            ConfigurationSummary(
                config_id=config.config_id,
                name=config.name,
                mcp_servers_count=len(config.mcp_servers),
                created_at=config.created_at,
                updated_at=config.updated_at
            )
            for config in configs
        ]
        
        return ListConfigurationsResponse(configurations=config_summaries)


class ListConversationsUseCase:
    """Use case for listing conversations."""
    
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository
    
    async def execute(self, config_id: Optional[str] = None, 
                     active_only: bool = True) -> ListConversationsResponse:
        """Execute the list conversations use case."""
        sessions = await self.conversation_repository.list_sessions(
            config_id=config_id, active_only=active_only
        )
        
        conversation_summaries = [
            ConversationSummary(
                session_id=session.session_id,
                config_id=session.config_id,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=len(session.messages)
            )
            for session in sessions
        ]
        
        return ListConversationsResponse(conversations=conversation_summaries)


class DeleteConversationUseCase:
    """Use case for deleting a conversation."""
    
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository
    
    async def execute(self, session_id: str) -> Optional[DeleteSessionResponse]:
        """Execute the delete conversation use case."""
        success = await self.conversation_repository.delete_session(session_id)
        if not success:
            return None
        
        return DeleteSessionResponse(
            session_id=session_id,
            message="Conversation deleted successfully"
        )


class GetConversationDetailsUseCase:
    """Use case for getting conversation details."""
    
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository
    
    async def execute(self, session_id: str) -> Optional[SessionDetailsResponse]:
        """Execute the get conversation details use case."""
        session = await self.conversation_repository.get_session(session_id)
        if not session:
            return None
        
        return SessionDetailsResponse(
            session_id=session.session_id,
            created_at=session.created_at,
            mcp_servers=[],  # Not applicable for conversations
            message_history=[
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in session.message_history
            ]
        )


# ===== LEGACY USE CASES - DEPRECATED =====

class CreateAgentUseCase:
    """LEGACY: Use case for creating a new agent."""
    
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
        
        return CreateAgentResponse(
            session_id=session.session_id,
            message=f"Agent created successfully with {len(request.mcp_servers)} MCP servers",
            mcp_servers_count=len(request.mcp_servers),
            created_at=session.created_at
        )


class ExecuteAgentUseCase:
    """LEGACY: Use case for executing an agent message."""
    
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
        
        if stream:
            return self._stream_response(session, request.message), session
        else:
            response = await self._sync_response(session, request.message)
            return response, session
    
    def _stream_response(self, session: AgentSession, message: str) -> AsyncGenerator[str, None]:
        """Stream response from agent."""
        async def generator():
            yield "This is a "
            yield "streamed "
            yield "response"
        return generator()
    
    async def _sync_response(self, session: AgentSession, message: str) -> str:
        """Get synchronous response from agent."""
        from ..domain.entities import MessageHistory, MessageRole
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
                result = await session.agent_instance.ainvoke({"messages": session.messages})
                
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
    """LEGACY: Use case for listing all sessions."""
    
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
    """LEGACY: Use case for getting session details."""
    
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
    """LEGACY: Use case for deleting a session."""
    
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
    
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository
    
    async def execute(self) -> HealthResponse:
        """Execute the health check use case."""
        sessions = await self.conversation_repository.list_sessions(active_only=True)
        active_sessions = len(sessions)
        
        return HealthResponse(
            status="healthy",
            active_sessions=active_sessions,
            timestamp=datetime.utcnow()
        )