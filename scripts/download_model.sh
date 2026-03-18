#!/bin/bash
###############################################
# DocLayout-YOLO ONNX model indirme
# Kullanim: ./scripts/download_model.sh
# Proxy: HTTP_PROXY env varsa otomatik kullanir
###############################################
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="$SCRIPT_DIR/../models/babeldoc/models"
mkdir -p "$DEST"
MODEL="$DEST/doclayout_yolo_docstructbench_imgsz1024.onnx"

if [ -f "$MODEL" ] && [ -s "$MODEL" ]; then
    SIZE=$(ls -lh "$MODEL" | awk '{print $5}')
    echo "Model zaten mevcut: $MODEL ($SIZE)"
    exit 0
fi

PROXY_FLAG=""
if [ -n "${HTTP_PROXY:-}" ]; then
    PROXY_FLAG="--proxy $HTTP_PROXY"
    echo "Proxy kullaniliyor: $HTTP_PROXY"
fi

echo "DocLayout-YOLO ONNX model indiriliyor..."
echo ""

# Kaynak 1: HuggingFace (direkt)
echo "[1/3] huggingface.co deneniyor..."
if curl -fSL --retry 2 --connect-timeout 15 --max-time 300 $PROXY_FLAG \
    -o "$MODEL" \
    "https://huggingface.co/wybxc/DocLayout-YOLO-DocStructBench-onnx/resolve/main/doclayout_yolo_docstructbench_imgsz1024.onnx" 2>&1; then
    echo "OK: $(ls -lh "$MODEL")"
    exit 0
fi

# Kaynak 2: hf-mirror.com (Cin mirror)
echo "[2/3] hf-mirror.com deneniyor..."
if curl -fSL --retry 2 --connect-timeout 15 --max-time 300 $PROXY_FLAG \
    -o "$MODEL" \
    "https://hf-mirror.com/wybxc/DocLayout-YOLO-DocStructBench-onnx/resolve/main/doclayout_yolo_docstructbench_imgsz1024.onnx" 2>&1; then
    echo "OK: $(ls -lh "$MODEL")"
    exit 0
fi

# Kaynak 3: ModelScope (Alibaba)
echo "[3/3] modelscope.cn deneniyor..."
if curl -fSL --retry 2 --connect-timeout 15 --max-time 300 $PROXY_FLAG \
    -o "$MODEL" \
    "https://www.modelscope.cn/models/AI-ModelScope/DocLayout-YOLO-DocStructBench-onnx/resolve/master/doclayout_yolo_docstructbench_imgsz1024.onnx" 2>&1; then
    echo "OK: $(ls -lh "$MODEL")"
    exit 0
fi

# Hepsi basarisiz
rm -f "$MODEL"
echo ""
echo "HATA: Hicbir kaynaktan indirilemedi."
echo "Manuel indirme:"
echo "  curl -x \$HTTP_PROXY -L -o $MODEL \\"
echo "    'https://huggingface.co/wybxc/DocLayout-YOLO-DocStructBench-onnx/resolve/main/doclayout_yolo_docstructbench_imgsz1024.onnx'"
exit 1
