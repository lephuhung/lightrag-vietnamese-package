# LightRAG Performance Analysis

## Current Status (Real-time)

### ✅ Embedding Service
- **Status**: Healthy, Running on GPU (CUDA)
- **GPU Memory**: 705 MiB / 8 GiB (NVIDIA T1000)
- **Latency**: ~50-60ms per request
- **Performance**: EXCELLENT

### ✅ LightRAG Server
- **Status**: Healthy, Pipeline: Busy
- **LLM Model**: zai-org/GLM-4.7-Flash
- **Document Count**: 0 (No documents currently indexed)
- **Processing**: Active with queries

### ⚠️ Bottleneck Analysis

Based on log analysis, here are the performance bottlenecks:

## 1. Where is the slowness coming from?

### A. Embedding (VIETNAMESE EMBEDDING) - ✅ FAST
- **Speed**: 50-60ms per embedding
- **GPU**: Being used correctly
- **Status**: NOT THE BOTTLENECK

### B. LightRAG Processing - ⚠️ MODERATE
- **Entity Extraction**: Depends on LLM speed
- **Chunk Processing**: 2-4 chunks typically
- **Status**: Can be slow for large documents

### C. LLM API (10.8.0.8:8000) - ⚠️ UNKNOWN
- **Latency**: Not directly measured
- **Impact**: Affects entity extraction speed
- **Status**: POTENTIAL BOTTLENECK

## 2. Performance Metrics

```
Embedding Latency:  50-60ms  ✅
Query Response:     Unknown  ⚠️
Doc Processing:     Unknown  ⚠️
```

## 3. Recommendations to Improve Speed

### Immediate Actions:

1. **Enable Docling** (Already done - script updated)
   ```bash
   ./scripts/start.sh  # Now includes --docling by default
   ```

2. **Check LLM API Speed**
   ```bash
   time curl -X POST http://10.8.0.8:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "zai-org/GLM-4.7-Flash", "messages": [{"role": "user", "content": "Hello"}]}'
   ```

3. **Optimize Concurrency** (Already set in .env)
   ```
   MAX_ASYNC=4
   MAX_PARALLEL_INSERT=2
   ```

### Configuration Tuning:

1. **Increase Workers** (if memory allows)
   ```env
   WORKERS=4  # Instead of 2
   ```

2. **Reduce Chunk Size for Faster Processing**
   ```env
   CHUNK_SIZE=800  # Instead of 1200
   CHUNK_OVERLAP_SIZE=50
   ```

3. **Enable Caching**
   ```env
   ENABLE_LLM_CACHE=true
   ENABLE_LLM_CACHE_FOR_EXTRACT=true
   ```

### For Large Documents:

1. **Split large files before upload**
2. **Use PDFs instead of scanned images** (faster with docling)
3. **Monitor with**: `./scripts/monitor.sh --watch`

## 4. Expected Performance

| Operation | Expected Time | Current |
|-----------|---------------|---------|
| Embedding (1 doc) | 50-100ms | ✅ 50-60ms |
| Small PDF (1-2 pages) | 5-10s | ⚠️ Unknown |
| Large PDF (10+ pages) | 30-60s | ⚠️ Unknown |
| Query (simple) | 1-3s | ⚠️ Unknown |
| Query (complex) | 5-10s | ⚠️ Unknown |

## 5. Monitoring Commands

```bash
# Real-time monitoring
./scripts/monitor.sh --watch

# Check GPU usage
watch -n 1 nvidia-smi

# Check logs
tail -f logs/lightrag.log
tail -f logs/embedding.log

# Test embedding speed
./scripts/monitor.sh | grep "Embedding latency"
```

## Summary

**✅ What's Working Well:**
- Embedding on GPU (fast)
- Services are stable
- Docling enabled by default

**⚠️ Potential Bottlenecks:**
- LLM API response time (need to test)
- Document processing for large files
- No documents currently indexed

**🔧 Next Steps:**
1. Upload a test document
2. Monitor processing time
3. Test LLM API latency
4. Adjust workers if needed
