# LightRAG Vietnamese - Quick Start

## 5 phút chạy được

### 1. Cài đặt (2 phút)

```bash
cd lightrag-vietnamese-package
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Cấu hình (1 phút)

Kiểm tra file `config/.env` và đảm bảo thông tin đúng:

```bash
# LLM của bạn
LLM_BINDING_HOST=http://10.8.0.8:8000/v1  # Thay đổi nếu cần
LLM_MODEL=Qwen3-Coder-30B-A3B-Instruct     # Tên model của bạn
```

### 3. Chạy (1 phút)

```bash
./scripts/start.sh
```

### 4. Truy cập (1 phút)

Mở browser: http://localhost:9621

## Upload và Query

### Upload tài liệu:
- Kéo thả file vào WebUI
- Hoặc copy file vào `inputs/` và nhấn "Scan"
- Hoặc dùng API: `curl -F "file=@doc.pdf" http://localhost:9621/documents/upload`

### Query:
- Chat trên WebUI
- Hoặc API: `curl -X POST http://localhost:9621/query -d '{"query":"?"}'`

## Dừng

Nhấn `Ctrl+C` hoặc:
```bash
pkill -f "vietnamese_embedding"
pkill -f "lightrag-server"
```

## Xử lý lỗi

**Lỗi "Model does not exist":**
```bash
curl http://10.8.0.8:8000/v1/models  # Kiểm tra tên model đúng
```

**Lỗi CUDA:**
- Edit `vietnamese_embedding_service.py`
- Đổi `device = "cuda"` thành `device = "cpu"`

**Port đã dùng:**
```bash
lsof -i :8001  # hoặc :9621
kill -9 <PID>
```

## API nhanh

```bash
# Health check
curl http://localhost:9621/health

# Upload
curl -F "file=@doc.pdf" http://localhost:9621/documents/upload

# Query
curl -X POST http://localhost:9621/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Câu hỏi?","mode":"hybrid"}'
```

Xem `README.md` đầy đủ để biết thêm chi tiết.
