import React, { useState, useRef } from "react";
import { Upload, FileText, X, File, Clipboard } from "lucide-react";

const UploadSection = ({ onSubmit, isLoading }) => {
  const [activeTab, setActiveTab] = useState("file");
  const [selectedFile, setSelectedFile] = useState(null);
  const [textInput, setTextInput] = useState("");
  const [scanMode, setScanMode] = useState("quick");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const validateAndSetFile = (file) => {
    const validTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain",
    ];
    const validExtensions = [".pdf", ".docx", ".txt"];
    const extension = "." + file.name.split(".").pop().toLowerCase();

    if (validTypes.includes(file.type) || validExtensions.includes(extension)) {
      setSelectedFile(file);
    } else {
      alert("Please upload a PDF, DOCX, or TXT file");
    }
  };

  const removeFile = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = () => {
    if (activeTab === "file" && !selectedFile) {
      alert("Please upload a file");
      return;
    }
    if (activeTab === "text" && !textInput.trim()) {
      alert("Please enter some text");
      return;
    }

    const formData = new FormData();
    if (activeTab === "file") {
      formData.append("file", selectedFile);
    } else {
      formData.append("text", textInput);
    }
    formData.append("scan_mode", scanMode);

    onSubmit(formData);
  };

  return (
    <section className="upload-section" id="checker">
      <div className="glass-card upload-card">
        <h2 className="section-title">Check Your Content</h2>
        <p className="section-description">
          Upload a PDF, DOCX, or TXT document or paste your text below
        </p>

        {/* Tab Switcher */}
        <div className="tab-switcher">
          <button
            className={`tab-btn ${activeTab === "file" ? "active" : ""}`}
            onClick={() => handleTabChange("file")}
          >
            <Upload size={20} />
            Upload File
          </button>
          <button
            className={`tab-btn ${activeTab === "text" ? "active" : ""}`}
            onClick={() => handleTabChange("text")}
          >
            <Clipboard size={20} />
            Paste Text
          </button>
        </div>

        {/* File Upload Tab */}
        <div
          className={`tab-content ${activeTab === "file" ? "active" : ""}`}
          id="file-tab"
        >
          <div
            className={`upload-area ${isDragging ? "drag-over" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !selectedFile && fileInputRef.current.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.docx,.txt"
              hidden
            />

            {selectedFile ? (
              <div className="file-info" style={{ display: "flex" }}>
                <File size={24} />
                <span id="file-name">{selectedFile.name}</span>
                <button className="remove-file" onClick={removeFile}>
                  ×
                </button>
              </div>
            ) : (
              <>
                <div className="upload-icon">
                  <Upload size={64} strokeWidth={1.5} />
                </div>
                <h3 className="upload-title">Drop your file here</h3>
                <p className="upload-subtitle">or click to browse</p>
              </>
            )}
          </div>
        </div>

        {/* Text Input Tab */}
        <div
          className={`tab-content ${activeTab === "text" ? "active" : ""}`}
          id="text-tab"
        >
          <textarea
            className="text-input"
            placeholder="Paste your text here for plagiarism analysis..."
            rows="10"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
          ></textarea>
          <div className="char-count">
            <span>{textInput.length.toLocaleString()}</span> characters
          </div>
        </div>

        {/* Scan Mode Selector */}
        <div className="scan-mode-selector">
          <label className="scan-mode-label">Scan Mode:</label>
          <div className="scan-mode-options">
            <label className="scan-mode-option">
              <input
                type="radio"
                name="scan-mode"
                value="quick"
                checked={scanMode === "quick"}
                onChange={(e) => setScanMode(e.target.value)}
              />
              <span className="option-content">
                <span className="option-title">⚡ Quick Scan</span>
                <span className="option-desc">~15 chunks, faster results</span>
              </span>
            </label>
            <label className="scan-mode-option">
              <input
                type="radio"
                name="scan-mode"
                value="deep"
                checked={scanMode === "deep"}
                onChange={(e) => setScanMode(e.target.value)}
              />
              <span className="option-content">
                <span className="option-title">🔍 Deep Scan</span>
                <span className="option-desc">All content, comprehensive</span>
              </span>
            </label>
          </div>
        </div>

        {/* Submit Button */}
        <button
          className="submit-btn"
          onClick={handleSubmit}
          disabled={isLoading}
        >
          <span className="btn-text">
            {isLoading ? "Analyzing..." : "Analyze Content"}
          </span>
          {!isLoading && <FileText size={20} />}
        </button>
      </div>
    </section>
  );
};

export default UploadSection;
