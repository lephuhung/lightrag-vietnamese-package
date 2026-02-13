#!/bin/bash

# LightRAG Server Startup Script with Vietnamese Embedding
# 
# Script này sẽ:
# 1. Khởi động Vietnamese Embedding Service tại port 8001
# 2. Đợi service sẵn sàng
# 3. Khởi động LightRAG Server tại port 9621
#
# Cách sử dụng:
#   chmod +x start_lightrag_server.sh
#   ./start_lightrag_server.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  LightRAG Server + Vietnamese Embedding${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo -e "${GREEN}✓${NC} Activating virtual environment..."
    source .venv/bin/activate
else
    echo -e "${RED}✗${NC} Virtual environment not found!"
    echo "Please run: python3 -m venv .venv"
    exit 1
fi

# Function to check if a port is in use
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
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳${NC} Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $service_name is ready!"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}✗${NC} $service_name failed to start after ${max_attempts}s"
    return 1
}

# Check if embedding service port is already in use
if check_port 8001; then
    echo -e "${YELLOW}⚠${NC}  Port 8001 is already in use."
    echo -e "    Vietnamese Embedding Service may already be running."
else
    # Start Vietnamese Embedding Service
    echo -e "${GREEN}→${NC} Starting Vietnamese Embedding Service on port 8001..."
    python vietnamese_embedding_service.py > embedding_service.log 2>&1 &
    EMBEDDING_PID=$!
    
    # Wait for embedding service
    if ! wait_for_service "http://localhost:8001/health" "Vietnamese Embedding Service"; then
        echo -e "${RED}✗${NC} Failed to start Vietnamese Embedding Service"
        echo "Check embedding_service.log for details"
        exit 1
    fi
    
    echo -e "${GREEN}✓${NC} Embedding Service PID: $EMBEDDING_PID"
fi

echo ""

# Check if LightRAG Server port is already in use
if check_port 9621; then
    echo -e "${YELLOW}⚠${NC}  Port 9621 is already in use."
    echo -e "    LightRAG Server may already be running."
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}✓${NC} LightRAG Server is already running!"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo "Access URLs:"
    echo "  - WebUI:        http://localhost:9621"
    echo "  - API Docs:     http://localhost:9621/docs"
    echo "  - Health:       http://localhost:9621/health"
    exit 0
fi

# Start LightRAG Server
echo -e "${GREEN}→${NC} Starting LightRAG Server on port 9621..."
echo ""

# Trap to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}⚠${NC}  Shutting down services..."
    if [ ! -z "$EMBEDDING_PID" ]; then
        kill $EMBEDDING_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✓${NC} Services stopped"
}
trap cleanup EXIT INT TERM

echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✓${NC} All services started successfully!"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "Access URLs:"
echo "  - WebUI:        http://localhost:9621"
echo "  - API Docs:     http://localhost:9621/docs"
echo "  - ReDoc:        http://localhost:9621/redoc"
echo "  - Health:       http://localhost:9621/health"
echo ""
echo "Embedding Service:"
echo "  - Endpoint:     http://localhost:8001/v1/embeddings"
echo "  - Health:       http://localhost:8001/health"
echo ""
echo -e "${YELLOW}ℹ${NC}  Press Ctrl+C to stop all services"
echo ""

# Start LightRAG Server (this will block)
lightrag-server
