#!/bin/bash

# LightRAG Vietnamese Server with Docling Markdown Export
# 
# Tự động lưu markdown files từ Docling vào thư mục docling_markdown/

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  LightRAG Vietnamese Server${NC}"
echo -e "${GREEN}  With Docling Markdown Export${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PACKAGE_DIR"

echo "Working directory: $PACKAGE_DIR"

# Create markdown output directory
MARKDOWN_DIR="$PACKAGE_DIR/docling_markdown"
mkdir -p "$MARKDOWN_DIR"
echo -e "${BLUE}📁 Markdown export directory: $MARKDOWN_DIR${NC}"
echo ""

# Activate virtual environment
source /root/lightRAG/LightRAG/.venv/bin/activate

# Function to check port
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Clear CUDA cache
python3 -c "import torch; torch.cuda.empty_cache()" 2>/dev/null || true

# Start Embedding Service
if check_port 8001; then
    echo -e "${YELLOW}⚠${NC}  Embedding Service already running"
else
    echo -e "${GREEN}→${NC} Starting Vietnamese Embedding Service..."
    nohup python vietnamese_embedding_service.py > logs/embedding.log 2>&1 &
    
    echo "   Waiting for model load (20s)..."
    sleep 20
    
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Embedding Service ready (GPU)"
    else
        echo -e "${YELLOW}⚠${NC}  Embedding Service still loading..."
    fi
fi

echo ""

# Start LightRAG with Docling
if check_port 9621; then
    echo -e "${YELLOW}⚠${NC}  LightRAG Server already running"
else
    echo -e "${GREEN}→${NC} Starting LightRAG Server..."
    echo -e "${BLUE}   Docling: ENABLED${NC}"
    echo -e "${BLUE}   Markdown export: $MARKDOWN_DIR${NC}"
    
    # Copy config
    cp config/.env .env
    
    # Export markdown directory path for Python to use
    export DOCLING_MARKDOWN_DIR="$MARKDOWN_DIR"
    
    # Start LightRAG with docling
    lightrag-server --docling > logs/lightrag.log 2>&1 &
    
    echo "   Waiting for initialization (15s)..."
    sleep 15
    
    echo -e "${GREEN}✓${NC} LightRAG Server started"
fi

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
echo "Docling Markdown Export:"
echo "  - Directory: $MARKDOWN_DIR"
echo "  - Files will be saved as: {filename}.md"
echo ""
echo "Directories:"
echo "  - Upload documents: ./inputs/"
echo "  - Markdown export:  ./docling_markdown/"
echo "  - Storage:          ./rag_storage/"
echo "  - Logs:             ./logs/"
echo ""
echo -e "${YELLOW}ℹ${NC}  Press Ctrl+C to stop all services"
echo ""

# Keep script running
cleanup() {
    echo ""
    echo -e "${YELLOW}⚠${NC}  Shutting down..."
    pkill -f "vietnamese_embedding_service" 2>/dev/null || true
    pkill -f "lightrag-server" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Services stopped"
}
trap cleanup EXIT INT TERM

wait
