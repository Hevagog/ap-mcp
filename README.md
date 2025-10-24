# ap-mcp: MCP server + functional SDK with auto-registration

Overview

FastAPI MCP server + functional SDK for building tools as plain Python functions. Tools expose a FastAPI app, auto-register a manifest with the MCP server on startup, and the server routes calls to per-function endpoints.

## How to run:

```shell
just run
```

Please create a `.env` file in the project root with the `API_KEY` variable set to *Gemini Developer API* key.


## Services and endpoints

 - Server (host): http://localhost:5000
	 - GET `/` → basic message
	 - GET `/health` → liveness
	 - GET `/ready` → readiness (Compose healthcheck uses this)
	 - POST `/register` → tools POST their manifest here on startup
	 - GET `/tools` → lists the registry names (includes top-level tool and per-method proxies; e.g., `calculator`, `calculator.add`)
 - Tool (host): http://localhost:5080
	 - GET `/manifest` → list[Manifest] (one per tool group)
	 - POST `/invoke/{function_name}` → per-function endpoint (e.g., `/invoke/add`)
	 - POST `/invoke` → generic invoker with body `{method, args, kwargs}` (kept for compatibility)

## Authoring tools

Annotate functions with `@mcp_tool(name=...)` and pass them to `create_app`:

```python
from tool_sdk import mcp_tool, create_app

@mcp_tool(name="calculator")
def add(a: int, b: int) -> int:
		"""Add two integers and return the result."""
		return a + b

app = create_app([add])  # or multiple functions: create_app([add, mul, ...])
```

### How registration works
 1. Tool starts its FastAPI app via the SDK.
 2. SDK builds a manifest per tool group:
		- name: group name (from `@mcp_tool(name=...)`)
		- base_url: TOOL_PUBLIC_URL
		- methods: [{name, description, path, http_method}] built from each function’s docstring and generated route `/invoke/{name}` (POST)
 3. SDK POSTs the manifest(s) to `${MCP_SERVER_URL}/register`.
 4. Server validates and stores:
		- a top-level entry for the tool group (metadata)
		- a per-method proxy (e.g., `calculator.add`) that calls the tool’s `/invoke/{method}`.
 5. Server indexes semantics using the method docstrings (vector DB).

