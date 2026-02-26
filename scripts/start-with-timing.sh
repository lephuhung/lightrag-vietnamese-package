#!/bin/bash

# LightRAG Server with Detailed Timing Logs
# Khởi động server với logging chi tiết để theo dõi thời gian xử lý

echo "=========================================="
echo "Starting LightRAG with TIMING LOGS"
echo "=========================================="
echo ""

# Get script setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PACKAGE_DIR"

echo "Working directory: $PACKAGE_DIR"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "llm" ]; then
    source llm/bin/activate
else
    echo "⚠️  WARNING: Virtual environment not found!"
fi

# Check if embedding service is running
if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "⚠️  WARNING: Embedding service not running on port 8001"
    echo "Please start embedding service first:"
    echo "  python vietnamese_embedding_service.py"
    # We don't exit here, just warn, as user might have it elsewhere
fi

echo "✅ Embedding service check complete"
echo ""

# Set environment variables for detailed logging
export LIGHTING_LOG_LEVEL=INFO
export PYTHONUNBUFFERED=1

# Kill any existing LightRAG server
pkill -f "lightrag-server" 2>/dev/null || true
pkill -f "lightrag_server" 2>/dev/null || true
sleep 2

echo "🚀 Starting LightRAG server with timing logs..."
echo "   - Log file: logs/lightrag-timing.log"
echo "   - Docling: ENABLED"
echo "   - Vietnamese Embedding: ENABLED"
echo "   - Config: Using .env file"
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

# Ensure logs directory exists
mkdir -p logs

# Start server with docling enabled and log to file with timestamps
# Rely on .env for LLM/Embedding config instead of passing invalid CLI args
lightrag-server \
  --host 0.0.0.0 \
  --port 9621 \
  --docling \
  --log-level INFO 2>&1 | tee logs/lightrag-timing.log
