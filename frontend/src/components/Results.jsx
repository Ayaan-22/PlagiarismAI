import React, { useEffect, useState } from "react";
import {
  Download,
  Copy,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  FileText,
} from "lucide-react";
import { jsPDF } from "jspdf";

const Results = ({ data, onNewCheck }) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [expandedMatches, setExpandedMatches] = useState({});
  const [copied, setCopied] = useState(false);
  const [scoreOffset, setScoreOffset] = useState(534);

  const { plagiarism_percent, matches, summary } = data;
  const originalityScore = (100 - plagiarism_percent).toFixed(1);
  const sourcesCount = summary ? summary.chunks_with_matches : matches.length;
  const citedCount = summary ? summary.citation_safe_chunks : 0;

  const triggerConfetti = () => {
    const container = document.getElementById("confetti-container");
    if (!container) return;

    const colors = ["#8b5cf6", "#06b6d4", "#ec4899", "#10b981", "#f59e0b"];
    const totalPieces = Math.min(
      60,
      Math.max(25, Math.floor(window.innerWidth / 40))
    );

    for (let i = 0; i < totalPieces; i++) {
      const confetti = document.createElement("div");
      confetti.className = "confetti";
      confetti.style.left = Math.random() * 100 + "vw";
      confetti.style.top = -10 + "px";
      confetti.style.backgroundColor =
        colors[Math.floor(Math.random() * colors.length)];
      confetti.style.animationDuration = Math.random() * 3 + 2 + "s";
      confetti.style.opacity = Math.random();
      confetti.style.transform = `rotate(${Math.random() * 360}deg)`;

      container.appendChild(confetti);

      setTimeout(() => {
        confetti.remove();
      }, 5000);
    }
  };

  useEffect(() => {
    // Animate score ring
    const circumference = 2 * Math.PI * 85; // radius = 85
    const offset = circumference - (plagiarism_percent / 100) * circumference;
    // Add small delay for animation
    setTimeout(() => {
      setScoreOffset(offset);
    }, 100);

    // Trigger confetti if score is low (< 5%)
    if (plagiarism_percent < 5) {
      triggerConfetti();
    }
  }, [plagiarism_percent]);

  const toggleMatch = (index) => {
    setExpandedMatches((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const getReportData = () => {
    const reportMatches = matches.map((m) => ({
      text: m.chunk,
      similarity: m.citation_safe ? "Cited" : `${m.similarity}%`,
      source: m.source,
    }));
    return {
      score: `${plagiarism_percent}%`,
      originality: `${originalityScore}%`,
      matches: reportMatches,
    };
  };

  const handleDownloadTxt = (e) => {
    e.preventDefault();
    const { score, originality, matches: reportMatches } = getReportData();

    const report = `Plagiarism Analysis Report
Date: ${new Date().toLocaleString()}

Summary:
-----------------------------------
Plagiarism Score: ${score}
Originality Score: ${originality}
Sources Found: ${reportMatches.length}

Matches:
-----------------------------------
${reportMatches
  .map(
    (m, i) => `
Match #${i + 1}
Similarity: ${m.similarity}
Source: ${m.source}
Content: ${m.text}
`
  )
  .join("\n")}
`;

    const blob = new Blob([report], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "plagiarism-report.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setShowDropdown(false);
  };

  const handleDownloadPdf = (e) => {
    e.preventDefault();
    const { score, originality, matches: reportMatches } = getReportData();

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 20;
    let y = 20;

    // Title
    doc.setFontSize(22);
    doc.setTextColor(139, 92, 246);
    doc.text("Plagiarism Analysis Report", margin, y);
    y += 10;

    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`Date: ${new Date().toLocaleString()}`, margin, y);
    y += 15;

    // Summary Box
    doc.setDrawColor(200);
    doc.setFillColor(245, 247, 250);
    doc.rect(margin, y, pageWidth - 2 * margin, 35, "F");

    y += 10;
    doc.setFontSize(14);
    doc.setTextColor(0);
    doc.text("Summary", margin + 5, y);

    y += 10;
    doc.setFontSize(11);
    doc.text(`Plagiarism Score: ${score}`, margin + 5, y);
    doc.text(`Originality Score: ${originality}`, margin + 60, y);
    doc.text(`Sources Found: ${reportMatches.length}`, margin + 120, y);

    y += 25;

    // Matches
    doc.setFontSize(14);
    doc.setTextColor(0);
    doc.text("Detailed Matches", margin, y);
    y += 10;

    doc.setFontSize(10);

    reportMatches.forEach((m, i) => {
      if (y > 270) {
        doc.addPage();
        y = 20;
      }

      doc.setDrawColor(220);
      doc.line(margin, y, pageWidth - margin, y);
      y += 10;

      doc.setFont(undefined, "bold");
      doc.text(`Match #${i + 1}`, margin, y);
      doc.setFont(undefined, "normal");

      doc.text(`Similarity: ${m.similarity}`, margin + 40, y);
      y += 7;

      doc.setTextColor(6, 182, 212);
      const sourceText = doc.splitTextToSize(
        `Source: ${m.source}`,
        pageWidth - 2 * margin
      );
      doc.text(sourceText, margin, y);
      doc.setTextColor(0);
      y += 7 * sourceText.length;

      doc.setFont(undefined, "italic");
      const contentText = doc.splitTextToSize(
        `"${m.text}"`,
        pageWidth - 2 * margin
      );
      doc.text(contentText, margin, y);
      doc.setFont(undefined, "normal");

      y += 7 * contentText.length + 5;
    });

    if (reportMatches.length === 0) {
      doc.text("No plagiarism detected. Great job!", margin, y);
    }

    doc.save("plagiarism-report.pdf");
    setShowDropdown(false);
  };

  const handleCopy = () => {
    // Quick simple copy implementation for report text (reusing txt logic roughly)
    const { score, originality } = getReportData();
    const report = `Plagiarism Analysis Report\nPlagiarism Score: ${score}\nOriginality Score: ${originality}`;
    navigator.clipboard.writeText(report).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const truncateUrl = (url) => {
    try {
      const urlObj = new URL(url);
      const domain = urlObj.hostname.replace("www.", "");
      const path = urlObj.pathname;
      if (path.length > 30) return domain + path.substring(0, 30) + "...";
      return domain + path;
    } catch {
      return url.length > 50 ? url.substring(0, 50) + "..." : url;
    }
  };

  return (
    <section className="results-section" id="results-section">
      <div className="glass-card results-card">
        <div className="results-header">
          <h2 className="section-title">Analysis Results</h2>
          <button className="new-check-btn" onClick={onNewCheck}>
            <RefreshCw size={18} /> New Check
          </button>

          <div className="dropdown" onMouseLeave={() => setShowDropdown(false)}>
            <button
              className="download-btn"
              style={{ marginLeft: "10px" }}
              onMouseEnter={() => setShowDropdown(true)}
            >
              <Download size={18} /> Download{" "}
              <ChevronDown size={14} style={{ marginLeft: 4 }} />
            </button>
            {showDropdown && (
              <div className="dropdown-content" style={{ display: "block" }}>
                <a href="#" onClick={handleDownloadTxt}>
                  Text Report (.txt)
                </a>
                <a href="#" onClick={handleDownloadPdf}>
                  PDF Report (.pdf)
                </a>
              </div>
            )}
          </div>

          <button
            className={`copy-btn ${copied ? "copied" : ""}`}
            onClick={handleCopy}
            style={{ marginLeft: "10px" }}
            title="Copy Report to Clipboard"
          >
            {copied ? <CheckCircle size={18} /> : <Copy size={18} />}{" "}
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>

        {/* Plagiarism Score */}
        <div className="score-container">
          <div className="score-circle">
            <svg className="score-ring" width="200" height="200">
              <circle className="score-ring-bg" cx="100" cy="100" r="85" />
              <circle
                className="score-ring-fill"
                cx="100"
                cy="100"
                r="85"
                style={{ strokeDashoffset: scoreOffset }}
              />
              <defs>
                <linearGradient
                  id="score-gradient"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="100%"
                >
                  <stop
                    offset="0%"
                    stopColor={
                      plagiarism_percent > 50
                        ? "#EF4444"
                        : plagiarism_percent > 25
                        ? "#F59E0B"
                        : "#10B981"
                    }
                  />
                  <stop
                    offset="100%"
                    stopColor={
                      plagiarism_percent > 50
                        ? "#EC4899"
                        : plagiarism_percent > 25
                        ? "#8B5CF6"
                        : "#06B6D4"
                    }
                  />
                </linearGradient>
              </defs>
            </svg>
            <div className="score-content">
              <div className="score-value">{plagiarism_percent}</div>
              <div className="score-label">Plagiarism</div>
            </div>
          </div>
          <div className="score-details">
            <div className="score-detail-item">
              <div className="detail-label">Originality</div>
              <div className="detail-value">{originalityScore}%</div>
            </div>
            <div className="score-detail-item">
              <div className="detail-label">Sources Found</div>
              <div className="detail-value">{sourcesCount}</div>
            </div>
            <div className="score-detail-item">
              <div className="detail-label">Cited Chunks</div>
              <div className="detail-value">{citedCount}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Matches */}
      <div className="matches-container">
        <h3 className="matches-title">Detected Matches</h3>
        <div className="matches-list">
          {matches.length === 0 ? (
            <div className="match-card">
              <p
                style={{
                  textAlign: "center",
                  color: "var(--color-text-secondary)",
                }}
              >
                🎉 No plagiarism detected! Your content appears to be original.
              </p>
            </div>
          ) : (
            matches.map((match, index) => {
              const similarity = match.similarity;
              let similarityClass = "similarity-low";
              if (similarity > 70) similarityClass = "similarity-high";
              else if (similarity > 40) similarityClass = "similarity-medium";

              let statusClass = "status-warning";
              if (match.citation_safe) statusClass = "status-safe";
              else if (similarity > 60) statusClass = "status-danger";

              let recClass = "recommendation-warning";
              if (match.citation_safe) recClass = "recommendation-safe";
              else if (similarity > 60) recClass = "recommendation-danger";

              const hasRealSource =
                match.source && match.source !== "Citation Detected";

              return (
                <div
                  key={index}
                  className={`match-card ${
                    match.citation_safe ? "citation-safe" : ""
                  }`}
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <div className="match-header">
                    <div className="match-similarity">
                      {match.citation_safe ? (
                        <span className="citation-badge">
                          <CheckCircle size={14} />
                          Cited ({match.citation_style || ""})
                        </span>
                      ) : (
                        <span className={`similarity-badge ${similarityClass}`}>
                          {similarity}% Match
                        </span>
                      )}
                    </div>
                  </div>

                  <div className={`match-status ${statusClass}`}>
                    {match.status ||
                      (match.citation_safe
                        ? "Properly Cited"
                        : "Potential Plagiarism")}
                  </div>

                  <p className="match-text">"{match.chunk}"</p>

                  {hasRealSource && (
                    <div className="match-source">
                      <div style={{ flexShrink: 0 }}>
                        <FileText size={16} />
                      </div>
                      <span>
                        Source:{" "}
                        <a
                          href={match.source}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {truncateUrl(match.source)}
                        </a>
                      </span>
                    </div>
                  )}

                  {match.recommendation && (
                    <div className={`match-recommendation ${recClass}`}>
                      <h4>
                        <AlertCircle size={16} />
                        Recommendation
                      </h4>
                      <p>{match.recommendation}</p>
                    </div>
                  )}

                  {match.matched_content && (
                    <>
                      <button
                        className="preview-toggle"
                        onClick={() => toggleMatch(index)}
                      >
                        <ChevronRight
                          size={16}
                          className="toggle-icon"
                          style={{
                            transform: expandedMatches[index]
                              ? "rotate(90deg)"
                              : "none",
                          }}
                        />
                        <span>
                          {expandedMatches[index]
                            ? "Hide Matched Content"
                            : "Show Matched Content"}
                        </span>
                      </button>
                      {expandedMatches[index] && (
                        <div
                          className="match-preview"
                          style={{ display: "block" }}
                        >
                          <div className="preview-section">
                            <h4>Your Content:</h4>
                            <div className="preview-content user-content">
                              {match.chunk}
                            </div>
                          </div>
                          <div className="preview-section">
                            <h4>Matched Content from Source:</h4>
                            <div className="preview-content matched-content">
                              {match.matched_content}
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </section>
  );
};

export default Results;
