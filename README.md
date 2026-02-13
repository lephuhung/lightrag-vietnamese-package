# LightRAG Vietnamese Package

Package triển khai LightRAG Server với Local LLM và Vietnamese Embedding (GPU)

## 🎯 Tính năng

- **Local LLM**: Qwen3-Coder-30B-A3B-Instruct qua OpenAI-compatible API
- **Vietnamese Embedding**: dangvantuan/vietnamese-embedding (GPU accelerated)
- **Docling Support**: Xử lý PDF, Word, Excel chất lượng cao (tables, layout, OCR)
- **WebUI**: Giao diện web quản lý documents và chat
- **API**: REST API đầy đủ với Swagger docs

## 📁 Cấu trúc

```
lightrag-vietnamese-package/
├── vietnamese_embedding_service.py  # Vietnamese embedding (GPU)
├── lightrag_vietnamese_demo.py      # Demo script
├── lightrag_vietnamese_benchmark.py # Benchmark tool
├── requirements.txt                 # Dependencies
├── scripts/
│   ├── start.sh                     # Standard startup
│   └── start-with-docling.sh        # With Docling support
├── config/
│   ├── .env                         # Configuration
│   └── .env.example                 # Template
├── inputs/                          # Upload documents here
├── rag_storage/                     # RAG data storage
├── logs/                            # Service logs
├── README.md                        # This file
├── DOCLING_GUIDE.md                 # Docling documentation
└── QUICKSTART.md                    # Quick start guide
```

## 🚀 Cài đặt

1. Tạo virtual environment:
   cd lightrag-vietnamese-package
   python3 -m venv .venv
   source .venv/bin/activate

2. Cài đặt dependencies:
   pip install -r requirements.txt

3. Chạy:
   ./scripts/start.sh

## 🔥 Chạy với Docling (Khuyến nghị cho PDF/Word phức tạp)

Docling giúp xử lý documents chất lượng cao hơn:

```bash
# Cách 1: Dùng script
./scripts/start-with-docling.sh --docling

# Cách 2: Manual
cp config/.env .env
lightrag-server --docling
```

Xem `DOCLING_GUIDE.md` để biết thêm chi tiết.

## 🌐 Truy cập

- WebUI: http://localhost:9621
- API Docs: http://localhost:9621/docs
- Embedding: http://localhost:8001

