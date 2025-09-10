# BlackSwan Multi-Tenant Agent API Documentation

## Overview

The BlackSwan Multi-Tenant Agent API provides a robust system for managing AI agent configurations and conversations. It separates agent configurations (reusable) from conversation sessions (execution results), enabling efficient resource utilization and true multi-tenancy.

## Base URL
```
http://localhost:8000
```

## Architecture Concepts

### Configurations vs Conversations
- **Configuration**: A reusable template containing MCP servers, system prompts, and model settings
- **Conversation**: An execution session linked to a specific configuration, containing message history

### Agent Instance Caching
- Agent instances are cached based on configuration ID
- Multiple conversations can share the same agent instance
- LRU eviction with 30-minute idle timeout

---

## Authentication

Currently, no authentication is required. This should be implemented for production use.

---

## API Endpoints

### 1. System Information

#### Get API Information
```http
GET /
```

**Response:**
```json
{
  "name": "BlackSwan Multi-Tenant Agent API",
  "version": "2.0.0",
  "description": "Multi-tenant AI agent system with separated configurations and conversations",
  "endpoints": {
    "/configurations": "Manage agent configurations",
    "/conversations": "Manage conversations",
    "/health": "Health check"
  }
}
```

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "active_sessions": 2,
  "timestamp": "2025-09-10T05:43:06.232739"
}
```

---

## Configuration Management

### 2. Create Agent Configuration

Create a reusable agent configuration that can power multiple conversations.

```http
POST /configurations
```

**Request Body:**
```json
{
  "name": "Trading Bot Configuration",
  "mcp_servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "env": {},
      "transport": "stdio"
    },
    {
      "name": "web_search",
      "command": "python",
      "args": ["-m", "web_search_server"],
      "env": {"API_KEY": "your_api_key"},
      "transport": "stdio"
    }
  ],
  "system_prompt": "You are a helpful trading assistant with access to file system and web search.",
  "model_settings": {
    "temperature": 0.1,
    "model": "gpt-4o"
  }
}
```

**Request Schema:**
- `name` (string, required): Human-readable configuration name
- `mcp_servers` (array, required): List of MCP server configurations
  - `name` (string): Unique identifier for the MCP server
  - `command` (string): Command to execute the MCP server
  - `args` (array): Arguments for the command
  - `env` (object, optional): Environment variables
  - `transport` (string, optional): Transport protocol (default: "stdio")
- `system_prompt` (string, optional): System prompt override
- `model_settings` (object, optional): Model-specific settings
  - `temperature` (number): Model temperature (0.0-1.0)
  - `model` (string): Model name (e.g., "gpt-4o", "gpt-3.5-turbo")

**Response:**
```json
{
  "config_id": "110ba721-354e-40fc-a591-d1f0cdb11ef5",
  "name": "Trading Bot Configuration",
  "message": "Configuration 'Trading Bot Configuration' created successfully",
  "mcp_servers_count": 2,
  "created_at": "2025-09-10T05:43:30.988462"
}
```

### 3. List Configurations

```http
GET /configurations?active_only=true
```

**Query Parameters:**
- `active_only` (boolean, optional): Filter to only active configurations (default: true)

**Response:**
```json
{
  "configurations": [
    {
      "config_id": "110ba721-354e-40fc-a591-d1f0cdb11ef5",
      "name": "Trading Bot Configuration",
      "mcp_servers_count": 2,
      "created_at": "2025-09-10T05:43:30.988000",
      "updated_at": "2025-09-10T05:43:30.988000"
    }
  ]
}
```

---

## Conversation Management

### 4. Start Conversation

Start a new conversation using an existing configuration.

```http
POST /conversations
```

**Request Body:**
```json
{
  "config_id": "110ba721-354e-40fc-a591-d1f0cdb11ef5",
  "session_id": "custom-session-id" // optional
}
```

**Request Schema:**
- `config_id` (string, required): Configuration ID to use
- `session_id` (string, optional): Custom session ID (auto-generated if not provided)

**Response:**
```json
{
  "session_id": "e9b62161-25b5-49ef-848d-206feeed4a8f",
  "config_id": "110ba721-354e-40fc-a591-d1f0cdb11ef5",
  "config_name": "Trading Bot Configuration",
  "message": "Conversation started with configuration 'Trading Bot Configuration'",
  "created_at": "2025-09-10T05:44:06.866297"
}
```

### 5. Execute Message

Send a message to the agent in a conversation.

```http
POST /conversations/execute
```

**Request Body:**
```json
{
  "session_id": "e9b62161-25b5-49ef-848d-206feeed4a8f",
  "message": "What's the weather like today?",
  "stream": false
}
```

**Request Schema:**
- `session_id` (string, required): Session ID of the conversation
- `message` (string, required): Message to send to the agent
- `stream` (boolean, optional): Whether to stream the response (default: false)

**Response (Non-streaming):**
```json
{
  "session_id": "e9b62161-25b5-49ef-848d-206feeed4a8f",
  "response": "I don't have access to real-time weather information...",
  "message_count": 3
}
```

**Response (Streaming):**
When `stream: true`, the response is returned as Server-Sent Events:

```
Content-Type: application/x-ndjson

data: {"type": "message", "session_id": "...", "data": "I'm checking the weather for you..."}

data: {"type": "message", "session_id": "...", "data": " The current temperature is..."}

data: {"type": "complete", "session_id": "..."}
```

**Stream Event Types:**
- `message`: Partial response content
- `complete`: Response finished successfully
- `error`: An error occurred

### 6. List Conversations

```http
GET /conversations?config_id=110ba721-354e-40fc-a591-d1f0cdb11ef5&active_only=true
```

**Query Parameters:**
- `config_id` (string, optional): Filter by configuration ID
- `active_only` (boolean, optional): Filter to only active conversations (default: true)

**Response:**
```json
{
  "conversations": [
    {
      "session_id": "e9b62161-25b5-49ef-848d-206feeed4a8f",
      "config_id": "110ba721-354e-40fc-a591-d1f0cdb11ef5",
      "created_at": "2025-09-10T05:44:06.866000",
      "updated_at": "2025-09-10T05:44:51.736000",
      "message_count": 3
    }
  ]
}
```

### 7. Get Conversation Details

```http
GET /conversations/{session_id}
```

**Response:**
```json
{
  "session_id": "e9b62161-25b5-49ef-848d-206feeed4a8f",
  "created_at": "2025-09-10T05:44:06.866000",
  "mcp_servers": [],
  "message_history": [
    {
      "role": "human",
      "content": "What's the weather like today?",
      "timestamp": "2025-09-10T05:44:38.041000"
    },
    {
      "role": "assistant",
      "content": "I don't have access to real-time weather information...",
      "timestamp": "2025-09-10T05:44:51.736000"
    }
  ]
}
```

### 8. Delete Conversation

```http
DELETE /conversations/{session_id}
```

**Response:**
```json
{
  "session_id": "e9b62161-25b5-49ef-848d-206feeed4a8f",
  "message": "Conversation deleted successfully"
}
```

---

## Error Handling

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Not Found (configuration or conversation not found)
- `410` - Gone (deprecated endpoints)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "detail": "Configuration 12345 not found"
}
```

### Common Errors

- **Configuration not found**: When starting conversation with non-existent config_id
- **Conversation not found**: When executing message or getting details for non-existent session_id
- **Validation errors**: Missing required fields or invalid data types
- **Agent creation errors**: Issues with MCP server configurations

---

## Client Implementation Examples

### Python Client Example

```python
import requests
import json
from typing import Dict, List, Optional

class BlackSwanAgentClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def create_configuration(self, name: str, mcp_servers: List[Dict], 
                           system_prompt: Optional[str] = None,
                           model_settings: Optional[Dict] = None) -> Dict:
        """Create a new agent configuration."""
        payload = {
            "name": name,
            "mcp_servers": mcp_servers,
            "system_prompt": system_prompt,
            "model_settings": model_settings
        }
        response = requests.post(f"{self.base_url}/configurations", json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_configurations(self, active_only: bool = True) -> Dict:
        """List all configurations."""
        params = {"active_only": active_only}
        response = requests.get(f"{self.base_url}/configurations", params=params)
        response.raise_for_status()
        return response.json()
    
    def start_conversation(self, config_id: str, session_id: Optional[str] = None) -> Dict:
        """Start a new conversation."""
        payload = {"config_id": config_id}
        if session_id:
            payload["session_id"] = session_id
        response = requests.post(f"{self.base_url}/conversations", json=payload)
        response.raise_for_status()
        return response.json()
    
    def send_message(self, session_id: str, message: str, stream: bool = False) -> Dict:
        """Send a message to the agent."""
        payload = {
            "session_id": session_id,
            "message": message,
            "stream": stream
        }
        response = requests.post(f"{self.base_url}/conversations/execute", json=payload)
        response.raise_for_status()
        
        if stream:
            return self._handle_stream(response)
        else:
            return response.json()
    
    def _handle_stream(self, response):
        """Handle streaming response."""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    yield data

# Example usage
client = BlackSwanAgentClient()

# Create configuration
config = client.create_configuration(
    name="My Trading Bot",
    mcp_servers=[{
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        "env": {},
        "transport": "stdio"
    }],
    system_prompt="You are a helpful trading assistant.",
    model_settings={"temperature": 0.1}
)

# Start conversation
conversation = client.start_conversation(config["config_id"])

# Send message
response = client.send_message(
    conversation["session_id"], 
    "Hello, can you help me analyze some trading data?"
)

print(response["response"])
```

### JavaScript/Node.js Client Example

```javascript
class BlackSwanAgentClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async createConfiguration(name, mcpServers, systemPrompt = null, modelSettings = null) {
        const payload = {
            name,
            mcp_servers: mcpServers,
            system_prompt: systemPrompt,
            model_settings: modelSettings
        };

        const response = await fetch(`${this.baseUrl}/configurations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        return await response.json();
    }

    async startConversation(configId, sessionId = null) {
        const payload = { config_id: configId };
        if (sessionId) payload.session_id = sessionId;

        const response = await fetch(`${this.baseUrl}/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        return await response.json();
    }

    async sendMessage(sessionId, message, stream = false) {
        const payload = {
            session_id: sessionId,
            message: message,
            stream: stream
        };

        const response = await fetch(`${this.baseUrl}/conversations/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

        if (stream) {
            return this._handleStream(response);
        } else {
            return await response.json();
        }
    }

    async *_handleStream(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.substring(6));
                        yield data;
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }
}

// Example usage
const client = new BlackSwanAgentClient();

async function example() {
    // Create configuration
    const config = await client.createConfiguration(
        'My Trading Bot',
        [{
            name: 'filesystem',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-filesystem', '/tmp'],
            env: {},
            transport: 'stdio'
        }],
        'You are a helpful trading assistant.',
        { temperature: 0.1 }
    );

    // Start conversation
    const conversation = await client.startConversation(config.config_id);

    // Send message
    const response = await client.sendMessage(
        conversation.session_id,
        'Hello, can you help me analyze some trading data?'
    );

    console.log(response.response);
}
```

---

## Best Practices

### 1. Configuration Reuse
- Create configurations for different use cases (trading, support, analysis)
- Reuse configurations across multiple conversations for resource efficiency
- Use descriptive names for easy identification

### 2. Session Management
- Store session IDs for ongoing conversations
- Clean up completed conversations to maintain performance
- Monitor session counts via health endpoint

### 3. Error Handling
- Always check HTTP status codes
- Implement retry logic for transient failures
- Handle streaming disconnections gracefully

### 4. Performance Optimization
- Use streaming for long responses
- Cache configuration lists on client side
- Implement connection pooling for high-volume usage

### 5. Security Considerations
- Implement authentication/authorization in production
- Validate all inputs before sending to API
- Use HTTPS in production environments
- Store sensitive data (API keys) securely

---

## Environment Variables

Required environment variables for the server:

```bash
# MongoDB Connection
MONGODB_URL="mongodb+srv://user:password@cluster.mongodb.net/database"
MONGODB_DATABASE="your_database_name"

# OpenAI Configuration
OPENAI_API_KEY="your_openai_api_key"
OPENAI_MODEL="gpt-4o"  # optional, defaults to gpt-4o

# Server Configuration (optional)
HOST="0.0.0.0"  # defaults to 0.0.0.0
PORT="8000"     # defaults to 8000
DEBUG="false"   # defaults to false
```

---

## Monitoring and Observability

### Health Monitoring
- Use `GET /health` endpoint for health checks
- Monitor active session counts
- Track response times for performance

### Logging
- Server logs include MongoDB operations
- Agent execution logs available
- Error details in response bodies

### Metrics to Monitor
- Configuration creation rate
- Conversation start rate
- Message execution rate
- Agent cache hit ratio
- Average response time
- Error rates by endpoint

---

## Migration from Legacy API

If migrating from the old single-session API:

### Old Pattern:
```javascript
// Create agent (creates both config and session)
const agent = await createAgent({mcp_servers: [...]});
await executeAgent(agent.session_id, "Hello");
```

### New Pattern:
```javascript
// 1. Create reusable configuration
const config = await createConfiguration({
    name: "My Agent", 
    mcp_servers: [...]
});

// 2. Start conversation
const conversation = await startConversation(config.config_id);

// 3. Execute messages
await sendMessage(conversation.session_id, "Hello");

// 4. Reuse configuration for new conversations
const conversation2 = await startConversation(config.config_id);
```

### Benefits of Migration:
- Agent instance reuse improves performance
- Better resource utilization
- Cleaner separation of concerns
- Support for multiple concurrent conversations
- Improved scalability