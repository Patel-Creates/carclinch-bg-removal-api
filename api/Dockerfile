FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  libgl1 \
  libglib2.0-0 \
  libsm6 \
  libxext6 \
  libxrender1 \
  libx11-6 \
  libxcb1 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt \
  --extra-index-url https://download.pytorch.org/whl/cpu

COPY . /app

EXPOSE 8000

RUN mkdir -p /app/models && chmod 777 /app/models && mkdir -p /root/.u2net && curl -L -o /root/.u2net/u2net.onnx \
  https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx

ENV MODEL_CACHE_DIR=/app/models
ENV YOLO_CONFIG_DIR=/app/models

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
