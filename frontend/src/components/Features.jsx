import React from "react";
import { Search, FileType, Languages } from "lucide-react";

const Features = () => {
  return (
    <section className="features-section" id="features">
      <h2 className="section-title">Why Choose PlagiarismAI?</h2>
      <p className="section-description">
        Industry-leading technology for accurate and fast results
      </p>
      <div className="features-grid">
        <div className="feature-card glass-card">
          <div className="feature-icon">
            <Search size={24} />
          </div>
          <h3 className="feature-title">Deep Search</h3>
          <p className="feature-text">
            We scan billions of web pages and academic papers to ensure
            comprehensive coverage.
          </p>
        </div>
        <div className="feature-card glass-card">
          <div className="feature-icon">
            <FileType size={24} />
          </div>
          <h3 className="feature-title">Multi-Format</h3>
          <p className="feature-text">
            Support for PDF, DOCX, TXT, and direct text input for maximum
            flexibility.
          </p>
        </div>
        <div className="feature-card glass-card">
          <div className="feature-icon">
            <Languages size={24} />
          </div>
          <h3 className="feature-title">Multi-Language</h3>
          <p className="feature-text">
            Detect plagiarism in over 50 languages with our advanced linguistic
            models.
          </p>
        </div>
      </div>
    </section>
  );
};

export default Features;
