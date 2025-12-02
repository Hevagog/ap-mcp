import streamlit as st
import requests
import os
from google import genai
from google.genai import types

st.set_page_config(page_title="MCP Chat", layout="wide")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp_server:5000")
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    st.error("API_KEY not found in environment variables.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("MCP Chat Interface")


@st.cache_data(ttl=60)
def get_tools():
    try:
        resp = requests.get(f"{MCP_SERVER_URL}/tools/definitions")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch tools: {e}")
        return {}


tools_def = get_tools()

gemini_tools = []
tool_map = {}  # Map gemini name back to real name

for name, tool in tools_def.items():
    # Skip top-level tool groups, only use methods (which have parameters)
    if "." not in name:
        continue

    # Gemini function names must be valid identifiers (no dots)
    safe_name = name.replace(".", "_")
    tool_map[safe_name] = name

    gemini_tools.append(
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=safe_name,
                    description=tool.get("description", ""),
                    parameters=tool.get("parameters", {}),
                )
            ]
        )
    )

client = genai.Client(api_key=API_KEY)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("What can I do for you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        try:
            config = types.GenerateContentConfig(
                tools=gemini_tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            )

            response = client.models.generate_content(
                model="gemini-2.0-flash-exp", contents=prompt, config=config
            )

            # Note: This is a single-turn handling for simplicity.
            if not response.candidates:
                st.error("No response from model.")
            else:
                part = response.candidates[0].content.parts[0]

                if part.function_call:
                    fc = part.function_call
                    tool_name_gemini = fc.name
                    tool_name_real = tool_map.get(tool_name_gemini, tool_name_gemini)
                    args = fc.args

                    st.info(f"Calling tool: `{tool_name_real}` with args: `{args}`")

                    # Call MCP Server
                    call_payload = {"tool_name": tool_name_real, "kwargs": args}
                    tool_resp = requests.post(
                        f"{MCP_SERVER_URL}/tools/call", json=call_payload
                    )

                    if tool_resp.status_code == 200:
                        tool_result = tool_resp.json()
                        st.success(f"Result: {tool_result}")
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": f"Executed {tool_name_real}: {tool_result}",
                            }
                        )
                    else:
                        st.error(f"Tool execution failed: {tool_resp.text}")
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": f"Error executing {tool_name_real}",
                            }
                        )

                else:
                    text = part.text
                    st.write(text)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": text}
                    )

        except Exception as e:
            st.error(f"Error: {e}")
