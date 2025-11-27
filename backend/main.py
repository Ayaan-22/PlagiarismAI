import io
import asyncio
import aiohttp
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer, util
from PyPDF2 import PdfReader
import docx
from dotenv import load_dotenv
import os
from typing import List, Dict

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Switch to multilingual model
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def extract_pdf_text(file_bytes):
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_docx_text(file_bytes):
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])


def extract_txt_text(file_bytes):
    return file_bytes.decode("utf-8", errors="ignore")


def chunk_text(text, size=700):
    """Split text into chunks of specified size"""
    return [text[i:i+size] for i in range(0, len(text), size)]


async def serp_search_async(query: str, session: aiohttp.ClientSession) -> List[str]:
    """Async search using SerpAPI"""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "api_key": SERPAPI_KEY,
        "q": query
    }
    
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
            res = await response.json()
            links = []
            for r in res.get("organic_results", []):
                if "link" in r:
                    links.append(r["link"])
            return links[:3]
    except Exception as e:
        print(f"SerpAPI error: {e}")
        return []


async def fetch_page_async(url: str, session: aiohttp.ClientSession) -> str:
    """Async fetch page content"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""


def compute_best_similarity(chunk: str, page_text: str) -> float:
    """
    Compute the best similarity by comparing the chunk against 
    all chunks of the page and returning the maximum similarity
    """
    if not page_text or len(page_text) < 100:
        return 0.0
    
    # Split page into chunks
    page_chunks = chunk_text(page_text, size=700)
    
    # Encode the input chunk once
    chunk_emb = model.encode(chunk, convert_to_tensor=True)
    
    max_similarity = 0.0
    
    # Compare against each page chunk
    for page_chunk in page_chunks[:20]:  # Limit to first 20 chunks of page for performance
        if len(page_chunk.strip()) < 50:  # Skip very short chunks
            continue
            
        page_emb = model.encode(page_chunk, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(chunk_emb, page_emb)[0].item() * 100
        max_similarity = max(max_similarity, similarity)
    
    return round(max_similarity, 2)


async def process_chunk(chunk: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> List[Dict]:
    """Process a single chunk: search and compare against sources"""
    async with semaphore:
        search_query = chunk[:150]
        urls = await serp_search_async(search_query, session)
        
        chunk_matches = []
        
        for url in urls:
            page_text = await fetch_page_async(url, session)
            if page_text:
                similarity = compute_best_similarity(chunk, page_text)
                
                # Only include matches with significant similarity
                if similarity > 30:
                    chunk_matches.append({
                        "chunk": chunk[:120],
                        "source": url,
                        "similarity": similarity
                    })
        
        return chunk_matches


@app.get("/health")
async def health_check():
    """Health check endpoint for frontend connection status"""
    return {"status": "ok", "message": "Backend is running"}


@app.post("/check")
async def check_plagiarism(text: str = Form(None), file: UploadFile = File(None)):
    
    # File support (PDF, DOCX, TXT)
    if file:
        file_bytes = await file.read()
        filename = file.filename.lower()
        
        if filename.endswith(".pdf"):
            text = extract_pdf_text(file_bytes)
        elif filename.endswith(".docx"):
            text = extract_docx_text(file_bytes)
        elif filename.endswith(".txt"):
            text = extract_txt_text(file_bytes)
        else:
            return {"error": "Unsupported file format. Please upload PDF, DOCX, or TXT."}

    if not text:
        return {"error": "No text provided"}

    # Split text into chunks
    chunks = chunk_text(text)
    
    # Limit to reasonable number for production (adjust based on needs)
    max_chunks = 15
    if len(chunks) > max_chunks:
        chunks = chunks[:max_chunks]
    
    # Create async session and semaphore for concurrency control
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
    
    async with aiohttp.ClientSession() as session:
        # Process all chunks in parallel
        tasks = [process_chunk(chunk, session, semaphore) for chunk in chunks]
        results = await asyncio.gather(*tasks)
    
    # Flatten results
    all_matches = []
    for chunk_matches in results:
        all_matches.extend(chunk_matches)
    
    # Calculate overall plagiarism percentage
    if all_matches:
        total_sim = sum(match["similarity"] for match in all_matches)
        plagiarism_percent = round(total_sim / len(all_matches), 2)
    else:
        plagiarism_percent = 0.0
    
    # Sort matches by similarity (highest first)
    all_matches.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Remove duplicate sources, keeping highest similarity
    seen_sources = set()
    unique_matches = []
    for match in all_matches:
        if match["source"] not in seen_sources:
            seen_sources.add(match["source"])
            unique_matches.append(match)
    
    return {
        "plagiarism_percent": plagiarism_percent,
        "matches": unique_matches[:20]  # Return top 20 matches
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9001)

