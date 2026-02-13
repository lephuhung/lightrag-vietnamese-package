# Sử dụng Docling với LightRAG

## Docling là gì?

Docling là thư viện xử lý documents chất lượng cao, hỗ trợ:
- **PDF**: Layout preservation, tables, figures
- **Word (DOCX)**: Full formatting support
- **Excel (XLSX)**: Table extraction
- **PowerPoint (PPTX)**: Slide content
- **HTML, Markdown**: Native support
- **Images (OCR)**: Text extraction from images

## Cách chạy với Docling

### Cách 1: Sử dụng script mới

```bash
cd lightrag-vietnamese-package
./scripts/start-with-docling.sh --docling
```

### Cách 2: Sử dụng lệnh trực tiếp

```bash
# Cài đặt docling
pip install docling

# Chạy LightRAG với docling
cp config/.env .env
lightrag-server --docling
```

### Cách 3: Sửa file .env

Thêm vào `config/.env`:

```bash
# Enable docling
DOCLING=true
```

## So sánh: Standard vs Docling

| Feature | Standard (PyPDF) | Docling |
|---------|------------------|---------|
| PDF Text | ✅ Basic | ✅ Advanced (layout-aware) |
| PDF Tables | ⚠️ Limited | ✅ Full support |
| PDF Images | ❌ No | ✅ OCR support |
| Word (DOCX) | ✅ Yes | ✅ Better formatting |
| Excel (XLSX) | ✅ Basic | ✅ Table structure |
| HTML/Markdown | ⚠️ Basic | ✅ Native |
| Processing Speed | 🚀 Fast | 🐢 Slower (but better quality) |

## Khi nào dùng Docling?

### Nên dùng Docling khi:
- PDF có nhiều tables, figures
- Cần preserve layout của tài liệu
- Xử lý scanned PDFs (OCR)
- Tài liệu Word phức tạp với formatting
- Excel với nhiều sheets và formulas

### Nên dùng Standard khi:
- Chỉ cần extract text đơn giản
- Performance là ưu tiên
- PDF là text-based đơn giản
- File size nhỏ, ít formatting

## Ví dụ sử dụng

### Upload PDF với tables

```bash
# File PDF có bảng dữ liệu
curl -X POST http://localhost:9621/documents/upload \
  -F "file=@report_with_tables.pdf"

# Docling sẽ preserve structure của tables
```

### Upload scanned PDF (OCR)

```bash
# File PDF scan từ máy scan
curl -X POST http://localhost:9621/documents/upload \
  -F "file=@scanned_document.pdf"

# Docling sẽ dùng OCR để extract text
```

### Upload Word document

```bash
# File Word với nhiều formatting
curl -X POST http://localhost:9621/documents/upload \
  -F "file=@complex_document.docx"

# Docling sẽ preserve headings, lists, tables
```

## Performance Considerations

Docling chậm hơn standard processor vì:
- Layout analysis
- Table detection
- OCR processing
- Format preservation

**Khuyến nghị:**
- Dùng GPU nếu có thể cho OCR
- Batch processing cho nhiều files
- Cache kết quả khi có thể

## Troubleshooting

### Lỗi "docling not found"

```bash
pip install docling
```

### Lỗi OCR

```bash
# Cài thêm dependencies cho OCR
pip install docling[ocr]
```

### Memory issues với large PDFs

```bash
# Giảm batch size trong .env
MAX_PARALLEL_INSERT=1
```

## Configuration

### Trong .env

```bash
# Bật docling
DOCLING=true

# Hoặc dùng command line
# lightrag-server --docling
```

### Advanced Docling Options

```python
# Trong code nếu cần customize
docling_options = {
    "do_ocr": True,
    "ocr_lang": ["vi", "en"],
    "table_structure": True,
    "image_export": False
}
```

## Kết hợp với Vietnamese Embedding

Pipeline hoàn chỉnh:

```
Document (PDF/Word/Excel)
    ↓
Docling Processor
    ↓
Extract structured text/markdown
    ↓
Vietnamese Embedding (GPU)
    ↓
LightRAG Knowledge Graph
    ↓
Query/Chat
```

## References

- Docling GitHub: https://github.com/docling-doc/docling
- LightRAG Doc: https://github.com/HKUDS/LightRAG
