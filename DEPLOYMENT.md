# 🚀 Deployment Guide

This guide explains how to deploy the Plagiarism Checker to a live environment. We recommend using **Render** as it offers free tiers for both web services (backend) and static sites (frontend), and it's very easy to set up.

## Option 1: Deploying on Render (Recommended)

### Part 1: Deploy the Backend

1.  **Push your code to GitHub**: Ensure your project is in a public or private GitHub repository.
2.  **Sign up/Login to Render**: Go to [render.com](https://render.com/).
3.  **Create a New Web Service**:
    - Click **New +** -> **Web Service**.
    - Connect your GitHub repository.
4.  **Configure the Service**:
    - **Name**: `plagiarism-checker-backend` (or similar)
    - **Region**: Choose the one closest to you.
    - **Branch**: `main` (or your working branch)
    - **Root Directory**: `backend` (Important! This tells Render where your python code lives)
    - **Runtime**: `Python 3`
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5.  **Environment Variables**:
    - Scroll down to "Environment Variables".
    - Add Key: `SERPAPI_KEY`
    - Value: `Your_Actual_SerpAPI_Key`
    - Add Key: `PYTHON_VERSION`
    - Value: `3.9.0` (or your local version)
6.  **Deploy**: Click **Create Web Service**. Render will build and start your backend.
7.  **Copy the URL**: Once live, copy your backend URL (e.g., `https://plagiarism-checker-backend.onrender.com`).

### Part 2: Configure and Deploy the Frontend

1.  **Update API URL**:

    - Open `frontend/script.js`.
    - Find `const API_URL` and `const HEALTH_CHECK_URL`.
    - Replace `http://127.0.0.1:9001` with your **new Backend URL** from Part 1.
      - Example: `const API_URL = "https://plagiarism-checker-backend.onrender.com/check";`
    - Commit and push this change to GitHub.

2.  **Create a New Static Site on Render**:
    - Click **New +** -> **Static Site**.
    - Connect the same GitHub repository.
3.  **Configure the Site**:
    - **Name**: `plagiarism-checker-frontend`
    - **Root Directory**: `frontend`
    - **Build Command**: (Leave empty, we are just serving HTML/JS)
    - **Publish Directory**: `.` (dot) or leave empty to serve the root of `frontend`.
4.  **Deploy**: Click **Create Static Site**.
5.  **Done!**: Visit your new frontend URL.

---

## Option 2: Docker (For advanced users)

You can containerize the backend to run it anywhere (AWS, DigitalOcean, Azure).

1.  **Create a `Dockerfile`** in the `backend/` directory:

    ```dockerfile
    FROM python:3.9-slim

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
    ```

2.  **Build and Run**:
    ```bash
    cd backend
    docker build -t plagiarism-backend .
    docker run -p 80:80 -e SERPAPI_KEY=your_key plagiarism-backend
    ```

---

## ⚠️ Important Notes

- **CORS**: The current backend is configured to allow all origins (`allow_origins=["*"]`). For a production app, you should restrict this to your specific frontend domain in `backend/main.py` for better security.
- **SerpAPI Limits**: Remember that the free tier of SerpAPI has usage limits.
- **Cold Starts**: On Render's free tier, the backend may go to sleep after inactivity. The first request might take 30-50 seconds to wake it up. The frontend's "Checking..." status indicator handles this gracefully.
