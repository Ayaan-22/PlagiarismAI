import React from "react";

const About = () => {
  return (
    <section className="about-section" id="about">
      <div className="glass-card about-card">
        <div className="about-content">
          <h2
            className="section-title"
            style={{ textAlign: "left", marginBottom: "1rem" }}
          >
            About PlagiarismAI
          </h2>
          <p className="about-text">
            PlagiarismAI is dedicated to promoting academic integrity and
            original content creation. Our state-of-the-art technology helps
            students, educators, and content creators ensure their work is
            unique and properly cited.
          </p>
          <p className="about-text">
            Built with the latest advancements in Natural Language Processing
            and Machine Learning, we provide fast, accurate, and reliable
            plagiarism detection.
          </p>
        </div>
        <div className="about-image">
          <div className="about-visual">
            <div className="visual-circle"></div>
            <div className="visual-circle"></div>
            <div className="visual-icon">
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
