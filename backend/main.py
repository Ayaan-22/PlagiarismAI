import io
from bs4 import BeautifulSoup
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

async def serp_search_async(query: str, session: aiohttp.ClientSession) -> List[Dict]:
    """Async search using SerpAPI"""
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []
        
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": 10
    }
    
    try:
        async with session.get(url, params=params) as response:
            data = await response.json()
            if "organic_results" in data:
                return [{
                    "url": result.get("link"),
                    "snippet": result.get("snippet", "")
                } for result in data["organic_results"]]
            return []
    except Exception as e:
        print(f"Error searching: {e}")
        return []


async def fetch_page_async(url: str, session: aiohttp.ClientSession) -> str:
    """Async fetch page content, including PDF extraction"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Handle PDF files
            if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
                try:
                    pdf_bytes = await response.read()
                    # Extract text from PDF
                    reader = PdfReader(io.BytesIO(pdf_bytes))
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    return text
                except Exception as pdf_error:
                    print(f"Error extracting PDF from {url}: {pdf_error}")
                    return ""
            
            # Handle regular web pages
            elif 'text/html' in content_type or 'text/plain' in content_type:
                try:
                    html_content = await response.text(errors='ignore')
                    # Clean HTML using BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "meta", "noscript", "header", "footer", "nav"]):
                        script.extract()
                        
                    # Get text
                    text = soup.get_text(separator=' ', strip=True)
                    return text
                    
                except UnicodeDecodeError:
                    # Fallback to latin-1 encoding
                    content = await response.read()
                    html_content = content.decode('latin-1', errors='ignore')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    for script in soup(["script", "style", "meta", "noscript", "header", "footer", "nav"]):
                        script.extract()
                    return soup.get_text(separator=' ', strip=True)
            
            # Skip other binary formats (images, videos, etc.)
            else:
                return ""
                
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""


def compute_best_similarity(chunk: str, page_text: str) -> tuple[float, str]:
    """
    Compute the best similarity by comparing the chunk against 
    all chunks of the page and returning the maximum similarity
    and the best matching chunk
    """
    if not page_text or len(page_text) < 100:
        return 0.0, ""
    
    # Split page into chunks
    page_chunks = chunk_text(page_text, size=700)
    
    # Encode the input chunk once
    chunk_emb = model.encode(chunk, convert_to_tensor=True)
    
    max_similarity = 0.0
    best_match_chunk = ""
    
    # Compare against each page chunk
    for page_chunk in page_chunks[:20]:  # Limit to first 20 chunks of page for performance
        if len(page_chunk.strip()) < 50:  # Skip very short chunks
            continue
            
        page_emb = model.encode(page_chunk, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(chunk_emb, page_emb)[0].item() * 100
        
        if similarity > max_similarity:
            max_similarity = similarity
            best_match_chunk = page_chunk
    
    return round(max_similarity, 2), best_match_chunk


async def process_chunk(chunk: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> List[Dict]:
    """Process a single chunk: search and compare against sources"""
    async with semaphore:
        search_query = chunk[:150]
        search_results = await serp_search_async(search_query, session)
        
        chunk_matches = []
        
        for result in search_results:
            url = result['url']
            snippet = result['snippet']
            
            page_text = await fetch_page_async(url, session)
            
            # If page fetch failed but we have a snippet, use the snippet
            if not page_text and snippet:
                page_text = snippet
                
            if page_text:
                similarity, matched_chunk = compute_best_similarity(chunk, page_text)
                
                # Only include matches with significant similarity
                if similarity > 30:
                    chunk_matches.append({
                        "chunk": chunk,  # Full user chunk
                        "source": url,
                        "similarity": similarity,
                        "matched_content": matched_chunk  # Full matched chunk
                    })
        
        return chunk_matches


@app.get("/health")
async def health_check():
    """Health check endpoint for frontend connection status"""
    return {"status": "ok", "message": "Backend is running"}


@app.post("/check")
async def check_plagiarism(
    text: str = Form(None), 
    file: UploadFile = File(None),
    scan_mode: str = Form("quick")  # "quick" or "deep"
):
    
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
    
    # Apply scan mode
    if scan_mode == "quick":
        # Quick Scan: Limit to 15 chunks (~10,500 characters)
        max_chunks = 15
        if len(chunks) > max_chunks:
            chunks = chunks[:max_chunks]
    # Deep Scan: Analyze all chunks (no limit)
    
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

