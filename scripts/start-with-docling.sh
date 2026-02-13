#!/bin/bash

# LightRAG Vietnamese Server với Docling Support
# 
# Sử dụng Docling để xử lý documents (PDF, Word, Excel) chất lượng cao
# trước khi đưa vào LightRAG embedding

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

USE_DOCLING=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --docling)
            USE_DOCLING=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--docling]"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  LightRAG Vietnamese Server${NC}"
if [ "$USE_DOCLING" = true ]; then
    echo -e "${GREEN}  (With Docling Document Processing)${NC}"
fi
echo -e "${GREEN}============================================${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PACKAGE_DIR"

echo "Working directory: $PACKAGE_DIR"

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

echo -e "${GREEN}✓${NC} Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
if ! pip show lightrag-hku >/dev/null 2>&1; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check if docling is installed
if [ "$USE_DOCLING" = true ]; then
    if ! pip show docling >/dev/null 2>&1; then
        echo -e "${YELLOW}Installing docling...${NC}"
        pip install docling
    fi
    echo -e "${GREEN}✓${NC} Docling enabled"
fi

# Functions
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

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

# Clear CUDA cache
python3 -c "import torch; torch.cuda.empty_cache()" 2>/dev/null || true

# Start Embedding Service
if check_port 8001; then
    echo -e "${YELLOW}⚠${NC}  Embedding Service already running"
else
    echo -e "${GREEN}→${NC} Starting Vietnamese Embedding Service..."
    python vietnamese_embedding_service.py > logs/embedding.log 2>&1 &
    
    if ! wait_for_service "http://localhost:8001/health" "Embedding Service"; then
        echo -e "${RED}✗${NC} Failed to start Embedding Service"
        exit 1
    fi
fi

echo ""

# Start LightRAG Server
if check_port 9621; then
    echo -e "${YELLOW}⚠${NC}  LightRAG Server already running"
else
    echo -e "${GREEN}→${NC} Starting LightRAG Server..."
    cp config/.env .env
    
    # Build command with optional docling
    LIGHTRAG_CMD="lightrag-server"
    if [ "$USE_DOCLING" = true ]; then
        LIGHTRAG_CMD="lightrag-server --docling"
        echo -e "${BLUE}ℹ${NC}  Document processing: Docling enabled"
    else
        echo -e "${BLUE}ℹ${NC}  Document processing: Standard (pypdf)"
    fi
    
    $LIGHTRAG_CMD > logs/lightrag.log 2>&1 &
    echo -e "${GREEN}✓${NC} LightRAG Server started"
    sleep 15
fi

# Cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}⚠${NC}  Shutting down..."
    pkill -f "vietnamese_embedding_service" 2>/dev/null || true
    pkill -f "lightrag-server" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Stopped"
}
trap cleanup EXIT INT TERM

# Info
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ All services running!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Services:"
echo "  - Vietnamese Embedding: http://localhost:8001 (GPU)"
echo "  - LightRAG WebUI:       http://localhost:9621"
echo "  - API Documentation:    http://localhost:9621/docs"
if [ "$USE_DOCLING" = true ]; then
    echo ""
    echo "Docling Features:"
    echo "  ✓ Advanced PDF processing (tables, layout)"
    echo "  ✓ Word document support"
    echo "  ✓ Excel spreadsheet support"
    echo "  ✓ Markdown/JSON output"
fi
echo ""
echo "Directories:"
echo "  - Upload:    ./inputs/"
echo "  - Storage:   ./rag_storage/"
echo "  - Logs:      ./logs/"
echo ""
echo -e "${YELLOW}ℹ${NC}  Press Ctrl+C to stop"
echo ""

wait
