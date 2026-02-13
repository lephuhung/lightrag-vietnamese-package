#!/bin/bash

# LightRAG Server with Detailed Timing Logs
# Khởi động server với logging chi tiết để theo dõi thờigian xử lý

echo "=========================================="
echo "Starting LightRAG with TIMING LOGS"
echo "=========================================="
echo ""

# Check if embedding service is running
if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "⚠️  WARNING: Embedding service not running on port 8001"
    echo "Please start embedding service first:"
    echo "  python vietnamese_embedding_service.py"
    exit 1
fi

echo "✅ Embedding service is running"
echo ""

# Set environment variables for detailed logging
export LIGHTING_LOG_LEVEL=INFO
export PYTHONUNBUFFERED=1

# Change to LightRAG directory
cd /root/lightRAG/LightRAG

# Activate virtual environment
source .venv/bin/activate

# Kill any existing LightRAG server
pkill -f "lightrag-server" 2>/dev/null || true
pkill -f "lightrag_server" 2>/dev/null || true
sleep 2

echo "🚀 Starting LightRAG server with timing logs..."
echo "   - Log file: /root/lightRAG/lightrag-vietnamese-package/logs/lightrag-timing.log"
echo "   - Docling: ENABLED"
echo "   - Vietnamese Embedding: ENABLED"
echo ""
echo "📊 Timing metrics will be logged with prefix: [TIMING]"
echo "   - Upload API timing"
echo "   - Docling conversion timing"
echo "   - Background processing timing"
echo ""
echo "=========================================="
echo "Server starting... Wait for 'Ready' message"
echo "=========================================="
echo ""

# Start server with docling enabled and log to file with timestamps
lightrag-server \
  --host 0.0.0.0 \
  --port 9621 \
  --working-dir /root/lightRAG/lightrag-vietnamese-package/rag_storage \
  --input-dir /root/lightRAG/lightrag-vietnamese-package/inputs \
  --docling \
  --llm-binding openai \
  --llm-binding-host http://10.8.0.8:8000/v1 \
  --llm-model glm-4-9b \
  --embedding-binding openai \
  --embedding-binding-host http://localhost:8001/v1 \
  --embedding-model vietnamese-embedding \
  --max-async 4 \
  --max-tokens 1200 \
  --max-embed-tokens 200 \
  --summary-language Vietnamese \
  --system-prompt "You are a helpful assistant for Vietnamese government documents. Always respond in Vietnamese." \
  --timeout 300 \
  --log-level INFO 2>&1 | tee /root/lightRAG/lightrag-vietnamese-package/logs/lightrag-timing.log
