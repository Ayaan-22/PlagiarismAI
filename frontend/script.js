// ===================================
// Configuration
// ===================================
const API_URL = "http://127.0.0.1:9001/check";
const HEALTH_CHECK_URL = "http://127.0.0.1:9001/health";

// ===================================
// DOM Elements
// ===================================
const fileTabBtn = document.getElementById("file-tab-btn");
const textTabBtn = document.getElementById("text-tab-btn");
const fileTab = document.getElementById("file-tab");
const textTab = document.getElementById("text-tab");

const uploadArea = document.getElementById("upload-area");
const fileInput = document.getElementById("file-input");
const fileInfo = document.getElementById("file-info");
const fileName = document.getElementById("file-name");
const removeFileBtn = document.getElementById("remove-file");

const textInput = document.getElementById("text-input");
const charCount = document.getElementById("char-count");

const submitBtn = document.getElementById("submit-btn");
const loadingOverlay = document.getElementById("loading-overlay");
const resultsSection = document.getElementById("results-section");
const newCheckBtn = document.getElementById("new-check-btn");

// Loading elements
const progressFill = document.getElementById("progress-fill");
const sourcesChecked = document.getElementById("sources-checked");
const chunksAnalyzed = document.getElementById("chunks-analyzed");

// Results elements
const plagiarismScore = document.getElementById("plagiarism-score");
const scoreRingFill = document.getElementById("score-ring-fill");
const originalityScore = document.getElementById("originality-score");
const sourcesFound = document.getElementById("sources-found");
const citedChunks = document.getElementById("cited-chunks");
const matchesList = document.getElementById("matches-list");

// ===================================
// State
// ===================================
let selectedFile = null;
let currentTab = "file";

// ===================================
// Tab Switching
// ===================================
fileTabBtn.addEventListener("click", () => switchTab("file"));
textTabBtn.addEventListener("click", () => switchTab("text"));

function switchTab(tab) {
  currentTab = tab;

  // Update buttons
  fileTabBtn.classList.toggle("active", tab === "file");
  textTabBtn.classList.toggle("active", tab === "text");

  // Update content
  fileTab.classList.toggle("active", tab === "file");
  textTab.classList.toggle("active", tab === "text");
}

// ===================================
// File Upload Handling
// ===================================
uploadArea.addEventListener("click", () => {
  fileInput.click();
});

uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadArea.classList.add("drag-over");
});

uploadArea.addEventListener("dragleave", () => {
  uploadArea.classList.remove("drag-over");
});

uploadArea.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadArea.classList.remove("drag-over");

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    const file = files[0];
    const validTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain",
    ];

    // Check extension as fallback
    const validExtensions = [".pdf", ".docx", ".txt"];
    const extension = "." + file.name.split(".").pop().toLowerCase();

    if (validTypes.includes(file.type) || validExtensions.includes(extension)) {
      handleFileSelect(file);
    } else {
      showError("Please upload a PDF, DOCX, or TXT file");
    }
  }
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) {
    handleFileSelect(e.target.files[0]);
  }
});

function handleFileSelect(file) {
  selectedFile = file;
  fileName.textContent = file.name;
  fileInfo.style.display = "flex";
  uploadArea.querySelector(".upload-icon").style.display = "none";
  uploadArea.querySelector(".upload-title").style.display = "none";
  uploadArea.querySelector(".upload-subtitle").style.display = "none";
}

removeFileBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  selectedFile = null;
  fileInput.value = "";
  fileInfo.style.display = "none";
  uploadArea.querySelector(".upload-icon").style.display = "block";
  uploadArea.querySelector(".upload-title").style.display = "block";
  uploadArea.querySelector(".upload-subtitle").style.display = "block";
});

// ===================================
// Text Input Handling
// ===================================
textInput.addEventListener("input", (e) => {
  const count = e.target.value.length;
  charCount.textContent = count.toLocaleString();
});

// ===================================
// Form Submission
// ===================================
submitBtn.addEventListener("click", async () => {
  // Validate input
  if (currentTab === "file" && !selectedFile) {
    showError("Please upload a PDF, DOCX, or TXT file");
    return;
  }

  if (currentTab === "text" && !textInput.value.trim()) {
    showError("Please enter some text to analyze");
    return;
  }

  // Prepare form data
  const formData = new FormData();

  if (currentTab === "file") {
    formData.append("file", selectedFile);
  } else {
    formData.append("text", textInput.value);
  }

  // Get selected scan mode
  const scanMode = document.querySelector(
    'input[name="scan-mode"]:checked'
  ).value;
  formData.append("scan_mode", scanMode);

  // Show loading
  showLoading();

  // Disable submit to prevent double clicks
  submitBtn.disabled = true;

  try {
    // Make API request
    const response = await fetch(API_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Failed to analyze content");
    }

    const result = await response.json();

    // Hide loading and show results
    hideLoading();
    displayResults(result);
  } catch (error) {
    hideLoading();
    showError(
      "An error occurred while analyzing your content. Please try again."
    );
    console.error("Error:", error);
  } finally {
    submitBtn.disabled = false;
  }
});

// ===================================
// Loading State
// ===================================
function showLoading() {
  loadingOverlay.style.display = "flex";
  resultsSection.style.display = "none";

  // Animate progress
  let progress = 0;
  let sources = 0;
  let chunks = 0;

  const progressInterval = setInterval(() => {
    progress += Math.random() * 15;
    if (progress > 90) progress = 90;

    progressFill.style.width = `${progress}%`;

    sources = Math.floor(Math.random() * 50) + sources;
    chunks = Math.floor(Math.random() * 5) + chunks;

    sourcesChecked.textContent = sources;
    chunksAnalyzed.textContent = chunks;
  }, 500);

  // Store interval ID for cleanup
  loadingOverlay.dataset.intervalId = progressInterval;
}

function hideLoading() {
  // Complete the progress bar
  progressFill.style.width = "100%";

  // Clear interval
  const intervalId = loadingOverlay.dataset.intervalId;
  if (intervalId) {
    clearInterval(parseInt(intervalId));
  }

  // Hide after a short delay
  setTimeout(() => {
    loadingOverlay.style.display = "none";
  }, 500);
}

// ===================================
// Results Display
// ===================================
function displayResults(data) {
  const { plagiarism_percent, matches, summary } = data;

  // Show results section
  resultsSection.style.display = "block";

  // Scroll to results
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  // Display plagiarism score
  plagiarismScore.textContent = `${plagiarism_percent}%`;
  originalityScore.textContent = `${(100 - plagiarism_percent).toFixed(1)}%`;

  if (summary) {
    sourcesFound.textContent = summary.chunks_with_matches;
    if (citedChunks) citedChunks.textContent = summary.citation_safe_chunks;
  } else {
    sourcesFound.textContent = matches.length;
    if (citedChunks) citedChunks.textContent = "0";
  }

  // Animate score ring
  const circumference = 2 * Math.PI * 85; // radius = 85
  const offset = circumference - (plagiarism_percent / 100) * circumference;

  // Add gradient definition for score ring
  if (!document.querySelector("#score-gradient")) {
    const svg = document.querySelector(".score-ring");
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    const gradient = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "linearGradient"
    );
    gradient.setAttribute("id", "score-gradient");
    gradient.setAttribute("x1", "0%");
    gradient.setAttribute("y1", "0%");
    gradient.setAttribute("x2", "100%");
    gradient.setAttribute("y2", "100%");

    const stop1 = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "stop"
    );
    stop1.setAttribute("offset", "0%");
    stop1.setAttribute(
      "stop-color",
      plagiarism_percent > 50
        ? "#EF4444"
        : plagiarism_percent > 25
        ? "#F59E0B"
        : "#10B981"
    );

    const stop2 = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "stop"
    );
    stop2.setAttribute("offset", "100%");
    stop2.setAttribute(
      "stop-color",
      plagiarism_percent > 50
        ? "#EC4899"
        : plagiarism_percent > 25
        ? "#8B5CF6"
        : "#06B6D4"
    );

    gradient.appendChild(stop1);
    gradient.appendChild(stop2);
    defs.appendChild(gradient);
    svg.appendChild(defs);
  }

  setTimeout(() => {
    scoreRingFill.style.strokeDashoffset = offset;
  }, 100);

  // Display matches
  displayMatches(matches);

  // Trigger confetti if score is low (excellent work)
  if (plagiarism_percent < 5) {
    setTimeout(triggerConfetti, 500);
  }
}

// ===================================
// Safe helpers for text & URLs (XSS hardening)
// ===================================
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function sanitizeUrl(url) {
  try {
    const parsed = new URL(url, window.location.origin);
    const protocol = parsed.protocol.toLowerCase();
    if (protocol === "http:" || protocol === "https:") {
      return parsed.href;
    }
    return "#";
  } catch {
    return "#";
  }
}

// ===================================
// Matches Display
// ===================================
function displayMatches(matches) {
  matchesList.innerHTML = "";

  if (matches.length === 0) {
    matchesList.innerHTML = `
            <div class="match-card">
                <p style="text-align: center; color: var(--color-text-secondary);">
                    🎉 No plagiarism detected! Your content appears to be original.
                </p>
            </div>
        `;
    return;
  }

  matches.forEach((match, index) => {
    const matchCard = document.createElement("div");
    matchCard.className = "match-card";
    if (match.citation_safe) {
      matchCard.classList.add("citation-safe");
    }
    matchCard.style.animationDelay = `${index * 0.1}s`;

    const similarity = match.similarity;
    let similarityClass = "similarity-low";
    if (similarity > 70) similarityClass = "similarity-high";
    else if (similarity > 40) similarityClass = "similarity-medium";

    // Status Color
    let statusClass = "status-warning";
    if (match.citation_safe) statusClass = "status-safe";
    else if (similarity > 60) statusClass = "status-danger";

    // Recommendation Color
    let recClass = "recommendation-warning";
    if (match.citation_safe) recClass = "recommendation-safe";
    else if (similarity > 60) recClass = "recommendation-danger";

    // Safely escaped text fields
    const statusText = escapeHtml(
      match.status ||
        (match.citation_safe ? "Properly Cited" : "Potential Plagiarism")
    );
    const chunkText = escapeHtml(match.chunk);
    const matchedContent = escapeHtml(match.matched_content);
    const recommendationText = escapeHtml(match.recommendation || "");
    const citationStyle = escapeHtml(match.citation_style || "");

    const hasRealSource = match.source && match.source !== "Citation Detected";

    const safeSourceUrl = hasRealSource ? sanitizeUrl(match.source) : null;
    const safeSourceLabel = hasRealSource
      ? escapeHtml(truncateUrl(match.source))
      : "";

    matchCard.innerHTML = `
            <div class="match-header">
                <div class="match-similarity">
                    ${
                      match.citation_safe
                        ? `<span class="citation-badge">
                             <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"></polyline>
                             </svg>
                             Cited (${citationStyle})
                           </span>`
                        : `<span class="similarity-badge ${similarityClass}">
                            ${similarity}% Match
                           </span>`
                    }
                </div>
            </div>
            
            <div class="match-status ${statusClass}">
                ${statusText}
            </div>

            <p class="match-text">"${chunkText}"</p>
            
            ${
              hasRealSource && safeSourceUrl
                ? `
            <div class="match-source">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                </svg>
                <span>Source: <a href="${safeSourceUrl}" target="_blank" rel="noopener noreferrer">${safeSourceLabel}</a></span>
            </div>`
                : ""
            }
            
            ${
              recommendationText
                ? `
            <div class="match-recommendation ${recClass}">
                <h4>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="16" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                    Recommendation
                </h4>
                <p>${recommendationText}</p>
            </div>`
                : ""
            }

            ${
              match.matched_content
                ? `
            <button class="preview-toggle" data-index="${index}">
                <svg class="toggle-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                <span>Show Matched Content</span>
            </button>
            <div class="match-preview" id="preview-${index}" style="display: none;">
                <div class="preview-section">
                    <h4>Your Content:</h4>
                    <div class="preview-content user-content">${chunkText}</div>
                </div>
                <div class="preview-section">
                    <h4>Matched Content from Source:</h4>
                    <div class="preview-content matched-content">${matchedContent}</div>
                </div>
            </div>
            `
                : ""
            }
        `;

    matchesList.appendChild(matchCard);
  });

  // Add click handlers for preview toggles
  document.querySelectorAll(".preview-toggle").forEach((button) => {
    button.addEventListener("click", function () {
      const index = this.dataset.index;
      const preview = document.getElementById(`preview-${index}`);
      const icon = this.querySelector(".toggle-icon");
      const text = this.querySelector("span");

      if (preview.style.display === "none") {
        preview.style.display = "block";
        icon.style.transform = "rotate(180deg)";
        text.textContent = "Hide Matched Content";
      } else {
        preview.style.display = "none";
        icon.style.transform = "rotate(0deg)";
        text.textContent = "Show Matched Content";
      }
    });
  });
}

// ===================================
// New Check
// ===================================
newCheckBtn.addEventListener("click", () => {
  // Reset form
  selectedFile = null;
  fileInput.value = "";
  textInput.value = "";
  charCount.textContent = "0";

  fileInfo.style.display = "none";
  uploadArea.querySelector(".upload-icon").style.display = "block";
  uploadArea.querySelector(".upload-title").style.display = "block";
  uploadArea.querySelector(".upload-subtitle").style.display = "block";

  // Hide results
  resultsSection.style.display = "none";

  // Scroll to upload section
  document.getElementById("checker").scrollIntoView({ behavior: "smooth" });
});

// ===================================
// Download Report  (fixed for citation-safe cards)
// ===================================
// ===================================
// Download Report (PDF & TXT)
// ===================================
const downloadTxtBtn = document.getElementById("download-txt");
const downloadPdfBtn = document.getElementById("download-pdf");

function getReportData() {
  const score = plagiarismScore.textContent;
  const originality = originalityScore.textContent;

  const matches = Array.from(matchesList.children)
    .map((card) => {
      const textEl = card.querySelector(".match-text");
      if (!textEl) return null;

      const similarityEl = card.querySelector(".similarity-badge");
      const citationEl = card.querySelector(".citation-badge");

      const similarity = similarityEl
        ? similarityEl.textContent.trim()
        : citationEl
        ? citationEl.textContent.trim()
        : "N/A";

      const sourceEl = card.querySelector(".match-source a");
      const source = sourceEl ? sourceEl.href : "N/A";

      return {
        text: textEl.textContent,
        similarity,
        source,
      };
    })
    .filter((m) => m);

  return { score, originality, matches };
}

downloadTxtBtn.addEventListener("click", (e) => {
  e.preventDefault();
  const { score, originality, matches } = getReportData();

  const report = `Plagiarism Analysis Report
Date: ${new Date().toLocaleString()}

Summary:
-----------------------------------
Plagiarism Score: ${score}
Originality Score: ${originality}
Sources Found: ${matches.length}

Matches:
-----------------------------------
${matches
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
});

downloadPdfBtn.addEventListener("click", (e) => {
  e.preventDefault();
  const { score, originality, matches } = getReportData();
  const { jsPDF } = window.jspdf;

  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 20;
  let y = 20;

  // Title
  doc.setFontSize(22);
  doc.setTextColor(139, 92, 246); // Primary color
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
  doc.text(`Sources Found: ${matches.length}`, margin + 120, y);

  y += 25;

  // Matches
  doc.setFontSize(14);
  doc.setTextColor(0);
  doc.text("Detailed Matches", margin, y);
  y += 10;

  doc.setFontSize(10);

  matches.forEach((m, i) => {
    // Check for page break
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

    doc.setTextColor(6, 182, 212); // Link color
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

  if (matches.length === 0) {
    doc.text("No plagiarism detected. Great job!", margin, y);
  }

  doc.save("plagiarism-report.pdf");
});

const copyBtn = document.getElementById("copy-btn");

copyBtn.addEventListener("click", () => {
  const score = plagiarismScore.textContent;
  const originality = originalityScore.textContent;

  const matches = Array.from(matchesList.children)
    .map((card) => {
      const textEl = card.querySelector(".match-text");
      if (!textEl) return null;

      const similarityEl = card.querySelector(".similarity-badge");
      const citationEl = card.querySelector(".citation-badge");

      const similarity = similarityEl
        ? similarityEl.textContent.trim()
        : citationEl
        ? citationEl.textContent.trim()
        : "N/A";

      const sourceEl = card.querySelector(".match-source a");
      const source = sourceEl ? sourceEl.href : "N/A";

      return {
        text: textEl.textContent,
        similarity,
        source,
      };
    })
    .filter((m) => m);

  const report = `Plagiarism Analysis Report
Date: ${new Date().toLocaleString()}

Summary:
-----------------------------------
Plagiarism Score: ${score}
Originality Score: ${originality}
Sources Found: ${matches.length}

Matches:
-----------------------------------
${matches
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

  navigator.clipboard.writeText(report).then(() => {
    const originalText = copyBtn.innerHTML;
    copyBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
      Copied!
    `;
    copyBtn.classList.add("copied");

    setTimeout(() => {
      copyBtn.innerHTML = originalText;
      copyBtn.classList.remove("copied");
    }, 2000);
  });
});

// ===================================
// Confetti Effect
// ===================================
function triggerConfetti() {
  const container = document.getElementById("confetti-container");
  const colors = ["#8b5cf6", "#06b6d4", "#ec4899", "#10b981", "#f59e0b"];

  for (let i = 0; i < 100; i++) {
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
}

// ===================================
// Utility Functions
// ===================================
function showError(message) {
  // Create error toast
  const toast = document.createElement("div");
  toast.className = "error-toast";
  toast.textContent = message;
  toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #EF4444, #DC2626);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
        font-weight: 500;
    `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "slideOutRight 0.3s ease-out";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function truncateUrl(url) {
  try {
    const urlObj = new URL(url);
    const domain = urlObj.hostname.replace("www.", "");
    const path = urlObj.pathname;

    if (path.length > 30) {
      return domain + path.substring(0, 30) + "...";
    }
    return domain + path;
  } catch {
    return url.length > 50 ? url.substring(0, 50) + "..." : url;
  }
}

// ===================================
// Add toast animations to CSS dynamically
// ===================================
const style = document.createElement("style");
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ===================================
// Smooth scroll for navigation
// ===================================
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

// ===================================
// Connection Status Check
// ===================================
const connectionStatus = document.getElementById("connection-status");
const statusText = connectionStatus.querySelector(".status-text");

async function checkBackendConnection() {
  try {
    const opts = { method: "GET" };
    // Gracefully handle older browsers that don't support AbortSignal.timeout
    if (typeof AbortSignal !== "undefined" && AbortSignal.timeout) {
      opts.signal = AbortSignal.timeout(3000);
    }

    const response = await fetch(HEALTH_CHECK_URL, opts);

    if (response.ok) {
      connectionStatus.classList.remove("disconnected");
      connectionStatus.classList.add("connected");
      statusText.textContent = "Connected";
      return true;
    } else {
      throw new Error("Backend not responding");
    }
  } catch (error) {
    connectionStatus.classList.remove("connected");
    connectionStatus.classList.add("disconnected");
    statusText.textContent = "Disconnected";
    return false;
  }
}

// Check connection on load
checkBackendConnection();

// Check connection every 10 seconds
setInterval(checkBackendConnection, 10000);

// ===================================
// Initialize
// ===================================
console.log("🚀 Plagiarism Checker initialized");
console.log("📡 API URL:", API_URL);
