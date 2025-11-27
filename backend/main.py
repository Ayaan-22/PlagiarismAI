import io
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer, util
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import os

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

model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_pdf_text(pdf):
    reader = PdfReader(pdf)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def chunk_text(text, size=700):
    return [text[i:i+size] for i in range(0, len(text), size)]


def serp_search(query):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "api_key": SERPAPI_KEY,
        "q": query
    }
    res = requests.get(url, params=params).json()
    
    links = []
    for r in res.get("organic_results", []):
        if "link" in r:
            links.append(r["link"])
    return links[:3]


def compute_similarity(a, b):
    emb1 = model.encode(a, convert_to_tensor=True)
    emb2 = model.encode(b, convert_to_tensor=True)
    return round(util.pytorch_cos_sim(emb1, emb2)[0].item() * 100, 2)


@app.post("/check")
async def check_plagiarism(text: str = Form(None), file: UploadFile = File(None)):

    # PDF support
    if file:
        pdf_bytes = await file.read()
        text = extract_pdf_text(io.BytesIO(pdf_bytes))

    if not text:
        return {"error": "No text provided"}

    chunks = chunk_text(text)
    matches = []
    total_sim = 0
    total_count = 0

    for chunk in chunks:
        search_query = chunk[:150]
        urls = serp_search(search_query)

        for u in urls:
            try:
                page = requests.get(u, timeout=5).text
                similarity = compute_similarity(chunk, page)

                matches.append({
                    "chunk": chunk[:120],
                    "source": u,
                    "similarity": similarity
                })

                total_sim += similarity
                total_count += 1

            except:
                pass

    plagiarism_percent = round(total_sim / max(total_count, 1), 2)

    return {
        "plagiarism_percent": plagiarism_percent,
        "matches": matches
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9001)
