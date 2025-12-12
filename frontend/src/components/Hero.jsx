import React from "react";

const Hero = () => {
  return (
    <section className="hero">
      <div className="hero-content">
        <h1 className="hero-title">
          <span className="gradient-text">AI-Powered</span>
          <br />
          Plagiarism Detection
        </h1>
        <p className="hero-description">
          Advanced semantic analysis powered by machine learning. Upload
          documents or paste text to detect plagiarism instantly with unmatched
          accuracy.
        </p>
        <div className="hero-stats">
          <div className="stat-item">
            <div className="stat-number">99.9%</div>
            <div className="stat-label">Accuracy</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">&lt;30s</div>
            <div className="stat-label">Analysis Time</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">∞</div>
            <div className="stat-label">Sources Checked</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
