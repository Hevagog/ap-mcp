import os

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()
templates = Jinja2Templates(directory="templates")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp_server:5000")


class ChatMessage(BaseModel):
    content: str


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    tools = []
    try:
        response = requests.get(f"{MCP_SERVER_URL}/tools/definitions", timeout=5)
        if response.status_code == 200:
            tools = response.json()
    except Exception as e:
        print(f"Error fetching tools: {e}")

    return templates.TemplateResponse("index.html", {"request": request, "tools": tools})


@app.post("/chat")
async def chat(message: ChatMessage):
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/message", json={"content": message.content}, timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8501)
