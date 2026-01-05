# YuXi MCP - Knowledge Base MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to query your knowledge base. This server provides tools for listing and searching knowledge bases via the MCP protocol.

## Features

- 🔍 **List Knowledge Bases** - Retrieve all available knowledge bases with their IDs and descriptions
- 📚 **Query Knowledge Base** - Perform vector search/RAG queries against specific knowledge bases
- 🔐 **Authentication** - Secure your deployment with token-based authentication
- 🐳 **Docker Support** - Easy deployment with Docker

## Prerequisites

- Python 3.12+
- A running Knowledge Base API server

## Installation

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/jielahou/Yuxi-Know-MCP-Server
cd Yuxi-Know-MCP-Server
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run the server:
```bash
python server_sse.py
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t yuki-mcp-server .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 \
  -e KB_API_URL=http://your-yuki-know-api-host:5050 \
  -e KB_USERNAME=your_username \
  -e KB_PASSWORD=your_password \
  -e MCP_AUTH_TOKEN=your_secure_token \
  --name yuki-mcp-server \
  yuki-mcp-server
```

## Configuration

| Environment Variable | Description | Required |
|---------------------|-------------|----------|
| `KB_API_URL` | URL of your Knowledge Base API | Yes |
| `KB_USERNAME` | Username for KB API authentication | Yes |
| `KB_PASSWORD` | Password for KB API authentication | Yes |
| `MCP_AUTH_TOKEN` | Token for securing MCP endpoint | Recommended |
| `HOST` | Server host (default: `0.0.0.0`) | No |
| `PORT` | Server port (default: `8000`) | No |

### Generating a Secure Token

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Usage

### Connecting to the Server

The SSE endpoint is available at:
```
http://localhost:8000/sse
```

With authentication:
```
http://localhost:8000/sse?token=your_secure_token
```

Or use the Authorization header:
```
Authorization: Bearer your_secure_token
```

### Available Tools

#### `list_knowledge_bases`
Lists all available knowledge bases with their IDs, names, and descriptions.

#### `query_knowledge_base`
Queries a specific knowledge base.

**Parameters:**
- `db_id` (string): The ID of the knowledge base to query
- `query` (string): Space-separated English keywords for the search

> **Note:** The query should consist of English words only, separated by spaces. Refine your input into concise English keywords for best results.

## Client Configuration

### Claude Code

Add to your `claude_desktop_config.json`, or `.mcp.json` in your project root directory:

```json
{
  "mcpServers": {
    "knowledge-base-mcp": {
      "type": "sse",
      "url": "http://localhost:8000/sse",
      "headers": {
        "Authorization": "Bearer your_secure_token"
      }
    }
  }
}
```

## License

MIT License
