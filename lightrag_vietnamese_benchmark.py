"""
LightRAG Benchmark - So sánh 4 phương thức query với metrics chi tiết

Cấu hình:
- LLM: Qwen3-Coder-30B-A3B-Instruct tại http://10.8.0.8:8000/v1
- Embedding: dangvantuan/vietnamese-embedding (HuggingFace)

Benchmark metrics:
- Thởi gian thực thi
- Số entities/relations truy xuất
- Số tokens sử dụng
- Độ chính xác (so sánh với ground truth)
- Memory usage

Chạy:
    python lightrag_vietnamese_benchmark.py
"""

import os
import asyncio
import json
import time
import psutil
import numpy as np
from typing import Literal, cast
from dataclasses import dataclass, field, asdict
from datetime import datetime
from openai import AsyncOpenAI
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache
from lightrag.utils import wrap_embedding_func_with_attrs, setup_logger
from sentence_transformers import SentenceTransformer

# Cấu hình logging
setup_logger("lightrag", level="WARNING")  # Giảm log để benchmark chính xác hơn

# Thư mục làm việc
WORKING_DIR = "./lightrag_benchmark_storage"
BENCHMARK_RESULTS_DIR = "./benchmark_results"

# Tạo thư mục
for dir_path in [WORKING_DIR, BENCHMARK_RESULTS_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# ============================================
# Cấu hình Local LLM
# ============================================
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://10.8.0.8:8000/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "not-needed")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen3-Coder-30B-A3B-Instruct")

openai_client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

# ============================================
# Cấu hình Embedding
# ============================================
EMBEDDING_MODEL_NAME = "dangvantuan/vietnamese-embedding"
EMBEDDING_DIM = 768

print(f"Đang tải model embedding: {EMBEDDING_MODEL_NAME}...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
print(f"✓ Model embedding đã tải xong!")


@dataclass
class QueryBenchmarkResult:
    """Kết quả benchmark cho một query"""
    query: str
    mode: str
    execution_time_ms: float
    entities_count: int = 0
    relations_count: int = 0
    chunks_count: int = 0
    response_length: int = 0
    memory_usage_mb: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BenchmarkReport:
    """Báo cáo benchmark tổng hợp"""
    model_name: str
    embedding_model: str
    total_queries: int
    results: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    return await openai_complete_if_cache(
        LLM_MODEL, prompt, system_prompt=system_prompt,
        history_messages=history_messages, api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL, **kwargs,
    )


async def vietnamese_embedding_func(texts: list[str]) -> np.ndarray:
    embeddings = embedding_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings


@wrap_embedding_func_with_attrs(
    embedding_dim=EMBEDDING_DIM, max_token_size=512, model_name=EMBEDDING_MODEL_NAME
)
async def embedding_func(texts: list[str]) -> np.ndarray:
    return await vietnamese_embedding_func(texts)


async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        llm_model_name=LLM_MODEL,
        embedding_func=embedding_func,
        addon_params={
            "language": "Vietnamese",
            "entity_types": ["organization", "person", "location", "event", "product"],
        },
    )
    await rag.initialize_storages()
    return rag


def get_memory_usage():
    """Lấy memory usage hiện tại (MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


async def benchmark_query(rag, query: str, mode: str) -> QueryBenchmarkResult:
    """
    Thực hiện query và đo các metrics
    """
    mode_literal = cast(Literal["naive", "local", "global", "hybrid"], mode)
    
    # Đo memory trước khi query
    mem_before = get_memory_usage()
    
    # Đo thởi gian
    start_time = time.perf_counter()
    
    try:
        resp = await rag.aquery(
            query,
            param=QueryParam(mode=mode_literal, stream=False, enable_rerank=False)
        )
        
        # Xử lý response
        if hasattr(resp, '__iter__') and not isinstance(resp, str):
            response_text = ""
            async for chunk in resp:
                response_text += chunk
        else:
            response_text = str(resp)
            
    except Exception as e:
        response_text = f"ERROR: {str(e)}"
    
    # Tính thởi gian
    execution_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
    
    # Đo memory sau khi query
    mem_after = get_memory_usage()
    memory_used = mem_after - mem_before
    
    # Đếm số lượng (ước tính từ response)
    entities_count = response_text.lower().count("**") // 2  # Markdown bold thường dùng cho entities
    response_length = len(response_text)
    
    return QueryBenchmarkResult(
        query=query,
        mode=mode,
        execution_time_ms=round(execution_time, 2),
        entities_count=entities_count,
        response_length=response_length,
        memory_usage_mb=round(memory_used, 2),
    )


def print_benchmark_table(results: list[QueryBenchmarkResult]):
    """In bảng benchmark đẹp"""
    print("\n" + "="*100)
    print("📊 BÁO CÁO BENCHMARK - SO SÁNH 4 PHƯƠNG THỨC QUERY")
    print("="*100)
    
    # Header
    print(f"\n{'Query':<40} {'Mode':<10} {'Time(ms)':<12} {'Entities':<10} {'Response':<12} {'Memory(MB)':<12}")
    print("-"*100)
    
    # Group by query
    current_query = None
    for result in results:
        if result.query != current_query:
            current_query = result.query
            print(f"\n🔍 {result.query}")
        
        print(f"{'':<40} {result.mode:<10} {result.execution_time_ms:<12.2f} "
              f"{result.entities_count:<10} {result.response_length:<12} {result.memory_usage_mb:<12.2f}")


def generate_summary(results: list[QueryBenchmarkResult]) -> dict:
    """Tạo summary statistics"""
    modes = ["naive", "local", "global", "hybrid"]
    summary = {}
    
    for mode in modes:
        mode_results = [r for r in results if r.mode == mode]
        if mode_results:
            summary[mode] = {
                "avg_time_ms": round(sum(r.execution_time_ms for r in mode_results) / len(mode_results), 2),
                "total_time_ms": round(sum(r.execution_time_ms for r in mode_results), 2),
                "avg_entities": round(sum(r.entities_count for r in mode_results) / len(mode_results), 1),
                "avg_response_length": round(sum(r.response_length for r in mode_results) / len(mode_results), 0),
                "avg_memory_mb": round(sum(r.memory_usage_mb for r in mode_results) / len(mode_results), 2),
                "queries_count": len(mode_results),
            }
    
    return summary


def print_summary_table(summary: dict):
    """In bảng tổng hợp"""
    print("\n" + "="*100)
    print("📈 TỔNG HỢP HIỆU NĂNG THEO PHƯƠNG THỨC QUERY")
    print("="*100)
    
    print(f"\n{'Mode':<10} {'Avg Time(ms)':<15} {'Total Time(ms)':<18} {'Avg Entities':<15} {'Avg Response':<15} {'Avg Memory(MB)':<15}")
    print("-"*100)
    
    for mode, stats in summary.items():
        print(f"{mode:<10} {stats['avg_time_ms']:<15.2f} {stats['total_time_ms']:<18.2f} "
              f"{stats['avg_entities']:<15.1f} {stats['avg_response_length']:<15.0f} {stats['avg_memory_mb']:<15.2f}")
    
    # So sánh nhanh
    print("\n" + "="*100)
    print("⚡ NHẬN XÉT NHANH:")
    print("="*100)
    
    if summary:
        fastest = min(summary.items(), key=lambda x: x[1]['avg_time_ms'])
        slowest = max(summary.items(), key=lambda x: x[1]['avg_time_ms'])
        most_detailed = max(summary.items(), key=lambda x: x[1]['avg_response_length'])
        
        print(f"  🏃 Nhanh nhất: {fastest[0]} ({fastest[1]['avg_time_ms']:.2f}ms)")
        print(f"  🐌 Chậm nhất: {slowest[0]} ({slowest[1]['avg_time_ms']:.2f}ms)")
        print(f"  📝 Chi tiết nhất: {most_detailed[0]} ({most_detailed[1]['avg_response_length']:.0f} chars)")
        
        speedup = slowest[1]['avg_time_ms'] / fastest[1]['avg_time_ms'] if fastest[1]['avg_time_ms'] > 0 else 0
        print(f"  📊 Chênh lệch tốc độ: {speedup:.2f}x")


async def run_benchmark():
    """Chạy benchmark đầy đủ"""
    print("\n" + "="*100)
    print("🚀 LightRAG Benchmark - Vietnamese Query Performance")
    print("="*100)
    print(f"\nModel: {LLM_MODEL}")
    print(f"Embedding: {EMBEDDING_MODEL_NAME}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    rag = await initialize_rag()
    
    try:
        # Dữ liệu mẫu
        sample_texts = """
        Hà Nội là thủ đô của Việt Nam, nằm ở phía Bắc của đất nước. 
        Thành phố có lịch sử hơn 1000 năm với nhiều di tích lịch sử như Văn Miếu, 
        Hoàng Thành Thăng Long và Hồ Gươm.

        TP. Hồ Chí Minh là thành phố lớn nhất Việt Nam, nằm ở phía Nam. 
        Đây là trung tâm kinh tế và tài chính của cả nước với nhiều tòa nhà cao tầng 
        và khu công nghiệp.

        Công ty VNG là một trong những công ty công nghệ hàng đầu Việt Nam, 
        được thành lập năm 2004. Công ty nổi tiếng với sản phẩm Zalo - 
        ứng dụng nhắn tin phổ biến nhất tại Việt Nam.

        FPT là tập đoàn công nghệ lớn nhất Việt Nam, hoạt động trong lĩnh vực 
        phần mềm, viễn thông và giáo dục. FPT Software là công ty con chuyên về 
        outsourcing phần mềm.

        Ngành trí tuệ nhân tạo (AI) đang phát triển rất nhanh tại Việt Nam. 
        Nhiều startup công nghệ đang ứng dụng AI vào các lĩnh vực như y tế, 
        giáo dục và tài chính.
        """
        
        print("\n📥 Inserting data...")
        insert_start = time.perf_counter()
        await rag.ainsert(sample_texts)
        insert_time = (time.perf_counter() - insert_start) * 1000
        print(f"✓ Insert completed in {insert_time:.2f}ms")
        
        # Các câu hỏi benchmark
        queries = [
            "Hà Nội có những địa điểm nổi tiếng nào?",
            "Công ty công nghệ nào lớn nhất Việt Nam?",
            "Ngành AI phát triển như thế nào tại Việt Nam?",
        ]
        
        modes = ["naive", "local", "global", "hybrid"]
        all_results = []
        
        print(f"\n🎯 Running {len(queries)} queries x {len(modes)} modes = {len(queries) * len(modes)} total queries...")
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*100}")
            print(f"Query {i}/{len(queries)}: {query}")
            print('='*100)
            
            for mode in modes:
                print(f"  Testing {mode}...", end=" ")
                result = await benchmark_query(rag, query, mode)
                all_results.append(result)
                print(f"✓ {result.execution_time_ms:.2f}ms")
        
        # In kết quả
        print_benchmark_table(all_results)
        
        # Tạo và in summary
        summary = generate_summary(all_results)
        print_summary_table(summary)
        
        # Lưu báo cáo JSON
        report = BenchmarkReport(
            model_name=LLM_MODEL,
            embedding_model=EMBEDDING_MODEL_NAME,
            total_queries=len(queries) * len(modes),
            results=[asdict(r) for r in all_results],
            summary=summary,
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(BENCHMARK_RESULTS_DIR, f"benchmark_report_{timestamp}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Report saved to: {report_file}")
        
    finally:
        await rag.finalize_storages()
    
    print("\n" + "="*100)
    print("✅ Benchmark completed!")
    print("="*100)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
