# 🚀 Deployment Guide

This guide explains how to deploy the secure, production-ready Plagiarism Checker to a live environment. We recommend using **Render** as it offers free tiers for both web services (backend) and static sites (frontend).

## Option 1: Deploying on Render (Recommended)

### Part 1: Deploy the Backend

1. **Push your code to GitHub**: Ensure your project is in a GitHub repository.
2. **Sign up/Login to Render**: Go to [render.com](https://render.com/).
3. **Create a New Web Service**:
   - Click **New +** -> **Web Service**.
   - Connect your GitHub repository.
4. **Configure the Service**:
   - **Name**: `plagiarism-checker-backend`
   - **Region**: Choose the one closest to you.
   - **Branch**: `main`
   - **Root Directory**: `backend` (Important! This tells Render where your Python code lives)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables**:
   - Scroll down to "Environment Variables".
   - Add Key: `SERPAPI_KEY` | Value: `Your_Actual_SerpAPI_Key`
   - Add Key: `API_KEYS` | Value: `your-secure-api-key-1,your-secure-api-key-2` (Generate strong random strings for this)
   - Add Key: `ALLOWED_ORIGINS` | Value: `https://your-frontend-domain.onrender.com` (You will update this *after* Part 2)
   - Add Key: `PYTHON_VERSION` | Value: `3.9.0`
6. **Deploy**: Click **Create Web Service**.
7. **Copy the URL**: Once live, copy your backend URL (e.g., `https://plagiarism-checker-backend.onrender.com`).

### Part 2: Configure and Deploy the Frontend

1. **Configure API URL**:
   - Navigate to the `frontend` directory locally.
   - Copy `.env.example` to `.env` if it doesn't exist.
   - Update the `.env` file with your deployed backend URL and the API key you chose:

     ```env
     VITE_API_BASE_URL=https://plagiarism-checker-backend.onrender.com
     VITE_API_KEY=your-secure-api-key-1
     ```

2. **Create a New Static Site on Render**:
   - Click **New +** -> **Static Site**.
   - Connect the same GitHub repository.
3. **Configure the Site**:
   - **Name**: `plagiarism-checker-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Publish Directory**: `dist`
4. **Environment Variables** (Important!):
   - Scroll down to "Environment Variables"
   - Add Key: `VITE_API_BASE_URL` | Value: `https://plagiarism-checker-backend.onrender.com`
   - Add Key: `VITE_API_KEY` | Value: `your-secure-api-key-1`
5. **Deploy**: Click **Create Static Site**.
6. **Update Backend CORS**: Copy your new frontend URL (e.g. `https://plagiarism-checker-frontend.onrender.com`). Go back to your Backend Web Service settings on Render, and update the `ALLOWED_ORIGINS` environment variable to match this exact URL. Restart the backend.
7. **Done!**: Visit your secure frontend URL.

---

## Option 2: Docker (For advanced users)

You can containerize the backend to run it anywhere (AWS, DigitalOcean, Azure).

1. **Create a `Dockerfile`** in the `backend/` directory:

   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
   ```

2. **Build and Run**:

   ```bash
   cd backend
   docker build -t plagiarism-backend .
   docker run -p 80:80 \
     -e SERPAPI_KEY=your_key \
     -e API_KEYS=your_secure_api_key \
     -e ALLOWED_ORIGINS=http://localhost:5173 \
     plagiarism-backend
   ```

---

## ⚠️ Important Production Notes

- **API Keys**: Ensure your `API_KEYS` are complex and secure. They are required for every API request to prevent unauthorized usage of your backend and SerpAPI quota.
- **CORS Restriction**: The `ALLOWED_ORIGINS` variable is strictly enforced. The backend will reject requests from any frontend domain not explicitly listed. Do not use wildcards (`*`) in production.
- **SerpAPI Limits**: The free tier of SerpAPI has usage limits. Rate limiting is implemented in the backend via `slowapi` to help prevent accidental abuse.
- **Cold Starts**: On Render's free tier, the backend may go to sleep after inactivity. The first request might take 30-50 seconds to wake it up.
