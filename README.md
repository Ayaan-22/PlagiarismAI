# 🧠 AI Plagiarism Checker

A premium, high-accuracy plagiarism detection tool powered by advanced AI and semantic analysis. This application compares your text or PDF documents against millions of online sources to detect plagiarism with high precision while intelligently recognizing proper citations.

## ✨ Features

- **🚀 Advanced AI Detection**: Uses `SentenceTransformer` (paraphrase-multilingual-MiniLM-L12-v2) for semantic similarity checking, supporting 50+ languages.
- **🎓 Smart Citation Detection**:
  - Automatically identifies academic citations (APA, MLA, IEEE, Chicago, etc.).
  - **Excludes cited content** from plagiarism scores.
  - Provides specific recommendations (e.g., "Add citation" vs. "Rewrite").
- **� Flexible Scan Modes**:
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
  - **Real-time connection indicator**.
  - **Citation Badges** & Status Labels.
- **📊 Detailed Reporting**:
  - Visual plagiarism score ring.
  - Breakdown of **Cited Chunks** vs. **Plagiarized Matches**.
  - Downloadable analysis reports.

## 🛠️ Tech Stack

### Backend

- **FastAPI**: High-performance async web framework.
- **Sentence Transformers**: State-of-the-art multilingual model for embeddings.
- **PyPDF2 & python-docx**: Document parsing.
- **aiohttp**: Async HTTP client for parallel web requests.
- **SerpAPI**: For searching the web for matching content.
- **BeautifulSoup4**: HTML cleaning and text extraction.

### Frontend

- **HTML5 & CSS3**: Semantic structure with modern CSS variables and animations.
- **JavaScript (ES6+)**: Vanilla JS for seamless interactions.
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

   The server will start at `http://127.0.0.1:9001`.

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

## 📄 License

This project is licensed under the MIT License.
