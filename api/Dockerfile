FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY api/src/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir uvicorn python-dotenv azure-storage-blob

COPY . /app

EXPOSE 8000

RUN mkdir -p /app/models && chmod 777 /app/models
ENV MODEL_CACHE_DIR=/app/models
ENV YOLO_CONFIG_DIR=/app/models

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "api/src"]