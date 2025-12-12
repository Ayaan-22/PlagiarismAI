import React, { useEffect, useState } from "react";

const LoadingOverlay = ({ isLoading }) => {
  const [progress, setProgress] = useState(0);
  const [sources, setSources] = useState(0);
  const [chunks, setChunks] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (isLoading) {
      setVisible(true);
      setProgress(0);
      setSources(0);
      setChunks(0);

      const interval = setInterval(() => {
        setProgress((prev) => {
          const next = prev + Math.random() * 15;
          return next > 90 ? 90 : next;
        });
        setSources((prev) => prev + Math.floor(Math.random() * 50));
        setChunks((prev) => prev + Math.floor(Math.random() * 5));
      }, 500);

      return () => clearInterval(interval);
    } else {
      if (visible) {
        setProgress(100);
        const timeout = setTimeout(() => {
          setVisible(false);
        }, 500);
        return () => clearTimeout(timeout);
      }
    }
  }, [isLoading]);

  if (!visible) return null;

  return (
    <div className="loading-overlay" style={{ display: "flex" }}>
      <div className="loading-card glass-card">
        <div className="loading-spinner"></div>
        <h3 className="loading-title">Analyzing Your Content</h3>
        <p className="loading-subtitle">
          Our AI is scanning millions of sources...
        </p>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="loading-stats">
          <div className="loading-stat">
            <span className="stat-value">{sources}</span>
            <span className="stat-label">Sources Checked</span>
          </div>
          <div className="loading-stat">
            <span className="stat-value">{chunks}</span>
            <span className="stat-label">Chunks Analyzed</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingOverlay;
