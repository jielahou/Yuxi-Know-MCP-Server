import os
import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from starlette.requests import Request
from starlette.routing import Route, Mount
import mcp.types as types
import uvicorn
from client import get_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Authentication token for SSE endpoint
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")

# Initialize standard MCP Server
app_mcp = Server("Knowledge Base MCP")

@app_mcp.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_knowledge_bases",
            description="List all available knowledge bases.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        types.Tool(
            name="query_knowledge_base",
            description=(
                "Perform a vector search/RAG query against a specific knowledge base. "
                "IMPORTANT: The `query` argument MUST consist of English words only, separated by spaces. "
                "The model should refine the input into concise English keywords based on the context before calling this tool."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "db_id": {"type": "string", "description": "The ID of the knowledge base to query."},
                    "query": {"type": "string", "description": "Space-separated English keywords representing the search query."}
                },
                "required": ["db_id", "query"]
            }
        )
    ]

@app_mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
    if name == "list_knowledge_bases":
        return await list_knowledge_bases_impl()
    elif name == "query_knowledge_base":
        return await query_knowledge_base_impl(arguments["db_id"], arguments["query"])
    else:
        raise ValueError(f"Unknown tool: {name}")

# Tool Implementations

async def list_knowledge_bases_impl() -> list[types.ContentBlock]:
    client = get_client()
    try:
        data = await client.request("GET", "/api/knowledge/databases")
        results = []
        databases = data.get("databases", []) if isinstance(data, dict) else []
        for db in databases:
            results.append({
                "id": db.get("db_id"),
                "name": db.get("name"),
                "description": db.get("description", "No description provided")
            })
        return [types.TextContent(type="text", text=str(results))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing knowledge bases: {str(e)}")]

async def query_knowledge_base_impl(db_id: str, query: str) -> list[types.ContentBlock]:
    client = get_client()
    try:
        payload = {
            "query": query,
            "meta": {}
        }
        result = await client.request("POST", f"/api/knowledge/databases/{db_id}/query", json=payload)
        return [types.TextContent(type="text", text=str(result))]
    except httpx.HTTPStatusError as e:
        return [types.TextContent(type="text", text=f"Query failed with status {e.response.status_code}: {e.response.text}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error querying knowledge base: {str(e)}")]

# Authentication check
def check_auth(request: Request) -> bool:
    """Check if the request has valid authentication."""
    if not MCP_AUTH_TOKEN:
        # No token configured, allow all requests (for local dev)
        return True
    
    # Check Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if token == MCP_AUTH_TOKEN:
            return True
    
    # Also check query parameter for SSE connections
    token_param = request.query_params.get("token")
    if token_param == MCP_AUTH_TOKEN:
        return True
    
    return False

# SSE Transport Setup
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request):
    # Check authentication
    if not check_auth(request):
        return JSONResponse(
            {"error": "Unauthorized", "message": "Valid authentication token required"},
            status_code=401
        )
    
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await app_mcp.run(streams[0], streams[1], app_mcp.create_initialization_options())
    return Response()

async def handle_messages(request: Request):
    # Check authentication
    if not check_auth(request):
        return JSONResponse(
            {"error": "Unauthorized", "message": "Valid authentication token required"},
            status_code=401
        )
    
    await sse.handle_post_message(request.scope, request.receive, request._send)
    # Note: sse.handle_post_message already sends the response,
    # so we don't return anything here to avoid double response

# Starlette App
app = Starlette(
    debug=False,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/messages/", endpoint=handle_messages, methods=["POST"]),
    ],
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    if MCP_AUTH_TOKEN:
        print(f"🔐 Authentication enabled. Use token to connect.")
    else:
        print("⚠️  No MCP_AUTH_TOKEN set. Running without authentication (not recommended for public deployment).")
    
    print(f"🚀 Starting MCP SSE server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
