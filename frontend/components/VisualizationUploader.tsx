// components/VisualizationUploader.tsx
"use client";

import { useState, useCallback } from 'react';
import { Upload, Eye, AlertCircle, Loader2, CheckCircle, X, Sparkles, Brain } from 'lucide-react';

interface VisualizationUploaderProps {
  onJobCreated: (jobId: string) => void;
  sessionId?: string;
}

export default function VisualizationUploader({
  onJobCreated,
  sessionId,
}: VisualizationUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // PDF info
  const [pdfInfo, setPdfInfo] = useState<any>(null);
  
  // Visualization options
  const [contentType, setContentType] = useState<string>('auto');
  const [outputFormat, setOutputFormat] = useState<'json' | 'html'>('json');

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const MAX_PAGES = 20;

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  // Drag handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
      setPdfInfo(null);
      setError(null);
      checkPdf(droppedFile);
    } else {
      setError('Please upload a PDF file');
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setPdfInfo(null);
      setError(null);
      checkPdf(selectedFile);
    } else {
      setError('Please upload a PDF file');
    }
  }, []);

  const handleRemoveFile = () => {
    setFile(null);
    setPdfInfo(null);
    setError(null);
  };

  // Check PDF
  const checkPdf = async (pdfFile: File) => {
    setIsChecking(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', pdfFile);

      const headers: HeadersInit = {};
      if (sessionId) {
        headers['X-Session-ID'] = sessionId;
      }

      const response = await fetch(`${API_BASE}/api/check-pdf-pages`, {
        method: 'POST',
        headers,
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to check PDF');
      }

      const data = await response.json();
      
      console.log('PDF Check Response:', data); // Debug log
      
      setPdfInfo(data);

      // **FIX: Trust the API's visualization_available flag**
      // The backend already determines if visualization is available
      if (!data.visualization_available) {
        // Normalize language codes for better comparison
        const lang = (data.detected_language || '').toLowerCase();
        const isEnglish = lang === 'en' || lang === 'eng' || lang === 'english';
        
        if (!isEnglish) {
          setError('Only English PDFs can be visualized. Please translate to English first or use the translation feature.');
        } else if (data.page_count > MAX_PAGES) {
          setError(`PDF has ${data.page_count} pages. Visualization is limited to ${MAX_PAGES} pages.`);
        } else {
          setError(data.visualization_note || 'This PDF cannot be visualized');
        }
      }

    } catch (err: any) {
      console.error('PDF Check Error:', err); // Debug log
      setError(err.message || 'Failed to check PDF');
    } finally {
      setIsChecking(false);
    }
  };

  // Upload for visualization
  const handleVisualize = async () => {
    if (!file || !pdfInfo?.visualization_available) return;

    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      if (contentType !== 'auto') {
        formData.append('content_type', contentType);
      }
      
      formData.append('output_format', outputFormat);

      const headers: HeadersInit = {};
      if (sessionId) {
        headers['X-Session-ID'] = sessionId;
      }

      const response = await fetch(`${API_BASE}/api/visualize`, {
        method: 'POST',
        headers,
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Visualization failed');
      }

      const data = await response.json();
      
      console.log('Visualization Response:', data); // Debug log
      
      if (data.job_id) {
        onJobCreated(data.job_id);
      } else {
        throw new Error('No job ID returned');
      }

    } catch (err: any) {
      console.error('Visualization Error:', err); // Debug log
      setError(err.message || 'Failed to start visualization');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 p-8 space-y-6 shadow-2xl">
      
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-purple-500/20 to-pink-500/20 mb-2">
          <Brain className="w-8 h-8 text-purple-400" />
        </div>
        <h2 className="text-2xl font-bold text-white">
          PDF Visualization
        </h2>
        <p className="text-sm text-gray-400">
          Transform English PDFs into visual data structures
        </p>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !file && document.getElementById('viz-file-input')?.click()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center
          transition-all cursor-pointer
          ${isDragging 
            ? 'border-purple-400 bg-purple-500/10' 
            : file
            ? 'border-green-500/50 bg-green-500/5'
            : 'border-white/20 hover:border-white/40 bg-white/5'
          }
        `}
      >
        <input
          id="viz-file-input"
          type="file"
          accept="application/pdf"
          onChange={handleFileSelect}
          className="hidden"
          disabled={isChecking || isUploading}
        />

        <div className="space-y-4">
          {file ? (
            <>
              <CheckCircle className="w-12 h-12 mx-auto text-green-400" />
              <div>
                <p className="text-white font-medium">{file.name}</p>
                <p className="text-sm text-gray-400">
                  {formatFileSize(file.size)}
                  {pdfInfo && ` • ${pdfInfo.page_count} pages`}
                  {pdfInfo && ` • ${pdfInfo.detected_language.toUpperCase()}`}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveFile();
                }}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md
                  text-xs text-gray-300 border border-white/20
                  hover:bg-white/5 transition"
              >
                <X className="w-3 h-3" />
                Remove
              </button>
            </>
          ) : (
            <>
              <Sparkles className="w-12 h-12 mx-auto text-purple-400" />
              <div>
                <p className="text-white font-medium">
                  Drop your English PDF here
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  PDF only • Max {MAX_PAGES} pages • English language
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* PDF Info & Checking Status */}
      {isChecking && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
            <div className="text-sm text-blue-300">
              Checking PDF compatibility...
            </div>
          </div>
        </div>
      )}

      {/* Visualization Options */}
      {file && pdfInfo?.visualization_available && (
        <>
          <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
              <div className="text-sm text-green-300">
                <p className="font-medium mb-1">✅ Ready for Visualization</p>
                <p className="text-green-400/80 text-xs">
                  {pdfInfo.page_count} pages will be processed
                </p>
              </div>
            </div>
          </div>

          {/* Content Type */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Content Type
            </label>
            <select
              value={contentType}
              onChange={(e) => setContentType(e.target.value)}
              className="w-full bg-[#020617] border border-white/10
                rounded-lg px-4 py-3 text-sm text-gray-200
                focus:border-purple-500 focus:outline-none transition"
            >
              <option value="auto">Auto-detect (Recommended)</option>
              <option value="academic">Academic / Research</option>
              <option value="technical">Technical / Code</option>
              <option value="educational">Educational / Textbook</option>
              <option value="general">General Document</option>
            </select>
            <p className="mt-2 text-xs text-gray-500">
              {contentType === 'auto' && 'AI will detect the best structure for your content'}
              {contentType === 'academic' && 'Optimized for research papers with key concepts & relationships'}
              {contentType === 'technical' && 'Best for technical docs with architecture & code structures'}
              {contentType === 'educational' && 'Perfect for textbooks with learning objectives & concept maps'}
              {contentType === 'general' && 'Suitable for any document type'}
            </p>
          </div>

          {/* Output Format */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Output Format
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setOutputFormat('json')}
                className={`p-3 rounded-lg border transition ${
                  outputFormat === 'json'
                    ? 'border-purple-500 bg-purple-500/20 text-purple-300'
                    : 'border-white/10 text-gray-400 hover:border-purple-500/50'
                }`}
              >
                <div className="text-sm font-medium">JSON Data</div>
                <div className="text-xs mt-1 opacity-80">Structured data</div>
              </button>
              <button
                onClick={() => setOutputFormat('html')}
                className={`p-3 rounded-lg border transition ${
                  outputFormat === 'html'
                    ? 'border-purple-500 bg-purple-500/20 text-purple-300'
                    : 'border-white/10 text-gray-400 hover:border-purple-500/50'
                }`}
              >
                <div className="text-sm font-medium">HTML View</div>
                <div className="text-xs mt-1 opacity-80">Visual display</div>
              </button>
            </div>
          </div>
        </>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <div className="flex items-start gap-2 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium">Cannot Visualize</p>
              <p className="text-xs mt-1 opacity-90">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Visualize Button */}
      {file && pdfInfo?.visualization_available && (
        <button
          onClick={handleVisualize}
          disabled={isChecking || isUploading}
          className="w-full py-3 rounded-lg font-medium text-white
            bg-gradient-to-r from-purple-600 to-pink-600
            hover:from-purple-500 hover:to-pink-500
            disabled:opacity-50 disabled:cursor-not-allowed
            transition shadow-lg flex items-center justify-center gap-2"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Creating Visualization...</span>
            </>
          ) : (
            <>
              <Eye className="w-5 h-5" />
              <span>Visualize PDF</span>
            </>
          )}
        </button>
      )}

      {/* Info Note */}
      <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-gray-400 space-y-1">
            <p>• <span className="text-blue-300">FREE</span> for up to {MAX_PAGES} pages</p>
            <p>• English PDFs only (translate first if needed)</p>
            <p>• AI generates visual data structures, concept maps & relationships</p>
            <p>• Perfect for understanding academic papers, technical docs & reports</p>
          </div>
        </div>
      </div>

    </div>
  );
}