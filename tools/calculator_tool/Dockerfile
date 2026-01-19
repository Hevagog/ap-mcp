FROM python:3.13-slim

WORKDIR /app

COPY src/server/core/logger/ logger/
COPY tool_sdk/ /tool_sdk/

RUN pip install --no-cache-dir uv
RUN pip install --no-cache-dir /tool_sdk

COPY tools/calculator_tool/pyproject.toml calculator_tool/pyproject.toml
COPY tools/calculator_tool/src/ calculator_tool/src/

EXPOSE 5080

CMD [ "uv" , "run", "calculator_tool/src/service.py"]
