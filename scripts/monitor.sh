#!/bin/bash

# Performance Monitoring Script for LightRAG
# 
# Usage: ./scripts/monitor.sh

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  LightRAG Performance Monitor${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Check services
echo -e "${BLUE}=== SERVICES STATUS ===${NC}"

# Embedding service
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    emb_data=$(curl -s http://localhost:8001/health)
    device=$(echo $emb_data | python3 -c "import sys, json; print(json.load(sys.stdin).get('device', 'unknown'))")
    echo -e "${GREEN}✓${NC} Embedding Service: Running ($device)"
else
    echo -e "${RED}✗${NC} Embedding Service: Not responding"
fi

# LightRAG
if curl -s http://localhost:9621/health > /dev/null 2>&1; then
    lr_data=$(curl -s http://localhost:9621/health)
    pipeline=$(echo $lr_data | python3 -c "import sys, json; print('busy' if json.load(sys.stdin).get('pipeline_busy') else 'idle')")
    echo -e "${GREEN}✓${NC} LightRAG Server: Running (pipeline: $pipeline)"
else
    echo -e "${RED}✗${NC} LightRAG Server: Not responding"
fi

echo ""

# GPU Status
echo -e "${BLUE}=== GPU STATUS ===${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader | while read line; do
        echo "GPU: $line"
    done
    
    echo ""
    echo "GPU Processes:"
    nvidia-smi --query-compute-apps=pid,name,used_memory --format=csv,noheader | head -5
else
    echo "nvidia-smi not available"
fi

echo ""

# Documents Status
echo -e "${BLUE}=== DOCUMENTS STATUS ===${NC}"
doc_data=$(curl -s "http://localhost:9621/documents?limit=100" 2>/dev/null)
if [ $? -eq 0 ]; then
    total=$(echo $doc_data | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))")
    echo "Total documents: $total"
    
    if [ $total -gt 0 ]; then
        echo ""
        echo "Status breakdown:"
        echo $doc_data | python3 -c "
import sys, json
data = json.load(sys.stdin)
statuses = {}
for doc in data.get('documents', []):
    status = doc.get('status', 'unknown')
    statuses[status] = statuses.get(status, 0) + 1
for status, count in sorted(statuses.items()):
    print(f'  {status}: {count}')
"
    fi
else
    echo "Cannot fetch document status"
fi

echo ""

# Recent Processing Activity
echo -e "${BLUE}=== RECENT ACTIVITY (last 50 lines) ===${NC}"
if [ -f logs/lightrag.log ]; then
    echo "Recent processing:"
    tail -50 logs/lightrag.log | grep -E "(Processing|Extracted|Completed|chunk)" | tail -10
else
    echo "No log file found"
fi

echo ""

# Performance Test
echo -e "${BLUE}=== PERFORMANCE TEST ===${NC}"
echo "Testing embedding speed..."
start_time=$(date +%s%N)
curl -s -X POST http://localhost:8001/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": "Performance test sentence", "model": "vietnamese-embedding"}' > /dev/null 2>&1
end_time=$(date +%s%N)
elapsed=$(( (end_time - start_time) / 1000000 ))
echo "Embedding latency: ${elapsed}ms"

echo ""

# Recommendations
echo -e "${BLUE}=== RECOMMENDATIONS ===${NC}"

# Check if GPU is being used
if command -v nvidia-smi &> /dev/null; then
    gpu_util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1 | tr -d ' ')
    if [ "$gpu_util" -lt 10 ]; then
        echo -e "${YELLOW}⚠${NC} GPU utilization is low (${gpu_util}%)"
        echo "  - This is normal when idle"
        echo "  - Should increase during document processing"
    else
        echo -e "${GREEN}✓${NC} GPU is active (${gpu_util}%)"
    fi
fi

# Check document processing
if [ "$total" -gt 0 ]; then
    processing=$(echo $doc_data | python3 -c "import sys, json; d=json.load(sys.stdin); print(sum(1 for doc in d.get('documents',[]) if doc.get('status')=='processing'))")
    if [ "$processing" -gt 0 ]; then
        echo -e "${YELLOW}ℹ${NC} $processing document(s) currently processing"
        echo "  - Normal for large documents or high volume"
    fi
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo "Press Ctrl+C to exit, or run with --watch to monitor continuously"
echo -e "${GREEN}============================================${NC}"

# Continuous monitoring if --watch flag
if [ "$1" == "--watch" ]; then
    echo ""
    echo "Monitoring every 5 seconds... (Ctrl+C to stop)"
    while true; do
        sleep 5
        clear
        $0
    done
fi
