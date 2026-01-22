"use client";

import { useState } from "react";
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
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">

      {/* 📄 Paper-style Drop Zone */}
      <label className="block cursor-pointer">
        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) =>
            setFile(e.target.files ? e.target.files[0] : null)
          }
        />

        <div
          className="rounded-xl border border-dashed border-white/20
          bg-white/5 hover:bg-white/10 transition
          p-6 text-center space-y-2"
        >
          <p className="text-sm text-gray-300">
            {file ? file.name : "Drop PDF here or click to browse"}
          </p>
          <p className="text-xs text-gray-500">
            PDF only · Scanned or text-based
          </p>
        </div>
      </label>

      {/* 🔁 Translation Direction */}
      <select
        value={direction}
        onChange={(e) => setDirection(e.target.value)}
        className="w-full bg-[#020617] border border-white/10
          rounded-md px-3 py-2 text-sm text-gray-200"
      >
        <option value="to_en">
          Gujarati / Hindi / Marathi → English
        </option>
        <option value="from_en">
          English → Gujarati / Hindi / Marathi
        </option>
      </select>

      {/* 🌐 Language + Mode */}
      {direction === "to_en" && (
        <div className="space-y-3">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full bg-[#020617] border border-white/10
              rounded-md px-3 py-2 text-sm text-gray-200"
          >
            <option value="gu">Gujarati (Source)</option>
            <option value="hi">Hindi (Source)</option>
            <option value="mr">Marathi (Source)</option>
          </select>

          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="w-full bg-[#020617] border border-white/10
              rounded-md px-3 py-2 text-sm text-gray-200"
          >
            <option value="general">
              General Translation
            </option>
            <option value="government">
              Government / NCERT
            </option>
          </select>
        </div>
      )}

      {direction === "from_en" && (
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full bg-[#020617] border border-white/10
            rounded-md px-3 py-2 text-sm text-gray-200"
        >
          <option value="gu">Gujarati (Target)</option>
          <option value="hi">Hindi (Target)</option>
          <option value="mr">Marathi (Target)</option>
        </select>
      )}

      {/* ▶️ Action Button */}
      <button
        onClick={handleUpload}
        disabled={loading}
        className="w-full py-2.5 rounded-lg text-sm font-medium text-white
          bg-gradient-to-r from-indigo-600 to-cyan-600
          hover:from-indigo-500 hover:to-cyan-500
          disabled:opacity-50 transition"
      >
        {loading ? "Processing…" : "Upload & Translate"}
      </button>

      {/* ⚠️ Error */}
      {error && (
        <p className="text-xs text-red-400 text-center">
          {error}
        </p>
      )}
    </div>
  );
}
