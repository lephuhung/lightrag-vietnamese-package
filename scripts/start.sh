#!/bin/bash

# LightRAG Vietnamese Server Startup Script
# 
# Khởi động cả 2 services:
# 1. Vietnamese Embedding Service (Port 8001) - GPU
# 2. LightRAG Server (Port 9621)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  LightRAG Vietnamese Server${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PACKAGE_DIR"

echo "Working directory: $PACKAGE_DIR"

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
fi

echo -e "${GREEN}✓${NC} Activating virtual environment..."
source .venv/bin/activate

# Install dependencies if needed
if ! pip show lightrag-hku > /dev/null 2>&1; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Function to check port
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳${NC} Waiting for $name..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $name ready!"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e "${RED}✗${NC} $name failed to start"
    return 1
}

# Clear CUDA cache if using GPU
python3 -c "import torch; torch.cuda.empty_cache()" 2>/dev/null || true

# Start Embedding Service
if check_port 8001; then
    echo -e "${YELLOW}⚠${NC}  Embedding Service already running on port 8001"
else
    echo -e "${GREEN}→${NC} Starting Vietnamese Embedding Service..."
    python vietnamese_embedding_service.py > logs/embedding.log 2>&1 &
    EMBEDDING_PID=$!
    
    if ! wait_for_service "http://localhost:8001/health" "Embedding Service"; then
        echo -e "${RED}✗${NC} Failed to start Embedding Service"
        echo "Check logs/embedding.log for details"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Embedding Service PID: $EMBEDDING_PID"
fi

echo ""

# Start LightRAG Server
if check_port 9621; then
    echo -e "${YELLOW}⚠${NC}  LightRAG Server already running on port 9621"
else
    echo -e "${GREEN}→${NC} Starting LightRAG Server..."
    
    # Copy .env to current directory
    cp config/.env .env
    
    lightrag-server --docling > logs/lightrag.log 2>&1 &
echo -e "${GREEN}✓${NC} LightRAG Server started"
    
    sleep 15
fi

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}⚠${NC}  Shutting down services..."
    pkill -f "vietnamese_embedding_service" 2>/dev/null || true
    pkill -f "lightrag-server --docling" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Services stopped"
}
trap cleanup EXIT INT TERM

# Display info
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ All services running!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Services:"
echo "  - Vietnamese Embedding: http://localhost:8001 (GPU)"
echo "  - LightRAG WebUI:       http://localhost:9621"
echo "  - API Documentation:    http://localhost:9621/docs"
echo ""
echo "Directories:"
echo "  - Upload documents to: ./inputs/"
echo "  - Storage:            ./rag_storage/"
echo "  - Logs:               ./logs/"
echo ""
echo -e "${YELLOW}ℹ${NC}  Press Ctrl+C to stop all services"
echo ""

# Keep script running
wait
