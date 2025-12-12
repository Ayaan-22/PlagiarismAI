# Plagiarism Checker - Frontend

Modern React frontend for the AI-powered plagiarism detection system, built with Vite for optimal performance.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and set your backend API URL:

```env
# For local development
VITE_API_BASE_URL=http://127.0.0.1:9002

# For production (after deploying backend to Render)
# VITE_API_BASE_URL=https://your-backend.onrender.com
```

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## 🔧 Environment Variables

| Variable            | Description          | Example                                                                             |
| ------------------- | -------------------- | ----------------------------------------------------------------------------------- |
| `VITE_API_BASE_URL` | Backend API base URL | `http://127.0.0.1:9002` (local) or `https://your-backend.onrender.com` (production) |

**Important**: In Vite, environment variables must be prefixed with `VITE_` to be exposed to the client-side code.

## 📦 Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

## 🌐 Deployment

See [DEPLOYMENT.md](../DEPLOYMENT.md) in the root directory for detailed deployment instructions to Render or other platforms.

### Quick Deployment Checklist:

1. ✅ Update `.env` with production backend URL
2. ✅ Run `npm run build` to test the build
3. ✅ Deploy to Render Static Site
4. ✅ Set `VITE_API_BASE_URL` environment variable in Render dashboard

## 🛠️ Tech Stack

- **React** - UI library
- **Vite** - Build tool and dev server
- **CSS3** - Styling with glassmorphism effects
- **jsPDF** - PDF report generation

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   │   ├── Header.jsx
│   │   ├── Hero.jsx
│   │   ├── UploadSection.jsx
│   │   ├── Results.jsx
│   │   └── ...
│   ├── App.jsx         # Main app component
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles
├── public/             # Static assets
├── .env.example        # Environment variables template
├── .env                # Your local environment variables (gitignored)
└── vite.config.js      # Vite configuration
```

## 🎨 Features

- Modern glassmorphism UI design
- Real-time backend connection status
- Drag-and-drop file upload
- Text input support
- Animated results display
- PDF and TXT report generation
- Confetti celebration for original content
- Responsive design

## 🔍 Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint

### Code Style

This project uses ESLint for code quality. Run `npm run lint` to check for issues.
