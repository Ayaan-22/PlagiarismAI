import React, { useState, useEffect } from "react";

const Header = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [statusText, setStatusText] = useState("Checking...");

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const API_BASE_URL =
          import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:9002";
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
          setIsConnected(true);
          setStatusText("Online");
        } else {
          setIsConnected(false);
          setStatusText("Offline");
        }
      } catch (error) {
        setIsConnected(false);
        setStatusText("Offline");
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="header">
      <div className="logo">
        <svg
          width="40"
          height="40"
          viewBox="0 0 40 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect width="40" height="40" rx="12" fill="url(#logo-gradient)" />
          <path
            d="M20 10L28 16V24L20 30L12 24V16L20 10Z"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle cx="20" cy="20" r="4" fill="white" />
          <defs>
            <linearGradient id="logo-gradient" x1="0" y1="0" x2="40" y2="40">
              <stop offset="0%" stopColor="#8B5CF6" />
              <stop offset="100%" stopColor="#06B6D4" />
            </linearGradient>
          </defs>
        </svg>
        <span className="logo-text">PlagiarismAI</span>
      </div>
      <nav className="nav">
        <a href="#features" className="nav-link">
          Features
        </a>
        <a href="#how-it-works" className="nav-link">
          How It Works
        </a>
        <a href="#about" className="nav-link">
          About
        </a>
        <div
          className={`connection-status ${
            isConnected ? "connected" : "disconnected"
          }`}
          id="connection-status"
        >
          <div className="status-dot"></div>
          <span className="status-text">{statusText}</span>
        </div>
      </nav>
    </header>
  );
};

export default Header;
