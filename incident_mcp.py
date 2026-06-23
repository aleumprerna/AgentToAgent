from mcp.server.fastmcp import FastMCP
import uvicorn
 
# Create MCP server
mcp = FastMCP("Incident Server")
 
 
@mcp.tool()
def fetch_incident_details(incident_number: str) -> dict:
    """
    Fetch incident details by incident number.
    Returns dummy data.
    """
    return {
        "incident_number": incident_number,
        "short_description": "Email service is down",
        "description": "Users are unable to send or receive emails.",
        "priority": "High",
        "state": "In Progress",
        "assigned_to": "Support Team",
        "created_on": "2026-06-22 10:00:00",
    }
 
 
 
def health() -> dict:
    """
    Check the health of the incident server.
    Returns dummy data.
    """
    return {
        "status": "healthy",
        "message": "Incident server is running",
    }
 
 
# MCP HTTP application
app = mcp.streamable_http_app()
 
 
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
    )
 