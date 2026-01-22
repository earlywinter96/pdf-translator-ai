"use client";

import { useRouter } from "next/navigation";
import TerminalTitle from "@/components/TerminalTitle";


export default function HomeClient() {
  const router = useRouter();

  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">

      {/* Hero background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[720px] h-[720px] bg-cyan-500/20 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      {/* MAIN HERO CONTENT */}
      <div className="relative max-w-4xl mx-auto pt-24 pb-24 space-y-14 text-center">

        {/* Title */}
        <TerminalTitle />





        {/* Subtitle */}
        <p className="text-gray-400 text-lg leading-relaxed">
          Translate scanned and text-based PDFs from{" "}
          <span className="text-gray-200 font-medium">
            Gujarati, Hindi, and Marathi
          </span>{" "}
          into accurate, structured English using AI.
        </p>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
          <Feature
            title="OCR + AI Translation"
            desc="Accurately extracts and translates text from scanned government and textbook PDFs."
          />
          <Feature
            title="Indian Language Focus"
            desc="Optimized specifically for Gujarati, Hindi, and Marathi documents."
          />
          <Feature
            title="Large PDFs Supported"
            desc="Handles long PDFs (300–400 pages) with reliable progress tracking."
          />
        </div>

        {/* Built by */}
        <div className="pt-4 text-sm text-gray-500">
          Built by{" "}
          <span className="text-gray-300 font-medium">
            Hemant Solanki
          </span>
        </div>

        {/* CTA */}
        <div className="pt-4">
          <button
            onClick={() => router.push("/convert")}
            className="px-8 py-3 rounded-lg text-white font-medium
              bg-gradient-to-r from-indigo-600 to-cyan-600
              hover:from-indigo-500 hover:to-cyan-500
              transition shadow-lg"
          >
            Convert PDF →
          </button>
        </div>
      </div>

      {/* SEO / EXPLANATION SECTION (MOVED HERE) */}
      <section className="relative max-w-4xl mx-auto pb-20 text-gray-400 text-sm leading-relaxed">
        <h2 className="text-white text-lg font-medium mb-2">
          Translate PDF Documents with AI
        </h2>
        <p>
          This AI-powered PDF translator helps convert scanned and
          text-based documents into accurate, readable translations.
          It supports PDFs commonly used in education, government, and
          research, where layout and terminology matter.
        </p>
      </section>

      {/* HOW IT WORKS */}
      <div className="relative max-w-4xl mx-auto pb-28 space-y-6">
        <h2 className="text-2xl font-semibold text-white text-center">
          How it works
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Step
            number="1"
            title="Upload PDF"
            desc="Upload scanned or text-based PDFs in supported languages."
          />
          <Step
            number="2"
            title="OCR Processing"
            desc="Text is extracted and cleaned using OCR and AI."
          />
          <Step
            number="3"
            title="AI Translation"
            desc="Translation preserves meaning, terminology, and structure."
          />
          <Step
            number="4"
            title="Download"
            desc="Receive a clean, readable translated PDF."
          />
        </div>
      </div>

    </main>
  );
}

/* Components unchanged */

function Feature({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
      <h3 className="text-white font-medium mb-1">{title}</h3>
      <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}

function Step({
  number,
  title,
  desc,
}: {
  number: string;
  title: string;
  desc: string;
}) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-center space-y-2">
      <div className="w-8 h-8 mx-auto rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-semibold">
        {number}
      </div>
      <h3 className="text-white font-medium">{title}</h3>
      <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}
