import os
 
from mcp.server.fastmcp import FastMCP
 
 
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8003"))
    
mcp = FastMCP("Weather MCP", host=MCP_HOST, port=MCP_PORT)
 
 
@mcp.tool()
def get_weather(city: str) -> str:
    return f"The weather in {city} is 32 degree Celsius."
 
 
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
 
 