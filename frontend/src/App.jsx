import React, { useState } from "react";
import Header from "./components/Header";
import Hero from "./components/Hero";
import UploadSection from "./components/UploadSection";
import Features from "./components/Features";
import HowItWorks from "./components/HowItWorks";
import About from "./components/About";
import Results from "./components/Results";
import Footer from "./components/Footer";
import LoadingOverlay from "./components/LoadingOverlay";

// Configuration
// Read API URL from environment variable (defined in .env file)
// For local development: http://127.0.0.1:9002
// For production: https://your-backend.onrender.com
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:9002";
const API_URL = `${API_BASE_URL}/check`;

function App() {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalysis = async (formData) => {
    setIsLoading(true);
    setResults(null);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to analyze content");
      }

      const data = await response.json();
      // Simulate loading delay for better UX if response is too fast
      // (The LoadingOverlay handles min display time but extra safety here)
      setTimeout(() => {
        setResults(data);
        setIsLoading(false);
      }, 1000); // minimal delay for animation
    } catch (error) {
      console.error("Error:", error);
      alert(
        "An error occurred while analyzing your content. Please try again."
      );
      setIsLoading(false);
    }
  };

  const handleNewCheck = () => {
    setResults(null);
    // Scroll to top or checker
    const checker = document.getElementById("checker");
    if (checker) checker.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <>
      {/* Background Animation */}
      <div className="background-animation">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>

      <div className="container">
        <Header />

        {!results && (
          <>
            <Hero />
            <UploadSection onSubmit={handleAnalysis} isLoading={isLoading} />
            <Features />
            <HowItWorks />
            <About />
          </>
        )}

        {results && <Results data={results} onNewCheck={handleNewCheck} />}

        <Footer />
      </div>

      <LoadingOverlay isLoading={isLoading} />

      {/* Confetti Container for direct DOM manipulation from Results component */}
      <div
        id="confetti-container"
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
          zIndex: 9999,
        }}
      ></div>
    </>
  );
}

export default App;
