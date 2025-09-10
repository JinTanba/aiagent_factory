from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from contextlib import asynccontextmanager
import asyncio
import json
import uuid
from datetime import datetime
try:
    from agent import generate_general_agent
    from mcp2tools import McpServer
except ImportError:
    from .agent import generate_general_agent
    from .mcp2tools import McpServer

app = FastAPI(title="MCP Agent API", version="1.0.0")

agent_sessions: Dict[str, Dict[str, Any]] = {}


class MCPServerConfig(BaseModel):
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    transport: Optional[str] = "stdio"


class CreateAgentRequest(BaseModel):
    mcp_servers: List[MCPServerConfig] = Field(
        description="List of MCP server configurations"
    )
    session_id: Optional[str] = Field(
        None, description="Optional session ID for agent persistence"
    )


class CreateAgentResponse(BaseModel):
    session_id: str
    message: str
    mcp_servers_count: int
    created_at: str


class ExecuteAgentRequest(BaseModel):
    session_id: str = Field(description="Session ID of the agent to use")
    message: str = Field(description="Message to send to the agent")
    stream: bool = Field(False, description="Whether to stream the response")


class ExecuteAgentResponse(BaseModel):
    session_id: str
    response: str
    timestamp: str


class ListSessionsResponse(BaseModel):
    sessions: List[Dict[str, Any]]


class DeleteSessionResponse(BaseModel):
    session_id: str
    message: str


@app.get("/")
async def root():
    return {
        "message": "MCP Agent API",
        "endpoints": {
            "/agents/create": "Create a new agent with MCP configurations",
            "/agents/execute": "Execute a message with an existing agent",
            "/agents/sessions": "List all active sessions",
            "/agents/sessions/{session_id}": "Get or delete a specific session",
            "/health": "Health check endpoint",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_sessions": len(agent_sessions)}


@app.post("/agents/create", response_model=CreateAgentResponse)
async def create_agent(request: CreateAgentRequest):
    """
    Create a new agent with the specified MCP server configurations.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id in agent_sessions:
            raise HTTPException(
                status_code=400, detail=f"Session {session_id} already exists"
            )
        
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
        
        agent = await generate_general_agent(mcp_servers_dict)
        
        agent_sessions[session_id] = {
            "agent": agent,
            "mcp_servers": mcp_servers_dict,
            "created_at": datetime.utcnow().isoformat(),
            "messages": [],  # Store actual LangChain message objects
            "message_history": [],  # Keep for backwards compatibility/logging
        }
        
        return CreateAgentResponse(
            session_id=session_id,
            message=f"Agent created successfully with {len(request.mcp_servers)} MCP servers",
            mcp_servers_count=len(request.mcp_servers),
            created_at=agent_sessions[session_id]["created_at"],
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/execute")
async def execute_agent(request: ExecuteAgentRequest):
    """
    Execute a message with an existing agent session.
    """
    if request.session_id not in agent_sessions:
        raise HTTPException(
            status_code=404, detail=f"Session {request.session_id} not found"
        )
    
    session = agent_sessions[request.session_id]
    agent = session["agent"]
    
    try:
        human_message = HumanMessage(content=request.message)
        session["message_history"].append(
            {"role": "human", "content": request.message, "timestamp": datetime.utcnow().isoformat()}
        )
        
        if request.stream:
            return StreamingResponse(
                stream_agent_response(agent, human_message, request.session_id),
                media_type="text/event-stream",
            )
        else:
            response = await execute_agent_sync(agent, human_message)
            
            session["message_history"].append(
                {"role": "assistant", "content": response, "timestamp": datetime.utcnow().isoformat()}
            )
            
            return ExecuteAgentResponse(
                session_id=request.session_id,
                response=response,
                timestamp=datetime.utcnow().isoformat(),
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def execute_agent_sync(agent, message: HumanMessage) -> str:
    """
    Execute agent synchronously and return the complete response.
    """
    response_chunks = []
    stream = agent.stream({"messages": [message]})
    
    for chunk in stream:
        if "agent" in chunk and "messages" in chunk["agent"]:
            for msg in chunk["agent"]["messages"]:
                if hasattr(msg, "content"):
                    response_chunks.append(msg.content)
    
    return "".join(response_chunks)


async def stream_agent_response(
    agent, message: HumanMessage, session_id: str
) -> AsyncGenerator[str, None]:
    """
    Stream agent response as Server-Sent Events.
    """
    try:
        stream = agent.stream({"messages": [message]})
        full_response = []
        
        for chunk in stream:
            if "agent" in chunk and "messages" in chunk["agent"]:
                for msg in chunk["agent"]["messages"]:
                    if hasattr(msg, "content"):
                        content = msg.content
                        full_response.append(content)
                        
                        event_data = json.dumps({
                            "type": "content",
                            "data": content,
                            "session_id": session_id,
                        })
                        yield f"data: {event_data}\n\n"
        
        agent_sessions[session_id]["message_history"].append(
            {"role": "assistant", "content": "".join(full_response), "timestamp": datetime.utcnow().isoformat()}
        )
        
        event_data = json.dumps({
            "type": "done",
            "session_id": session_id,
        })
        yield f"data: {event_data}\n\n"
    
    except Exception as e:
        event_data = json.dumps({
            "type": "error",
            "error": str(e),
            "session_id": session_id,
        })
        yield f"data: {event_data}\n\n"


@app.get("/agents/sessions", response_model=ListSessionsResponse)
async def list_sessions():
    """
    List all active agent sessions.
    """
    sessions = [
        {
            "session_id": session_id,
            "created_at": data["created_at"],
            "mcp_servers_count": len(data["mcp_servers"]),
            "message_count": len(data["message_history"]),
        }
        for session_id, data in agent_sessions.items()
    ]
    
    return ListSessionsResponse(sessions=sessions)


@app.get("/agents/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get details of a specific session.
    """
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    session = agent_sessions[session_id]
    
    return {
        "session_id": session_id,
        "created_at": session["created_at"],
        "mcp_servers": session["mcp_servers"],
        "message_history": session["message_history"],
    }


@app.delete("/agents/sessions/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str):
    """
    Delete a specific session.
    """
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    del agent_sessions[session_id]
    
    return DeleteSessionResponse(
        session_id=session_id, message="Session deleted successfully"
    )


@app.delete("/agents/sessions")
async def delete_all_sessions():
    """
    Delete all active sessions.
    """
    count = len(agent_sessions)
    agent_sessions.clear()
    
    return {"message": f"Deleted {count} sessions"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)