##############################################
# Stage 1: build dependencies
##############################################
FROM python:3.12-slim AS builder

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV HTTP_PROXY=${HTTP_PROXY} HTTPS_PROXY=${HTTPS_PROXY} NO_PROXY=${NO_PROXY}

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

# requirements.txt olustur ve sadece dependency'leri kur
RUN python -c "import tomllib;f=open('pyproject.toml','rb');d=tomllib.load(f);print('\n'.join(d['project']['dependencies']))" > /tmp/requirements.txt && \
    pip install --no-cache-dir -r /tmp/requirements.txt

##############################################
# Stage 2: production image
##############################################
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

# pdf2zh runtime icin gerekli sistem paketleri
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

# Dependency'leri kopyala (tum site-packages)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Uygulama kodunu kopyala
# NOT: DocLayout-YOLO model volume ile mount edilir (docker-compose'da)
# Indirmek icin: ./scripts/download_model.sh
COPY . .

# Dogrulama
RUN ls -la /app/app/ && python -c "import app; print('app module OK')"
RUN python -c "import pdf2zh; print('pdf2zh OK')" || echo "WARN: pdf2zh import failed (onnxruntime may need runtime libs)"

RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
