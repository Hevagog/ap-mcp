# ap-mcp: MCP server + functional SDK with auto-registration

## Overview

FastAPI MCP server + functional SDK for building tools as plain Python functions. Tools expose a FastAPI app, auto-register a manifest with the MCP server on startup, and the server routes calls to per-function endpoints.

**Key features:**
- **Semantic tool discovery** – Uses sentence-transformers (`all-MiniLM-L6-v2`) to match user queries to tool descriptions
- **Native LLM tool calling** – Ollama with `qwen2.5:1.5b` (**or any other tool-calling model**) selects and parameterizes tools
- **Auto-registration** – Tools register themselves on startup; no manual configuration needed
- **Functional SDK** – Write tools as plain Python functions with decorators

## Prerequisites

### Ollama (Required)

The server uses [Ollama](https://ollama.ai) for LLM-powered tool selection. Install and start Ollama before running.

```shell
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull qwen2.5:1.5b
```

> **Note:** The server will auto-pull the model on first startup if not present, but this may take some time.

**Supported models:** Any Ollama model with native tool calling support works. Configure via `OLLAMA_MODEL` env var.

## Quick Start

```shell
cd ap-mcp
ollama serve
just run
```

## Architecture

```
┌─────────────┐     ┌─────────────────────────────────────────────────┐
│     UI      │     │                  MCP Server                     │
│ (port 8501) │────▶│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
└─────────────┘     │  │ Registry │  │ VectorDB │  │ Orchestrator │   │
                    │  └──────────┘  └──────────┘  └──────────────┘   │
                    │       │              │              │           │
                    │       ▼              ▼              ▼           │
                    │  ┌─────────────────────────────────────────┐    │
                    │  │           Ollama (LLM)                  │    │
                    │  │   Tool selection & response synthesis   │    │
                    │  └─────────────────────────────────────────┘    │
                    └──────────────────────┬──────────────────────────┘
                                           │ HTTP proxy calls
                    ┌──────────────────────▼──────────────────────┐
                    │              External Tools                 │
                    │  ┌────────────────┐  ┌────────────────┐     │
                    │  │ calculator_tool│  │  (your tool)   │     │
                    │  │  (port 5080)   │  │                │     │
                    │  └────────────────┘  └────────────────┘     │
                    └─────────────────────────────────────────────┘
```

**Data flow:**
1. User sends message via UI → Server `/message` endpoint
2. `LLMOrchestrator` queries VectorDB for semantically similar tools
3. Ollama selects the best tool and extracts arguments via native tool calling
4. Server proxies the call to the tool's HTTP endpoint
5. Ollama synthesizes a natural language response from the tool output

## Services and Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| **MCP Server** | http://localhost:5000 | Central hub |
| **Calculator Tool** | http://localhost:5080 | Example tool |
| **UI** | http://localhost:8501 | Chat interface |

### Server Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Basic status message |
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe (used by Docker healthcheck) |
| POST | `/register` | Tools POST their manifest here on startup |
| GET | `/tools` | List registered tools (e.g., `calculator`, `calculator.add`) |
| POST | `/message` | Main chat endpoint – handles user messages |

### Tool Endpoints (per tool)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/manifest` | Returns `list[Manifest]` for the tool |
| POST | `/invoke/{function_name}` | Invoke a specific function (e.g., `/invoke/add`) |

## UI

A chat interface is available at http://localhost:8501. It connects to the MCP Server and uses Ollama to intelligently select and invoke registered tools based on natural language queries.

**Example interactions:**
- "What is 5 plus 3?" → Invokes `calculator.add(5, 3)`
- "Add 10 and 20" → Invokes `calculator.add(10, 20)`

## Authoring Tools

Annotate functions with `@mcp_tool(name=...)` and pass them to `create_app`:

```python
from tool_sdk import mcp_tool, create_app
import uvicorn
import os

@mcp_tool(name="calculator")
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b

@mcp_tool(name="calculator")
def multiply(a: int, b: int) -> int:
    """Multiply two integers and return the product."""
    return a * b

if __name__ == "__main__":
    app = create_app([add, multiply])
    port = int(os.environ.get("TOOL_PORT", "5080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

> **Important:** Docstrings are **critical** – they are indexed by the VectorDB for semantic search. Write clear, descriptive docstrings that explain what the function does.

### How Registration Works

1. Tool starts its FastAPI app via the SDK
2. SDK builds a manifest per tool group:
   - `name`: group name (from `@mcp_tool(name=...)`)
   - `base_url`: `TOOL_PUBLIC_URL` env var
   - `methods`: `[{name, description, parameters, path, http_method}]` built from function signatures and docstrings
3. SDK POSTs the manifest(s) to `${MCP_SERVER_URL}/register`
4. Server validates and stores:
   - A top-level entry for the tool group (metadata)
   - A per-method proxy (e.g., `calculator.add`) that calls the tool's `/invoke/{method}`
5. Server indexes method descriptions in the VectorDB for semantic search

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | LLM model for tool selection |
| `MCP_SERVER_URL` | `http://mcp_server:5000` | Server URL (for tools) |
| `TOOL_PUBLIC_URL` | – | Public URL of the tool (for registration) |
| `TOOL_PORT` | `5080` | Port for tool service |
| `PORT` | `5000` | Port for MCP server |
| `FLAVOR` | – | Set to `localdev` for hot reload |

### Using a Different Ollama Model

```shell
# Set via environment variable
export OLLAMA_MODEL=llama3.1:8b
just run

# Or in docker-compose.yml
environment:
  - OLLAMA_MODEL=qwen2.5:7b
```

## Development

### Commands (using `just`)

```shell
just run          # Start full stack (Docker Compose)
just build        # Build Docker images
just shell <svc>  # Interactive shell in container (e.g., just shell mcp_server)
just test         # Run pytest
just lint_full    # Run ruff + mypy + fawltydeps
just lint_fix     # Auto-fix linting issues
just dc <cmd>     # Run command inside Docker (e.g., just dc test)
```

### Project Structure

```
ap-mcp/
├── src/                    # MCP Server
│   ├── main.py             # FastAPI app entry point
│   └── core/
│       ├── llm/            # Ollama integration
│       ├── orchestrator/   # LLM orchestration logic
│       ├── registry/       # Tool registry
│       ├── vec_db/         # Vector database (sentence-transformers)
│       └── embedder/       # Embedding service
├── tool_sdk/               # SDK for building tools
│   └── src/tool_sdk/
│       ├── app.py          # create_app() and auto-registration
│       └── core/
│           ├── decorators.py   # @mcp_tool decorator
│           └── manifest.py     # Pydantic models
├── tools/                  # Example tools
│   └── calculator_tool/
└── ui/                     # Chat interface
```
