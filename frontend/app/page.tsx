// app/page.tsx
/**
 * Homepage - Updated for Sarvam AI
 */

import Link from "next/link";
import TerminalTitle from "@/components/TerminalTitle";
import DeveloperSignature from "@/components/DeveloperSignature";
import { ArrowRight, Languages, Brain, Zap, Shield, FileText, Eye } from "lucide-react";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#0b0d14] px-4 text-[#eef0f5] sm:px-6">
      <div className="mx-auto max-w-7xl pb-24 pt-32 lg:px-8">
        
        {/* Hero Section */}
        <div className="mb-16 space-y-8 text-center">
          <TerminalTitle />
          
          <div className="inline-flex items-center gap-2 rounded-md border border-cyan-300/20 bg-cyan-300/10 px-3 py-1.5">
            <Zap className="h-4 w-4 text-cyan-300" />
            <span className="text-sm font-medium text-cyan-200">
              Now powered by Sarvam AI - Native Indian Language Translation
            </span>
          </div>
          
          <p className="mx-auto max-w-3xl text-xl leading-7 text-[#a3a9b8]">
            AI-powered PDF translation and visualization for{" "}
            <span className="font-medium text-cyan-200">Gujarati, Hindi, Marathi and English</span>
          </p>

          <div className="flex justify-center">
            <DeveloperSignature variant="hero" />
          </div>

          {/* Main CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
            <Link
              href="/convert"
              className="group inline-flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-300 px-8 py-4 font-medium text-slate-950 transition-colors hover:bg-cyan-200 sm:w-auto"
            >
              <Languages className="w-5 h-5" />
              Translate PDF
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
            </Link>

            <Link
              href="/visualize"
              className="group inline-flex w-full items-center justify-center gap-2 rounded-lg border border-white/15 bg-[#191c24] px-8 py-4 font-medium text-white transition-colors hover:border-cyan-300/40 hover:bg-[#202631] sm:w-auto"
            >
              <Brain className="w-5 h-5" />
              Visualize PDF
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
            </Link>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto mb-16">
          
          {/* Translation Card */}
          <div className="group rounded-2xl border border-white/10 bg-[#11141c] p-8 transition-colors hover:border-cyan-300/35 hover:bg-[#151a23]">
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-cyan-300/10">
              <Languages className="h-7 w-7 text-cyan-300" />
            </div>
            <h3 className="mb-3 text-2xl font-medium text-white">PDF translation</h3>
            <p className="mb-4 leading-7 text-[#a3a9b8]">
              Get a free one-page translation preview to check the accuracy before you pay.
              Full-document translation is powered by <span className="font-medium text-cyan-200">Sarvam AI</span>.
            </p>
            <ul className="space-y-2 text-sm text-[#a3a9b8]">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400"></div>
                Gujarati, Hindi, Marathi and English are currently available
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400"></div>
                Original design, tables, and images are preserved for text-based PDFs
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400"></div>
                1 page free to review accuracy — pay only to unlock the remaining pages
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-green-400"></div>
                <span className="font-medium text-emerald-300">Secure payment unlocks full-document translation</span>
              </li>
            </ul>
            <Link
              href="/convert"
              className="mt-6 inline-flex items-center gap-2 font-medium text-cyan-200 transition-colors hover:text-cyan-100"
            >
              Start Translating
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Visualization Card */}
          <div className="group rounded-2xl border border-white/10 bg-[#11141c] p-8 transition-colors hover:border-cyan-300/35 hover:bg-[#151a23]">
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-xl bg-cyan-300/10">
              <Brain className="h-7 w-7 text-cyan-300" />
            </div>
            <h3 className="mb-3 text-2xl font-medium text-white">PDF visualization</h3>
            <p className="mb-4 leading-7 text-[#a3a9b8]">
              Transform English PDFs into visual data structures using Google Gemini. Perfect for understanding complex documents, research papers, and reports.
            </p>
            <ul className="space-y-2 text-sm text-[#a3a9b8]">
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-cyan-300"></div>
                Up to 20 pages
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400"></div>
                Concept maps & relationships
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400"></div>
                FREE (English PDFs only)
              </li>
            </ul>
            <Link
              href="/visualize"
              className="mt-6 inline-flex items-center gap-2 font-medium text-cyan-200 transition-colors hover:text-cyan-100"
            >
              Start Visualizing
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* New Section: Translation Engine */}
        <div className="max-w-5xl mx-auto mb-16">
          <div className="rounded-2xl border border-white/10 bg-[#11141c] p-8">
            <div className="text-center mb-8">
              <h2 className="mb-3 text-3xl font-medium text-white">
                Powered by Sarvam AI
              </h2>
              <p className="mx-auto max-w-2xl text-[#a3a9b8]">
                We use Sarvam AI&apos;s translation model for authentic Indian-language translation.
              </p>
            </div>
            
            <div className="max-w-md mx-auto">
              <div className="rounded-lg border border-white/10 bg-[#191c24] p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-300/10">
                    <Zap className="h-5 w-5 text-cyan-300" />
                  </div>
                  <h3 className="font-medium text-white">Sarvam AI</h3>
                </div>
                <ul className="space-y-2 text-sm text-gray-300">
                  <li>• Native speaker quality</li>
                  <li>• Gujarati, Hindi, Marathi and English</li>
                  <li>• Cultural context aware</li>
                  <li>• ₹0.003 per page (~99% savings)</li>
                </ul>
              </div>
              
            </div>
          </div>
        </div>

        {/* How It Works */}
        <div className="max-w-5xl mx-auto mb-16">
          <h2 className="mb-12 text-center text-3xl font-medium text-white">
            How it works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center space-y-4">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-cyan-300/10">
                <FileText className="h-8 w-8 text-cyan-300" />
              </div>
              <h3 className="text-xl font-semibold text-white">1. Upload PDF</h3>
              <p className="text-gray-400 text-sm">
                Select your PDF file. We support both text and scanned image-based PDFs with OCR.
              </p>
            </div>
            
            <div className="text-center space-y-4">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-cyan-300/10">
                <Zap className="h-8 w-8 text-cyan-300" />
              </div>
              <h3 className="text-xl font-semibold text-white">2. AI Processing</h3>
              <p className="text-gray-400 text-sm">
                Sarvam AI translates your content with native speaker quality and cultural awareness.
              </p>
            </div>
            
            <div className="text-center space-y-4">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-300/10">
                <Eye className="h-8 w-8 text-emerald-300" />
              </div>
              <h3 className="text-xl font-semibold text-white">3. Download Result</h3>
              <p className="text-gray-400 text-sm">
                Get your translated PDF instantly with preserved formatting and layout.
              </p>
            </div>
          </div>
        </div>

        {/* Benefits */}
        <div className="max-w-5xl mx-auto mb-16">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="rounded-xl border border-white/10 bg-[#191c24] p-6 text-center">
              <Zap className="w-10 h-10 text-yellow-400 mx-auto mb-3" />
              <h4 className="font-semibold text-white mb-2">Lightning Fast</h4>
              <p className="text-sm text-gray-400">
                Process documents in minutes with optimized AI
              </p>
            </div>
            
            <div className="rounded-xl border border-white/10 bg-[#191c24] p-6 text-center">
              <Shield className="w-10 h-10 text-green-400 mx-auto mb-3" />
              <h4 className="font-semibold text-white mb-2">Secure & Private</h4>
              <p className="text-sm text-gray-400">
                Files auto-deleted after processing
              </p>
            </div>
            
            <div className="rounded-xl border border-white/10 bg-[#191c24] p-6 text-center">
              <Languages className="w-10 h-10 text-cyan-400 mx-auto mb-3" />
              <h4 className="font-semibold text-white mb-2">4 Languages Available</h4>
              <p className="text-sm text-gray-400">
                More Indian languages are being added after quality testing
              </p>
            </div>
            
            <div className="rounded-xl border border-white/10 bg-[#191c24] p-6 text-center">
              <Brain className="w-10 h-10 text-purple-400 mx-auto mb-3" />
              <h4 className="font-semibold text-white mb-2">AI-Powered</h4>
              <p className="text-sm text-gray-400">
                Sarvam for translation/OCR; Gemini for visualization only
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center space-y-6">
          <h2 className="text-3xl font-medium text-white">
            Ready to get started?
          </h2>
          <p className="mx-auto max-w-2xl text-[#a3a9b8]">
            Choose your service below and experience the power of AI-driven document processing
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/convert"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-300 px-8 py-4 font-medium text-slate-950 transition-colors hover:bg-cyan-200"
            >
              <Languages className="w-5 h-5" />
              Translate Now
            </Link>
            <Link
              href="/visualize"
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/15 bg-[#191c24] px-8 py-4 font-medium text-white transition-colors hover:border-cyan-300/40 hover:bg-[#202631]"
            >
              <Brain className="w-5 h-5" />
              Visualize Now
            </Link>
          </div>
        </div>

      </div>
    </main>
  );
}
