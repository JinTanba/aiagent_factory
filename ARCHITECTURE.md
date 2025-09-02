# Clean Architecture for MCP Agent System

This project follows Clean Architecture principles to create a maintainable and testable AI Agent system that can accept any MCP (Model Context Protocol) server from the outside.

## Architecture Overview

The system is organized into 4 main layers:

```
src/
├── domain/          # Core business logic and entities
├── application/     # Use cases and application services
├── infrastructure/  # External concerns (web, database, etc.)
└── aiagent/        # AI Agent and MCP integration layer
```

## Layer Responsibilities

### 1. Domain Layer (`src/domain/`)
- **Entities**: Core business objects (`AgentSession`, `MCPServerConfig`)
- **Value Objects**: Immutable objects representing concepts (`SessionId`, `StreamEventType`)
- **Repository Interfaces**: Contracts for data access
- **Domain Services**: Business logic that doesn't fit in entities

**Key Files:**
- `entities.py` - Core domain entities
- `value_objects.py` - Domain value objects
- `repositories.py` - Repository interfaces
- `services.py` - Domain services

### 2. Application Layer (`src/application/`)
- **Use Cases**: Application-specific business rules
- **DTOs**: Data transfer objects for API communication
- **Interfaces**: Contracts for external services

**Key Files:**
- `use_cases.py` - Application use cases
- `dtos.py` - Data transfer objects

### 3. Infrastructure Layer (`src/infrastructure/`)
- **Repository Implementations**: Concrete implementations of domain repositories
- **Web API**: FastAPI routes and controllers
- **Configuration**: Application configuration management

**Key Files:**
- `repositories.py` - Concrete repository implementations
- `web_api.py` - FastAPI routing and controllers
- `config.py` - Application configuration

### 4. AI Agent Layer (`src/aiagent/`)
- **MCP Client**: Integration with MCP servers
- **Agent Factory**: Creates AI agents with MCP integration
- **Tools**: Built-in and MCP tools management
- **Agent Repository**: AI agent creation and management

**Key Files:**
- `mcp_client.py` - MCP server integration
- `agent_factory.py` - AI agent creation
- `tools.py` - Built-in tools
- `agent_repository.py` - Agent repository implementation

## Core Components

### 1. Models (`models.py`)

**Purpose**: Define all data structures and types used throughout the application.

**Key Models**:
- `MCPServerConfig`: Configuration for MCP servers
- `AgentSession`: Session data model
- `CreateAgentRequest/Response`: API request/response models
- `ExecuteAgentRequest/Response`: Message execution models
- `MessageHistory`: Conversation history structure
- `StreamEvent`: Streaming event types

**Benefits**:
- Type safety with Pydantic validation
- Clear data contracts
- Centralized model definitions

### 2. Services Layer

#### AgentService (`services/agent_service.py`)

**Purpose**: Handle all agent-related operations.

**Key Methods**:
- `create_agent()`: Create agents with MCP configurations
- `execute_agent_sync()`: Synchronous agent execution
- `stream_agent_response()`: Streaming agent responses

**Responsibilities**:
- Agent creation and configuration
- Message processing
- Response formatting

#### SessionService (`services/session_service.py`)

**Purpose**: Manage agent sessions and conversation state.

**Key Methods**:
- `create_session()`: Create new agent sessions
- `execute_message()`: Execute messages with conversation history
- `get_session()`, `list_sessions()`: Session retrieval
- `delete_session()`: Session cleanup

**Responsibilities**:
- Session lifecycle management
- Conversation history tracking
- Message routing

### 3. API Layer (`api/routes.py`)

**Purpose**: Handle HTTP requests and responses.

**Key Endpoints**:
- `POST /agents/create`: Create new agents
- `POST /agents/execute`: Execute messages
- `GET /agents/sessions`: List sessions
- `GET/DELETE /agents/sessions/{id}`: Session operations
- `GET /health`: Health check

**Responsibilities**:
- Request validation
- Response formatting
- Error handling
- Streaming support

### 4. Application Entry Point (`main.py`)

**Purpose**: Configure and start the FastAPI application.

**Responsibilities**:
- Application setup
- Route registration
- Server configuration

## Key Benefits of the New Architecture

### 1. **Separation of Concerns**
- API logic separated from business logic
- Session management isolated from agent operations
- Clear responsibility boundaries

### 2. **Testability**
- Services can be unit tested independently
- Mock services for integration testing
- Clear interfaces for testing

### 3. **Maintainability**
- Changes to one layer don't affect others
- Easy to modify or extend functionality
- Clear code organization

### 4. **Reusability**
- Services can be reused across different API endpoints
- Agent logic independent of HTTP layer
- Modular design allows component reuse

### 5. **Type Safety**
- Pydantic models provide runtime validation
- Clear type definitions throughout
- IDE support and error catching

## Design Patterns Used

### 1. **Service Pattern**
- Business logic encapsulated in service classes
- Clear service interfaces
- Dependency injection ready

### 2. **Repository Pattern (Implicit)**
- SessionService acts as a repository for sessions
- Abstract data access from business logic
- In-memory storage can be easily replaced

### 3. **Factory Pattern**
- AgentService.create_agent() acts as a factory
- Encapsulates agent creation complexity
- Configurable agent creation

### 4. **Request/Response Pattern**
- Clear API contracts with request/response models
- Validation at API boundaries
- Consistent response formats

## Conversation History Implementation

The refactored architecture properly handles conversation history:

1. **Message Storage**: Both LangChain `BaseMessage` objects and serializable `MessageHistory` entries
2. **Context Passing**: Full conversation history passed to agents
3. **Memory Management**: Proper message lifecycle tracking
4. **Type Safety**: Strongly typed message handling

## Error Handling

The new architecture provides comprehensive error handling:

- **Validation Errors**: Pydantic models catch invalid input
- **Business Logic Errors**: Services raise specific exceptions
- **API Errors**: Routes convert exceptions to HTTP responses
- **Streaming Errors**: Proper error events in streams

## Testing Strategy

### Unit Tests
- Test services independently
- Mock dependencies
- Test business logic isolation

### Integration Tests
- Test API endpoints end-to-end
- Test conversation history
- Test streaming functionality

### Example Test Coverage
- ✅ Agent creation with various MCP configurations
- ✅ Message execution with conversation history
- ✅ Session management operations
- ✅ Streaming responses
- ✅ Error handling and validation

## Performance Considerations

### 1. **Memory Management**
- Sessions stored in memory for fast access
- Configurable session limits
- Automatic cleanup options

### 2. **Async Operations**
- All agent operations are async
- Non-blocking session management
- Streaming for long operations

### 3. **Resource Optimization**
- Lazy loading of agent resources
- Efficient message serialization
- Minimal memory footprint

## Future Enhancements

### 1. **Persistent Storage**
- Replace in-memory session storage
- Database integration
- Session persistence across restarts

### 2. **Caching Layer**
- Cache agent responses
- Session state caching
- MCP server response caching

### 3. **Monitoring & Observability**
- Health metrics
- Performance monitoring
- Request tracing

### 4. **Authentication & Authorization**
- API key authentication
- Session-based auth
- Role-based access control

### 5. **Horizontal Scaling**
- Distributed session management
- Load balancing support
- Multi-instance deployment

## Migration Guide

### From Old Architecture

1. **API Consumers**: No breaking changes to API contracts
2. **Deployment**: Same startup process with `python agents/main.py`
3. **Configuration**: Same MCP server configuration format
4. **Features**: All existing features maintained with improvements

### Benefits Gained

- ✅ **Cleaner Code**: Easier to read and understand
- ✅ **Better Testing**: Comprehensive test coverage
- ✅ **Improved Maintainability**: Modular structure
- ✅ **Enhanced Reliability**: Better error handling
- ✅ **Future Ready**: Extensible architecture

## Conclusion

The refactored architecture provides a solid foundation for the MCP Agent API with:

- **Clean separation of concerns**
- **Improved conversation history handling**
- **Better error handling and validation**
- **Enhanced testability and maintainability**
- **Type-safe operations throughout**

The new structure makes the codebase more professional, maintainable, and ready for production deployment while maintaining full backward compatibility with the existing API.