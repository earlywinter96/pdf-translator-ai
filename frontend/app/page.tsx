// app/page.tsx
/**
 * Homepage - Updated for Sarvam AI
 */

import Link from "next/link";
import TerminalTitle from "@/components/TerminalTitle";
import DeveloperSignature from "@/components/DeveloperSignature";
import { ArrowRight, Languages, Brain, Zap, Shield, FileText, Eye, Sparkles } from "lucide-react";

export default function HomePage() {
  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] via-[#0c1838] to-[#020617] overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl -top-48 -left-48 animate-pulse"></div>
        <div className="absolute w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -bottom-48 -right-48 animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-24">
        
        {/* Hero Section */}
        <div className="text-center space-y-8 mb-16">
          <TerminalTitle />
          
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-cyan-500/10 to-indigo-500/10 border border-cyan-500/20 backdrop-blur-sm">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span className="text-sm text-cyan-300 font-medium">
              Now powered by Sarvam AI - Native Indian Language Translation
            </span>
          </div>
          
          <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            AI-powered PDF translation and visualization for{" "}
            <span className="text-cyan-400 font-semibold">Gujarati, Hindi, Marathi and English</span>
          </p>

          <div className="flex justify-center">
            <DeveloperSignature variant="hero" />
          </div>

          {/* Main CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
            <Link
              href="/convert"
              className="group px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-semibold transition shadow-lg hover:shadow-cyan-500/25 flex items-center gap-2 w-full sm:w-auto justify-center"
            >
              <Languages className="w-5 h-5" />
              Translate PDF
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
            </Link>

            <Link
              href="/visualize"
              className="group px-8 py-4 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold transition shadow-lg hover:shadow-purple-500/25 flex items-center gap-2 w-full sm:w-auto justify-center"
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
          <div className="group rounded-2xl bg-gradient-to-br from-indigo-500/10 to-cyan-500/10 border border-indigo-500/20 p-8 hover:border-cyan-500/40 transition backdrop-blur-sm">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition">
              <Languages className="w-7 h-7 text-cyan-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">PDF Translation</h3>
            <p className="text-gray-400 mb-4 leading-relaxed">
              Get a free one-page translation preview to check the accuracy before you pay.
              Full-document translation is powered by <span className="text-cyan-400 font-semibold">Sarvam AI</span>.
            </p>
            <ul className="space-y-2 text-sm text-gray-300">
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
                <span className="text-green-400 font-medium">Secure payment unlocks full-document translation</span>
              </li>
            </ul>
            <Link
              href="/convert"
              className="inline-flex items-center gap-2 mt-6 text-cyan-400 hover:text-cyan-300 font-medium transition"
            >
              Start Translating
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Visualization Card */}
          <div className="group rounded-2xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 p-8 hover:border-pink-500/40 transition backdrop-blur-sm">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition">
              <Brain className="w-7 h-7 text-purple-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">PDF Visualization</h3>
            <p className="text-gray-400 mb-4 leading-relaxed">
              Transform English PDFs into visual data structures using Google Gemini. Perfect for understanding complex documents, research papers, and reports.
            </p>
            <ul className="space-y-2 text-sm text-gray-300">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400"></div>
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
              className="inline-flex items-center gap-2 mt-6 text-purple-400 hover:text-purple-300 font-medium transition"
            >
              Start Visualizing
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* New Section: Translation Engine */}
        <div className="max-w-5xl mx-auto mb-16">
          <div className="rounded-2xl bg-gradient-to-br from-cyan-500/5 to-indigo-500/5 border border-cyan-500/20 p-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-white mb-3">
                Powered by Sarvam AI
              </h2>
              <p className="text-gray-400 max-w-2xl mx-auto">
                We use Sarvam AI&apos;s translation model for authentic Indian-language translation.
              </p>
            </div>
            
            <div className="max-w-md mx-auto">
              <div className="bg-white/5 rounded-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                    <Zap className="w-5 h-5 text-cyan-400" />
                  </div>
                  <h3 className="font-semibold text-white">Sarvam AI</h3>
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
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 flex items-center justify-center mx-auto">
                <FileText className="w-8 h-8 text-cyan-400" />
              </div>
              <h3 className="text-xl font-semibold text-white">1. Upload PDF</h3>
              <p className="text-gray-400 text-sm">
                Select your PDF file. We support both text and scanned image-based PDFs with OCR.
              </p>
            </div>
            
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center mx-auto">
                <Zap className="w-8 h-8 text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold text-white">2. AI Processing</h3>
              <p className="text-gray-400 text-sm">
                Sarvam AI translates your content with native speaker quality and cultural awareness.
              </p>
            </div>
            
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-green-500/20 to-emerald-500/20 flex items-center justify-center mx-auto">
                <Eye className="w-8 h-8 text-green-400" />
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
            <div className="rounded-xl bg-white/5 border border-white/10 p-6 text-center">
              <Zap className="w-10 h-10 text-yellow-400 mx-auto mb-3" />
              <h4 className="font-semibold text-white mb-2">Lightning Fast</h4>
              <p className="text-sm text-gray-400">
                Process documents in minutes with optimized AI
              </p>
            </div>
            
            <div className="rounded-xl bg-white/5 border border-white/10 p-6 text-center">
              <Shield className="w-10 h-10 text-green-400 mx-auto mb-3" />
              <h4 className="font-semibold text-white mb-2">Secure & Private</h4>
              <p className="text-sm text-gray-400">
                Files auto-deleted after processing
              </p>
            </div>
            
            <div className="rounded-xl bg-white/5 border border-white/10 p-6 text-center">
              <Languages className="w-10 h-10 text-cyan-400 mx-auto mb-3" />
              <h4 className="font-semibold text-white mb-2">4 Languages Available</h4>
              <p className="text-sm text-gray-400">
                More Indian languages are being added after quality testing
              </p>
            </div>
            
            <div className="rounded-xl bg-white/5 border border-white/10 p-6 text-center">
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
          <h2 className="text-3xl font-bold text-white">
            Ready to Get Started?
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Choose your service below and experience the power of AI-driven document processing
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/convert"
              className="px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-semibold transition shadow-lg flex items-center gap-2 justify-center"
            >
              <Languages className="w-5 h-5" />
              Translate Now
            </Link>
            <Link
              href="/visualize"
              className="px-8 py-4 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold transition shadow-lg flex items-center gap-2 justify-center"
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
