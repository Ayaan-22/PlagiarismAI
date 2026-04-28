import asyncio
from typing import Tuple, Optional
from sentence_transformers import SentenceTransformer, util

from config import CHUNK_SIZE, MAX_PAGE_CHUNKS_PER_SOURCE, MIN_PAGE_CHUNK_LENGTH, EMBEDDING_MAX_CONCURRENCY
from services.text_extraction import chunk_text

model: Optional[SentenceTransformer] = None
embedding_semaphore = asyncio.Semaphore(EMBEDDING_MAX_CONCURRENCY)

def load_model():
    global model
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def compute_best_similarity(chunk: str, page_text: str) -> Tuple[float, str]:
    if not model:
        raise RuntimeError("Model not loaded")
        
    if not page_text or len(page_text) < 100:
        return 0.0, ""

    page_chunks = chunk_text(page_text, size=CHUNK_SIZE)
    if not page_chunks:
        return 0.0, ""

    page_chunks = page_chunks[:MAX_PAGE_CHUNKS_PER_SOURCE]

    chunk_emb = model.encode(chunk, convert_to_tensor=True)
    page_embs = model.encode(page_chunks, convert_to_tensor=True)

    similarities = util.pytorch_cos_sim(chunk_emb, page_embs)[0] * 100.0
    similarities_list = similarities.tolist()

    max_similarity = 0.0
    best_match_chunk = ""

    for idx, page_chunk in enumerate(page_chunks):
        if len(page_chunk.strip()) < MIN_PAGE_CHUNK_LENGTH:
            continue

        sim = similarities_list[idx]
        if sim > max_similarity:
            max_similarity = sim
            best_match_chunk = page_chunk

    return round(max_similarity, 2), best_match_chunk

async def compute_best_similarity_async(chunk: str, page_text: str) -> Tuple[float, str]:
    loop = asyncio.get_running_loop()
    async with embedding_semaphore:
        # Wrap inference in a timeout (30 seconds) to prevent hanging
        return await asyncio.wait_for(
            loop.run_in_executor(None, compute_best_similarity, chunk, page_text),
            timeout=30.0
        )
