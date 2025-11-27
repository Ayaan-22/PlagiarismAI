# 🧠 AI Plagiarism Checker

A premium, high-accuracy plagiarism detection tool powered by advanced AI and semantic analysis. This application compares your text or PDF documents against millions of online sources to detect plagiarism with high precision.

## ✨ Features

- **🚀 Advanced AI Detection**: Uses `SentenceTransformer` (all-MiniLM-L6-v2) for semantic similarity checking, going beyond simple keyword matching.
- **📄 PDF Support**: Drag and drop PDF files for instant analysis.
- **📝 Text Analysis**: Paste text directly to check for plagiarism.
- **🎨 Premium UI**:
  - Glassmorphism design with vibrant gradients.
  - Dark mode with animated background.
  - Fully responsive layout for all devices.
- **⚡ Real-time Results**:
  - Visual plagiarism score ring.
  - Detailed match breakdown with source links.
  - Similarity percentage for each match.

## 🛠️ Tech Stack

### Backend

- **FastAPI**: High-performance web framework for building APIs.
- **Sentence Transformers**: State-of-the-art model for generating sentence embeddings.
- **PyPDF2**: For extracting text from PDF documents.
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

1. **Select Input Method**: Choose between "Upload File" or "Paste Text" using the tabs.
2. **Upload/Enter Content**:
   - Drag & drop a PDF file.
   - Or paste your text into the text area.
3. **Analyze**: Click the **Analyze Content** button.
4. **View Results**:
   - See the overall plagiarism percentage.
   - Review specific matches and their sources.
   - Click "New Check" to start over.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
