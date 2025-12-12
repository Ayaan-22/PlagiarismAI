import React from "react";

const HowItWorks = () => {
  return (
    <section className="how-it-works-section" id="how-it-works">
      <h2 className="section-title">How It Works</h2>
      <p className="section-description">
        Simple steps to ensure your content is original
      </p>
      <div className="steps-container">
        <div className="step-item">
          <div className="step-number">1</div>
          <h3 className="step-title">Upload</h3>
          <p className="step-text">
            Upload your file or paste your text into the checker.
          </p>
        </div>
        <div className="step-line"></div>
        <div className="step-item">
          <div className="step-number">2</div>
          <h3 className="step-title">Analyze</h3>
          <p className="step-text">
            Our AI scans your content against our massive database.
          </p>
        </div>
        <div className="step-line"></div>
        <div className="step-item">
          <div className="step-number">3</div>
          <h3 className="step-title">Result</h3>
          <p className="step-text">
            Get a detailed report with similarity score and sources.
          </p>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
