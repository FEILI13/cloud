FROM python:3.12-slim

WORKDIR /app

ARG ENGINE_VERSION=v1.0.0

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN ARCH=$(uname -m | sed 's/aarch64/arm64/' | sed 's/x86_64/amd64/') && \
    curl -L -o /usr/local/bin/engine \
    https://github.com/CSSE6400/ageoverflow-engine/releases/download/${ENGINE_VERSION}/engine-${ENGINE_VERSION}-linux-${ARCH} && \
    chmod +x /usr/local/bin/engine

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]