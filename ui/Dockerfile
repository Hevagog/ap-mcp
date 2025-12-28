FROM python:3.12-slim

WORKDIR /app

COPY src/core/logger/ logger/
COPY ui/ .

RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8501"]
