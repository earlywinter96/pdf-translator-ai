"use client";

import { useState } from 'react';
import { Loader2 } from 'lucide-react';

interface Props {
  jobId: string;
  type?: 'original' | 'translated';
}

export default function PdfPreview({ jobId, type = 'translated' }: Props) {
  const [isLoading, setIsLoading] = useState(true);
  
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE ||
    "https://pdf-translator-ai-ggqe.onrender.com";
  
  const pdfUrl = type === 'original' 
    ? `${API_BASE}/api/preview/original/${jobId}`
    : `${API_BASE}/api/preview/translated/${jobId}`;

  return (
    <div className="relative w-full h-[70vh] border border-white/10 rounded-lg overflow-hidden bg-black">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-10">
          <div className="text-center space-y-3">
            <Loader2 className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
            <p className="text-sm text-gray-400">Loading PDF...</p>
          </div>
        </div>
      )}
      
      <iframe
        src={pdfUrl}
        className="w-full h-full"
        title={`${type === 'original' ? 'Original' : 'Translated'} PDF Preview`}
        allow="fullscreen"
        onLoad={() => setIsLoading(false)}
      />
    </div>
  );
}
