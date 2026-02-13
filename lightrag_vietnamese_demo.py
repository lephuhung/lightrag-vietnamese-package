"""
LightRAG Demo với Local LLM (OpenAI API compatible) và Vietnamese Embedding

Cấu hình:
- LLM: Qwen3-Coder-30B-A3B-Instruct tại http://10.8.0.8:8000/v1
- Embedding: dangvantuan/vietnamese-embedding (HuggingFace)

Yêu cầu:
pip install lightrag-hku sentence-transformers transformers

Cách chạy:
1. Chạy trực tiếp (model mặc định đã được cấu hình):
   python lightrag_vietnamese_demo.py

2. Hoặc ghi đè model qua environment variable:
   export LLM_MODEL="other-model-name"
   python lightrag_vietnamese_demo.py
"""

import os
import asyncio
import numpy as np
from typing import Literal, cast
from openai import AsyncOpenAI
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache
from lightrag.utils import wrap_embedding_func_with_attrs, setup_logger
from sentence_transformers import SentenceTransformer

# Cấu hình logging
setup_logger("lightrag", level="INFO")

# Thư mục làm việc
WORKING_DIR = "./lightrag_vietnamese_storage"

# Tạo thư mục nếu chưa tồn tại
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

# ============================================
# Cấu hình Local LLM (OpenAI API compatible)
# ============================================
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://10.8.0.8:8000/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "not-needed")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen3-Coder-30B-A3B-Instruct")

# Khởi tạo OpenAI client để kiểm tra models
openai_client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)


async def get_available_models():
    """Lấy danh sách models có sẵn từ API"""
    try:
        models = await openai_client.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        print(f"Không thể lấy danh sách models: {e}")
        return []


async def setup_model():
    """Thiết lập model name từ environment hoặc auto-detect"""
    global LLM_MODEL
    
    if not LLM_MODEL:
        print("LLM_MODEL chưa được cấu hình. Đang kiểm tra models có sẵn...")
        models = await get_available_models()
        
        if not models:
            raise ValueError(
                "Không thể kết nối đến API hoặc không có models nào. "
                "Vui lòng cấu hình LLM_MODEL environment variable "
                "hoặc đảm bảo API local đang chạy tại " + LLM_BASE_URL
            )
        
        print(f"Các models có sẵn: {models}")
        
        # Ưu tiên chọn model phổ biến cho tiếng Việt
        preferred_models = [
            "qwen", "llama", "gemma", "mistral", "mixtral",
            "vicuna", "wizardlm", "phind", "openchat"
        ]
        
        for preferred in preferred_models:
            for model in models:
                if preferred.lower() in model.lower():
                    LLM_MODEL = model
                    print(f"✓ Auto-selected model: {LLM_MODEL}")
                    return
        
        # Nếu không tìm thấy preferred, chọn model đầu tiên
        LLM_MODEL = models[0]
        print(f"✓ Selected first available model: {LLM_MODEL}")
    else:
        print(f"✓ Using configured model: {LLM_MODEL}")

# ============================================
# Cấu hình Vietnamese Embedding
# ============================================
EMBEDDING_MODEL_NAME = "dangvantuan/vietnamese-embedding"
EMBEDDING_DIM = 768  # Kích thước vector embedding của model này

# Load model embedding tiếng Việt một lần
print(f"Đang tải model embedding: {EMBEDDING_MODEL_NAME}...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
print(f"✓ Model embedding đã tải xong!")


async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    """
    Hàm gọi Local LLM qua OpenAI API
    """
    return await openai_complete_if_cache(
        LLM_MODEL,
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        **kwargs,
    )


async def vietnamese_embedding_func(texts: list[str]) -> np.ndarray:
    """
    Hàm tạo embedding tiếng Việt sử dụng sentence-transformers
    """
    # SentenceTransformer trả về numpy array với shape (batch_size, embedding_dim)
    embeddings = embedding_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings


# Wrap embedding function với metadata
@wrap_embedding_func_with_attrs(
    embedding_dim=EMBEDDING_DIM,
    max_token_size=512,
    model_name=EMBEDDING_MODEL_NAME
)
async def embedding_func(texts: list[str]) -> np.ndarray:
    return await vietnamese_embedding_func(texts)


async def initialize_rag():
    """Khởi tạo LightRAG instance"""
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        llm_model_name=LLM_MODEL,
        embedding_func=embedding_func,
        # Tùy chọn: cấu hình ngôn ngữ và entity types
        addon_params={
            "language": "Vietnamese",  # Ngôn ngữ cho entity/relation extraction
            "entity_types": ["organization", "person", "location", "event", "product"],
        },
    )
    
    # QUAN TRỌNG: Khởi tạo storage
    await rag.initialize_storages()
    return rag


async def test_embedding():
    """Test hàm embedding"""
    print("\n" + "="*60)
    print("TEST EMBEDDING FUNCTION")
    print("="*60)
    
    test_texts = [
        "Xin chào Việt Nam",
        "Công nghệ trí tuệ nhân tạo đang phát triển mạnh mẽ",
        "Hà Nội là thủ đô của Việt Nam"
    ]
    
    embeddings = await vietnamese_embedding_func(test_texts)
    print(f"✓ Số lượng texts: {len(test_texts)}")
    print(f"✓ Shape embeddings: {embeddings.shape}")
    print(f"✓ Embedding dimension: {embeddings.shape[1]}")
    
    return embeddings.shape[1]


async def demo_insert_and_query():
    """Demo insert và query dữ liệu tiếng Việt"""
    
    print("\n" + "="*60)
    print("DEMO INSERT & QUERY")
    print("="*60)
    
    # Khởi tạo RAG
    rag = await initialize_rag()
    
    try:
        # Văn bản mẫu tiếng Việt
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
        
        print("\nĐang insert dữ liệu...")
        await rag.ainsert(sample_texts)
        print("✓ Insert hoàn tất!")
        
        # Test các mode query khác nhau
        queries = [
            "Hà Nội có những địa điểm nổi tiếng nào?",
            "Công ty công nghệ nào lớn nhất Việt Nam?",
            "Ngành AI phát triển như thế nào tại Việt Nam?",
        ]
        
        modes = ["naive", "local", "global", "hybrid"]
        
        for query in queries:
            print(f"\n{'='*60}")
            print(f"Câu hỏi: {query}")
            print('='*60)
            
            for mode in modes:
                mode_literal = cast(Literal["naive", "local", "global", "hybrid"], mode)
                print(f"\n--- Query mode: {mode} ---")
                try:
                    resp = await rag.aquery(
                        query,
                        param=QueryParam(mode=mode_literal, stream=False)
                    )
                    if hasattr(resp, '__iter__') and not isinstance(resp, str):
                        async for chunk in resp:
                            print(chunk, end="", flush=True)
                    else:
                        resp_str = str(resp)
                        print(resp_str[:500] + "..." if len(resp_str) > 500 else resp_str)
                except Exception as e:
                    print(f"Lỗi trong mode {mode}: {e}")
                    
    finally:
        # Đóng storage
        await rag.finalize_storages()


async def main():
    """Hàm chính"""
    print("\n" + "="*60)
    print("LightRAG Demo với Local LLM và Vietnamese Embedding")
    print("="*60)

    # Setup model trước
    await setup_model()

    print(f"\nCấu hình:")
    print(f"  - LLM API: {LLM_BASE_URL}")
    print(f"  - LLM Model: {LLM_MODEL}")
    print(f"  - Embedding: {EMBEDDING_MODEL_NAME}")
    print(f"  - Embedding Dim: {EMBEDDING_DIM}")
    print(f"  - Working Dir: {WORKING_DIR}")

    # Test embedding trước
    await test_embedding()

    # Demo insert và query
    await demo_insert_and_query()

    print("\n" + "="*60)
    print("Demo hoàn tất!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
