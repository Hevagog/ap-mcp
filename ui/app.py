import requests
import os


MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp_server:5000")
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    print("API_KEY not found in environment variables.")
    exit(1)
