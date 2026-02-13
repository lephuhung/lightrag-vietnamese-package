#!/usr/bin/env python3
"""
Vietnamese Embedding Service for LightRAG Server - GPU
"""

import torch
import numpy as np
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn

MODEL_NAME = "dangvantuan/vietnamese-embedding"
EMBEDDING_DIM = 768
MAX_TOKENS = 200  # Giới hạn an toàn cho model (model có max 258)
HOST = "0.0.0.0"
PORT = 8001

print(f"Loading model: {MODEL_NAME}...")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"  Device: {device}")

model = SentenceTransformer(MODEL_NAME, device=device)
# Không set max_seq_length để tránh xung đột

print(f"✓ Model loaded on {device}")
print(f"  Dimension: {EMBEDDING_DIM}")

app = FastAPI(title="Vietnamese Embedding Service", version="1.4.0")

class EmbeddingRequest(BaseModel):
    input: str | List[str]
    model: str = "vietnamese-embedding"

def truncate_text(text: str) -> str:
    """Truncate text to MAX_TOKENS"""
    try:
        tokens = model.tokenizer.encode(text, add_special_tokens=True, max_length=MAX_TOKENS, truncation=True)
        return model.tokenizer.decode(tokens, skip_special_tokens=True)
    except:
        # Fallback
        return text[:MAX_TOKENS*4] if len(text) > MAX_TOKENS*4 else text

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{
            "id": "vietnamese-embedding",
            "object": "model",
            "created": 1700000000,
            "owned_by": "local",
            "root": MODEL_NAME,
        }]
    }

@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    try:
        texts = [request.input] if isinstance(request.input, str) else request.input
        if not texts:
            raise HTTPException(status_code=400, detail="Empty input")
        
        # Truncate
        truncated = [truncate_text(t) for t in texts]
        
        # Encode
        embeddings = model.encode(
            truncated, batch_size=8, convert_to_numpy=True,
            normalize_embeddings=True, show_progress_bar=False
        )
        
        data = [{"object": "embedding", "index": i, "embedding": emb.tolist()} 
                for i, emb in enumerate(embeddings)]
        
        return {
            "object": "list",
            "data": data,
            "model": request.model or "vietnamese-embedding",
            "usage": {"prompt_tokens": sum(len(t.split()) for t in texts), "total_tokens": sum(len(t.split()) for t in texts)}
        }
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "dimensions": EMBEDDING_DIM,
        "device": device,
        "max_tokens": MAX_TOKENS,
        "gpu": torch.cuda.is_available()
    }

if __name__ == "__main__":
    print(f"\nStarting server on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
