// ===================================
// Configuration
// ===================================
const API_URL = "http://127.0.0.1:9001/check";

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

  // Show loading
  showLoading();

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
  const { plagiarism_percent, matches } = data;

  // Show results section
  resultsSection.style.display = "block";

  // Scroll to results
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  // Display plagiarism score
  plagiarismScore.textContent = `${plagiarism_percent}%`;
  originalityScore.textContent = `${(100 - plagiarism_percent).toFixed(1)}%`;
  sourcesFound.textContent = matches.length;

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
}

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
    matchCard.style.animationDelay = `${index * 0.1}s`;

    const similarity = match.similarity;
    let similarityClass = "similarity-low";
    if (similarity > 70) similarityClass = "similarity-high";
    else if (similarity > 40) similarityClass = "similarity-medium";

    matchCard.innerHTML = `
            <div class="match-header">
                <div class="match-similarity">
                    <span class="similarity-badge ${similarityClass}">
                        ${similarity}% Match
                    </span>
                </div>
            </div>
            <p class="match-text">"${match.chunk}"</p>
            <div class="match-source">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                </svg>
                <span>Source: <a href="${
                  match.source
                }" target="_blank" rel="noopener noreferrer">${truncateUrl(
      match.source
    )}</a></span>
            </div>
        `;

    matchesList.appendChild(matchCard);
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
// Download Report
// ===================================
const downloadBtn = document.getElementById("download-btn");

downloadBtn.addEventListener("click", () => {
  const score = plagiarismScore.textContent;
  const originality = originalityScore.textContent;
  const matches = Array.from(matchesList.children)
    .map((card) => {
      if (card.querySelector(".match-text")) {
        return {
          text: card.querySelector(".match-text").textContent,
          similarity: card
            .querySelector(".similarity-badge")
            .textContent.trim(),
          source: card.querySelector(".match-source a").href,
        };
      }
      return null;
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
// Initialize
// ===================================
console.log("🚀 Plagiarism Checker initialized");
console.log("📡 API URL:", API_URL);
