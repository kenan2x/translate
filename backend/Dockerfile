##############################################
# Stage 1: build dependencies
##############################################
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
# Sadece dependency'leri kur (app kodunu degil)
RUN pip install --no-cache-dir --prefix=/install $(python -c "
import tomllib, pathlib
data = tomllib.loads(pathlib.Path('pyproject.toml').read_text())
deps = data['project']['dependencies']
print(' '.join(deps))
")

##############################################
# Stage 2: production image
##############################################
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependency'leri kopyala
COPY --from=builder /install /usr/local

# Uygulama kodunu kopyala
COPY . .

RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
