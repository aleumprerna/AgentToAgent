import os

import uvicorn
from mcp.server.fastmcp import FastMCP


MCP_HOST = os.getenv("EMAIL_MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("EMAIL_MCP_PORT", "8201"))

mcp = FastMCP("Email MCP Server", host=MCP_HOST, port=MCP_PORT)


@mcp.tool()
def send_mock_email(to: str, subject: str, body: str, cc: str = "") -> dict:
    return {
        "mock_email_sent": True,
        "to": to,
        "cc": cc,
        "subject": subject,
        "body": body,
        "message": f"Your message has been sent to {to}.",
    }


@mcp.tool()
def health() -> dict:
    return {"status": "healthy", "server": "Email MCP Server"}


app = mcp.streamable_http_app()


if __name__ == "__main__":
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)
