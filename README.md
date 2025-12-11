# 🧠 AI Plagiarism Checker

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

A premium, high-accuracy plagiarism detection tool powered by advanced AI and semantic analysis. This application compares your text or PDF documents against millions of online sources to detect plagiarism with high precision while intelligently recognizing proper citations.

## ✨ Features

- **🚀 Advanced AI Detection**: Uses `SentenceTransformer` (paraphrase-multilingual-MiniLM-L12-v2) for semantic similarity checking, supporting 50+ languages.
- **🎓 Smart Citation Detection**:
  - Automatically identifies academic citations (APA, MLA, IEEE, Chicago, etc.).
  - **Excludes cited content** from plagiarism scores.
  - Provides specific recommendations (e.g., "Add citation" vs. "Rewrite").
- **🔄 Flexible Scan Modes**:
  - **Quick Scan**: Fast analysis of up to 15 chunks (~10,500 chars).
  - **Deep Scan**: Comprehensive analysis of the entire document.
- **📂 Multi-Format Support**: Drag and drop PDF, DOCX, or TXT files for instant analysis.
- **⚡ Production-Ready Performance**:
  - Async/await processing for 10x faster analysis.
  - Parallel chunk processing with concurrency control.
  - Smart deduplication and filtering (>30% similarity threshold).
- **🎨 Premium UI**:
  - Glassmorphism design with vibrant gradients.
  - Dark mode with animated background.
  - **Real-time connection indicator** to check backend status.
  - **Citation Badges** & Status Labels.
  - **Confetti Celebration** for high originality scores!
- **📊 Detailed Reporting**:
  - Visual plagiarism score ring.
  - Breakdown of **Cited Chunks** vs. **Plagiarized Matches**.
  - **Client-side PDF & TXT Reports** generation (via jsPDF).

## ⚙️ How it Works

1.  **Input Processing**:

    - The backend accepts **PDF, DOCX, or TXT** files (or raw text).
    - It extracts text using `PyPDF2`, `python-docx`, or standard decoding.
    - The text is split into fixed-size **chunks** (default ~700 chars) to ensure granular analysis.

2.  **Citation Analysis**:

    - Before checking for plagiarism, each chunk is scanned for **citations** using regex patterns (APA, MLA, IEEE, etc.).
    - If a valid citation is found, the chunk is marked as **"Properly Cited"** and excluded from the plagiarism score.

3.  **Smart Search (SerpAPI)**:

    - Uncited chunks are sent to **Google Search** via SerpAPI to find potential source matches.
    - The system fetches the content of the top search results using **browser-mimicking headers** and **robust compression handling** (Brotli) to bypass common scraping blocks.

4.  **Semantic Comparison**:

    - The user's text and the fetched source text are converted into vector embeddings using `SentenceTransformer` (**paraphrase-multilingual-MiniLM-L12-v2**).
    - Cosine similarity is calculated to determine how closely the texts match, even if words are paraphrased.

5.  **Scoring & Reporting**:
    - **Plagiarism Score** = (Plagiarized Chunks / Total Chunks) \* 100.
    - Matches are categorized as **High Risk** (>60% similarity) or **Potential Plagiarism** (>30% similarity).
    - The frontend displays these results with clear visual indicators.

## 🛠️ Tech Stack

### Backend

- **FastAPI**: High-performance async web framework.
- **Sentence Transformers**: State-of-the-art multilingual model for embeddings.
- **PyPDF2 & python-docx**: Document parsing.
- **aiohttp**: Async HTTP client for parallel web requests.
- **SerpAPI**: Leveraged via direct async API calls for robust web searching.
- **BeautifulSoup4**: HTML cleaning and text extraction.
- **python-multipart**: For handling file uploads in FastAPI.
- **langdetect**: Auto-detects input language for optimized search.
- **brotli**: Handles compressed responses from web servers.

### Frontend

- **HTML5 & CSS3**: Semantic structure with modern CSS variables, animations, and glassmorphism.
- **JavaScript (ES6+)**: Vanilla JS for seamless interactions.
- **jsPDF**: Client-side PDF report generation.
- **Inter Font**: Clean, modern typography.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- A [SerpAPI](https://serpapi.com/) API Key (for web search functionality).

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Ayaan-22/PlagiarismAI.git
   cd plagiarism-checker
   ```

2. **Backend Setup**
   Navigate to the backend directory and install dependencies:

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   Create a `.env` file in the `backend` directory and add your SerpAPI key:
   ```env
   SERPAPI_KEY=your_serpapi_key_here
   ```

### Running the Application

1. **Start the Backend Server**

   ```bash
   cd backend
   python main.py
   ```

   The server will start at `http://127.0.0.1:9002`.

2. **Launch the Frontend**
   Simply open the `frontend/index.html` file in your web browser.

   _Tip: You can just double-click the file or drag it into Chrome/Edge/Firefox._

## 📖 Usage Guide

1. **Check Connection**: Look at the top-right corner for the connection status indicator (🟢 Green = Connected).
2. **Select Input Method**: Choose "Upload File" or "Paste Text".
3. **Choose Scan Mode**:
   - **Quick Scan**: Good for quick checks.
   - **Deep Scan**: Thorough analysis for final submissions.
4. **Analyze**: Click **Analyze Content**.
5. **View Results**:
   - **Plagiarism Score**: Percentage of content that matches external sources (excluding citations).
   - **Cited Chunks**: See which parts were correctly cited.
   - **Matches**: Review specific matches with similarity scores and recommendations.
   - **Download Report**: Save a text summary of the analysis.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🚀 Deployment

Want to take this project live? Check out our detailed [Deployment Guide](DEPLOYMENT.md) for step-by-step instructions on how to deploy to Render (Free Tier) or use Docker.

## 📄 License

This project is licensed under the MIT License.
