FROM python:3.13-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync

FROM python:3.13-slim AS runner

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/pyproject.toml ./
COPY src/ ./src/

EXPOSE 5000

CMD ["uv", "run","src/main.py"]
