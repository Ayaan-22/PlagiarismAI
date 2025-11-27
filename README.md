# 🧠 AI Plagiarism Checker

A premium, high-accuracy plagiarism detection tool powered by advanced AI and semantic analysis. This application compares your text or PDF documents against millions of online sources to detect plagiarism with high precision.

## ✨ Features

- **🚀 Advanced AI Detection**: Uses `SentenceTransformer` (paraphrase-multilingual-MiniLM-L12-v2) for semantic similarity checking, supporting 50+ languages.
- **📂 Multi-Format Support**: Drag and drop PDF, DOCX, or TXT files for instant analysis.
- **📝 Text Analysis**: Paste text directly to check for plagiarism.
- **⚡ Production-Ready Performance**:
  - Async/await processing for 10x faster analysis
  - Parallel chunk processing with concurrency control
  - Analyzes up to 15 chunks (~10,500 characters)
  - Smart deduplication and filtering (>30% similarity threshold)
- **🎨 Premium UI**:
  - Glassmorphism design with vibrant gradients.
  - Dark mode with animated background.
  - Fully responsive layout for all devices.
  - **Real-time connection indicator** - Shows backend status
- **📊 Real-time Results**:
  - Visual plagiarism score ring.
  - Detailed match breakdown with source links.
  - Accurate chunk-to-chunk similarity matching.
  - **Downloadable Reports**: Save your analysis as a text file.

## 🛠️ Tech Stack

### Backend

- **FastAPI**: High-performance async web framework for building APIs.
- **Sentence Transformers**: State-of-the-art multilingual model for generating sentence embeddings.
- **PyPDF2 & python-docx**: For extracting text from PDF and DOCX documents.
- **aiohttp**: Async HTTP client for parallel web requests.
- **SerpAPI**: For searching the web for matching content.

### Frontend

- **HTML5 & CSS3**: Semantic structure with modern CSS variables and animations.
- **JavaScript (ES6+)**: Vanilla JS for seamless interactions and API integration.
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

1. **Check Connection**: Look at the top-right corner for the connection status indicator:
   - 🟢 Green = Backend connected
   - 🔴 Red = Backend disconnected
2. **Select Input Method**: Choose between "Upload File" or "Paste Text" using the tabs.
3. **Upload/Enter Content**:
   - Drag & drop a PDF, DOCX, or TXT file.
   - Or paste your text into the text area.
4. **Analyze**: Click the **Analyze Content** button.
5. **View Results**:
   - See the overall plagiarism percentage.
   - Review specific matches and their sources with accurate similarity scores.
   - Download the report for your records.
   - Click "New Check" to start over.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
