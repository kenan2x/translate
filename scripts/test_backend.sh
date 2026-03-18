#!/bin/bash
###############################################
# Backend Test Script
# Kullanim: ./scripts/test_backend.sh <BACKEND_URL>
# Ornek:    ./scripts/test_backend.sh http://10.20.1.50:8080
###############################################
set -euo pipefail

BACKEND_URL="${1:-http://localhost:8080}"
LOG_FILE="/tmp/backend_test.log"

echo "============================================" | tee "$LOG_FILE"
echo "Backend Test - $(date)" | tee -a "$LOG_FILE"
echo "Backend URL: $BACKEND_URL" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"

# --- 1. Health check ---
echo "" | tee -a "$LOG_FILE"
echo "[1/6] Health check..." | tee -a "$LOG_FILE"
curl -s -w "\nHTTP_CODE: %{http_code}\n" "$BACKEND_URL/health" 2>&1 | tee -a "$LOG_FILE"

# --- 2. API docs erisilebilir mi ---
echo "" | tee -a "$LOG_FILE"
echo "[2/6] Swagger docs..." | tee -a "$LOG_FILE"
curl -s -o /dev/null -w "HTTP_CODE: %{http_code}\n" "$BACKEND_URL/docs" 2>&1 | tee -a "$LOG_FILE"

# --- 3. Upload endpoint (OPTIONS/CORS) ---
echo "" | tee -a "$LOG_FILE"
echo "[3/6] Upload endpoint CORS preflight..." | tee -a "$LOG_FILE"
curl -s -w "\nHTTP_CODE: %{http_code}\n" \
  -X OPTIONS "$BACKEND_URL/api/v1/upload" \
  -H "Origin: http://test.local" \
  -H "Access-Control-Request-Method: POST" 2>&1 | tee -a "$LOG_FILE"

# --- 4. Test PDF olustur ---
echo "" | tee -a "$LOG_FILE"
echo "[4/6] Test PDF olusturuluyor..." | tee -a "$LOG_FILE"

python3 -c "
# Minimal gecerli PDF olustur
pdf = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 100 700 Td (Hello World) Tj ET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000266 00000 n \n0000000360 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n434\n%%EOF'
with open('/tmp/test.pdf', 'wb') as f:
    f.write(pdf)
print('OK - /tmp/test.pdf olusturuldu (%d bytes)' % len(pdf))
" 2>&1 | tee -a "$LOG_FILE"

# --- 5. PDF upload ---
echo "" | tee -a "$LOG_FILE"
echo "[5/6] PDF upload deneniyor..." | tee -a "$LOG_FILE"
UPLOAD_RESPONSE=$(curl -s -w "\n---HTTP_CODE: %{http_code}---" \
  -X POST "$BACKEND_URL/api/v1/upload" \
  -F "file=@/tmp/test.pdf;type=application/pdf" \
  --max-time 30 2>&1)
echo "$UPLOAD_RESPONSE" | tee -a "$LOG_FILE"

# HTTP kodunu ayikla
HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | grep -o 'HTTP_CODE: [0-9]*' | grep -o '[0-9]*' || echo "000")
echo "Upload HTTP Code: $HTTP_CODE" | tee -a "$LOG_FILE"

# --- 6. Container durumlari ---
echo "" | tee -a "$LOG_FILE"
echo "[6/6] Container durumlari..." | tee -a "$LOG_FILE"
docker compose -f docker-compose.dev.yml ps 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "--- Backend son 30 log satiri ---" | tee -a "$LOG_FILE"
docker compose -f docker-compose.dev.yml logs backend --tail 30 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "--- Celery son 15 log satiri ---" | tee -a "$LOG_FILE"
docker compose -f docker-compose.dev.yml logs celery-worker --tail 15 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"
echo "Test tamamlandi. Log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "Issue acmak icin:" | tee -a "$LOG_FILE"
echo "  gh issue create --repo kenan2x/translate --title 'Backend test sonuclari' --body-file $LOG_FILE" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"
