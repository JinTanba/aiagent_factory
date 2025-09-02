## Simple AIAgent Factory.
With just an MCP, even the most complex AIAgent can be created through a simple Factory.
First, turn the program you want the LLM to use into an MCP server and pass it to this program. We'll turn it into an AIAgent and return it to you!

1. Accepts any MCP server from an external source.
2. Uses Langchain's `MultiServerMCPClient` to convert it into a Langchain BaseTool-type tool.
3. Passes the tools created in step 2 to Langgraph's prebuilt ReAct agent.
