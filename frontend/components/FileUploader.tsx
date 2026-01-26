"use client";

import { useState } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, X } from "lucide-react";
import { uploadPDF } from "@/lib/api";

interface Props {
  onJobCreated: (jobId: string) => void;
}

export default function FileUploader({ onJobCreated }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("gu");
  const [direction, setDirection] = useState("to_en");
  const [mode, setMode] = useState("general");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  // File validation
  const validateFile = (selectedFile: File) => {
    // Check file type
    if (selectedFile.type !== "application/pdf") {
      setError("Please select a PDF file");
      return false;
    }

    // Check file size (25MB limit)
    const maxSize = 25 * 1024 * 1024;
    if (selectedFile.size > maxSize) {
      setError("File size must be less than 25MB. Try compressing your PDF.");
      return false;
    }

    return true;
  };

  // Handle file selection
  const handleFileSelect = (selectedFile: File | null) => {
    if (!selectedFile) return;

    if (validateFile(selectedFile)) {
      setFile(selectedFile);
      setError(null);
    } else {
      setFile(null);
    }
  };

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  // Upload handler
  async function handleUpload() {
    if (!file) {
      setError("Please select a PDF file");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const response = await uploadPDF(file, language, direction, mode);
      onJobCreated(response.job_id);
    } catch (err: any) {
      setError(err.message || "Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">

      {/* Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !file && document.getElementById("file-input")?.click()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center
          transition cursor-pointer
          ${dragActive
            ? "border-cyan-500 bg-cyan-500/10"
            : file
            ? "border-green-500/50 bg-green-500/5"
            : "border-white/20 bg-white/5 hover:bg-white/10 hover:border-white/30"
          }
        `}
      >
        <input
          id="file-input"
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
        />

        {!file ? (
          <div className="space-y-3">
            <Upload className="w-10 h-10 mx-auto text-gray-400" />
            <div>
              <p className="text-gray-300 font-medium mb-1">
                Drop your PDF here or click to browse
              </p>
              <p className="text-xs text-gray-500">
                PDF only • Max 25MB • Up to 400 pages
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <CheckCircle className="w-10 h-10 mx-auto text-green-400" />
            <div>
              <p className="text-white font-medium">{file.name}</p>
              <p className="text-sm text-gray-400 mt-1">
                {formatFileSize(file.size)}
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
              }}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md
                text-xs text-gray-300 border border-white/20
                hover:bg-white/5 transition"
            >
              <X className="w-3 h-3" />
              Remove
            </button>
          </div>
        )}
      </div>

      {/* Translation Direction */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Translation Direction
        </label>
        <select
          value={direction}
          onChange={(e) => setDirection(e.target.value)}
          className="w-full bg-[#020617] border border-white/10
            rounded-lg px-4 py-3 text-sm text-gray-200
            focus:border-cyan-500 focus:outline-none transition"
        >
          <option value="to_en">
            Indian Language → English
          </option>
          <option value="from_en">
            English → Indian Language
          </option>
        </select>
      </div>

      {/* Language Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          {direction === "to_en" ? "Source Language" : "Target Language"}
        </label>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full bg-[#020617] border border-white/10
            rounded-lg px-4 py-3 text-sm text-gray-200
            focus:border-cyan-500 focus:outline-none transition"
        >
          <option value="gu">Gujarati (ગુજરાતી)</option>
          <option value="hi">Hindi (हिन्दी)</option>
          <option value="mr">Marathi (मराठी)</option>
        </select>
      </div>

      {/* Translation Mode (only for to_en) */}
      {direction === "to_en" && (
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Translation Mode
          </label>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="w-full bg-[#020617] border border-white/10
              rounded-lg px-4 py-3 text-sm text-gray-200
              focus:border-cyan-500 focus:outline-none transition"
          >
            <option value="general">General Translation</option>
            <option value="government">Government / NCERT</option>
          </select>
          <p className="mt-2 text-xs text-gray-500">
            {mode === "general"
              ? "Best for everyday documents and personal content"
              : "Optimized for official documents and textbooks"
            }
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-start gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/30">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={loading || !file}
        className="w-full py-3.5 rounded-lg text-white font-medium
          bg-gradient-to-r from-indigo-600 to-cyan-600
          hover:from-indigo-500 hover:to-cyan-500
          disabled:opacity-50 disabled:cursor-not-allowed
          transition shadow-lg flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Uploading...
          </>
        ) : (
          <>
            <Upload className="w-5 h-5" />
            Upload & Translate
          </>
        )}
      </button>

      {/* Privacy Note */}
      <p className="text-xs text-center text-gray-500">
        🔒 Your file is processed securely and automatically deleted after translation
      </p>

    </div>
  );
}