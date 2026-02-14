"use client";

import { BookOpen, Zap, Globe2, Shield } from "lucide-react";

interface Props {
  progress: number;
}

export default function WaitingTimeFiller({ progress }: Props) {
  // Only show when progress is active
  if (progress === 0 || progress >= 100) {
    return null;
  }

  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Lightning Fast",
      description: "Process documents 10x faster with optimized AI pipeline",
    },
    {
      icon: <Globe2 className="w-6 h-6" />,
      title: "Multi-Language",
      description: "Support for Gujarati, Hindi, Marathi, and English",
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Secure & Private",
      description: "Files automatically deleted after translation",
    },
    {
      icon: <BookOpen className="w-6 h-6" />,
      title: "OCR Enabled",
      description: "Works with scanned PDFs and images",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="text-center">
        <p className="text-sm text-gray-400 mb-4">
          While you wait, here's what makes LipiTranslate special:
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {features.map((feature, idx) => (
          <div
            key={idx}
            className="rounded-xl bg-white/5 border border-white/10 p-5 hover:bg-white/10 hover:border-cyan-500/30 transition"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 flex items-center justify-center text-cyan-400 flex-shrink-0">
                {feature.icon}
              </div>
              <div>
                <h3 className="text-white font-semibold mb-1">
                  {feature.title}
                </h3>
                <p className="text-sm text-gray-400">
                  {feature.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="text-center">
        <p className="text-xs text-gray-500">
          💡 Tip: Bookmark this page for future translations
        </p>
      </div>
    </div>
  );
}