#!/bin/bash
###############################################
# Kapsamli Backend Test Script
# Kullanim: ./scripts/test_backend.sh <BACKEND_URL>
# Ornek:    ./scripts/test_backend.sh http://172.30.146.31:9775
###############################################
set -uo pipefail

BACKEND_URL="${1:-http://localhost:8080}"
LOG_FILE="/tmp/backend_test.log"
COMPOSE_FILE="docker-compose.dev.yml"

log() { echo "$1" | tee -a "$LOG_FILE"; }
sep() { log ""; log "--------------------------------------------"; }

echo "" > "$LOG_FILE"
log "============================================"
log "Kapsamli Backend Test — $(date)"
log "Backend URL: $BACKEND_URL"
log "============================================"

###############################################
sep
log "[1/10] Container durumlari"
###############################################
docker compose -f "$COMPOSE_FILE" ps 2>&1 | tee -a "$LOG_FILE"

###############################################
sep
log "[2/10] Health check"
###############################################
HEALTH=$(curl -s -w "\nHTTP:%{http_code}" "$BACKEND_URL/health" 2>&1)
log "$HEALTH"

###############################################
sep
log "[3/10] Swagger docs erisilebilir mi"
###############################################
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/docs" 2>&1)
log "HTTP: $DOCS_CODE"

###############################################
sep
log "[4/10] Test PDF olustur"
###############################################
python3 -c "
pdf = b'''%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Hello World) Tj ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000360 00000 n
trailer << /Size 6 /Root 1 0 R >>
startxref
434
%%EOF'''
with open('/tmp/test.pdf','wb') as f: f.write(pdf)
print('OK — %d bytes' % len(pdf))
" 2>&1 | tee -a "$LOG_FILE"

###############################################
sep
log "[5/10] PDF upload"
###############################################
UPLOAD_RESP=$(curl -s -w "\n---HTTP:%{http_code}---" \
  -X POST "$BACKEND_URL/api/v1/upload" \
  -F "file=@/tmp/test.pdf;type=application/pdf" \
  --max-time 30 2>&1)
log "$UPLOAD_RESP"

# job_id cek
JOB_ID=$(echo "$UPLOAD_RESP" | grep -o '"job_id"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*' || echo "")
if [ -z "$JOB_ID" ]; then
  JOB_ID=$(echo "$UPLOAD_RESP" | grep -o '"job_id"[[:space:]]*:[[:space:]]*"[^"]*"' | grep -o '"[^"]*"$' | tr -d '"' || echo "")
fi
log "Parsed job_id: $JOB_ID"

###############################################
sep
log "[6/10] Job durumu kontrol (eger job_id varsa)"
###############################################
if [ -n "$JOB_ID" ]; then
  JOB_RESP=$(curl -s -w "\n---HTTP:%{http_code}---" \
    "$BACKEND_URL/api/v1/jobs/$JOB_ID" \
    -H "Accept: text/event-stream" \
    --max-time 10 2>&1)
  log "$JOB_RESP"
else
  log "SKIP — job_id yok, upload basarisiz olmus olabilir"
fi

###############################################
sep
log "[7/10] History endpoint"
###############################################
HIST_RESP=$(curl -s -w "\n---HTTP:%{http_code}---" "$BACKEND_URL/api/v1/history" --max-time 5 2>&1)
log "$HIST_RESP"

###############################################
sep
log "[8/10] Backend loglari (son 50 satir)"
###############################################
docker compose -f "$COMPOSE_FILE" logs backend --tail 50 --no-color 2>&1 | tee -a "$LOG_FILE"

###############################################
sep
log "[9/10] Celery worker loglari (son 50 satir)"
###############################################
docker compose -f "$COMPOSE_FILE" logs celery-worker --tail 50 --no-color 2>&1 | tee -a "$LOG_FILE"

###############################################
sep
log "[10/10] Redis ve Postgres baglanti kontrol"
###############################################
# Redis
docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping 2>&1 | tee -a "$LOG_FILE"
# Postgres
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U translate -d translate_db 2>&1 | tee -a "$LOG_FILE"

###############################################
sep
log "============================================"
log "Test tamamlandi. Log: $LOG_FILE"
log ""
log "Issue acmak icin:"
log "  gh issue create --repo kenan2x/translate \\"
log "    --title 'Test sonuclari $(date +%Y-%m-%d_%H:%M)' \\"
log "    --body-file $LOG_FILE"
log "============================================"
