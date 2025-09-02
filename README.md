## Simple AIAgent Factory.
With just an MCP, even the most complex AIAgent can be created through a simple Factory.
### about this
1. Accepts any MCP server from an external source.
2. Uses Langchain's `MultiServerMCPClient` to convert it into a Langchain BaseTool-type tool.
3. Passes the tools created in step 2 to Langgraph's prebuilt ReAct agent.

### for devs
First, turn the program you want the LLM to use into an MCP server and pass it to this program. We'll turn it into an AIAgent and return it to you!
👇
```python
class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    name: str = Field(description="Unique identifier for the MCP server")
    command: str = Field(description="Command to execute the MCP server")
    args: List[str] = Field(description="Arguments for the command")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    transport: Optional[str] = Field("stdio", description="Transport protocol")

```