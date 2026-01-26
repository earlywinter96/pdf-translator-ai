"use client";

import { useState, useEffect } from "react";
import { FileText, Zap, Globe, CheckCircle, ArrowRight, Shield, Clock, Languages } from "lucide-react";

import { ReactNode } from "react";

// TerminalTitle Component with typing effect
function TerminalTitle() {
  const TEXT = "< AI PDF Translator >";
  const [displayed, setDisplayed] = useState("");
  const [showCursor, setShowCursor] = useState(true);

  // Typing effect
  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      setDisplayed(TEXT.slice(0, index + 1));
      index++;

      if (index === TEXT.length) {
        clearInterval(interval);
      }
    }, 60);

    return () => clearInterval(interval);
  }, []);

  // Cursor blink
  useEffect(() => {
    const cursorInterval = setInterval(() => {
      setShowCursor((prev) => !prev);
    }, 500);

    return () => clearInterval(cursorInterval);
  }, []);

  return (
    <h1 className="
      text-xl            
      sm:text-2xl
      md:text-4xl        
      lg:text-5xl
      font-mono
      font-semibold
      tracking-tight
      text-white
      flex justify-center items-center
      drop-shadow-[0_0_14px_rgba(56,189,248,0.35)]
      whitespace-nowrap
    ">
      {displayed}
      <span className={`ml-1 ${showCursor ? "opacity-100" : "opacity-0"}`}>
        _
      </span>
    </h1>
  );
}

export default function ImprovedHomepage() {
  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black overflow-hidden">
      
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[720px] h-[720px] bg-cyan-500/20 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      <div className="relative max-w-6xl mx-auto px-6 pt-24 pb-20">

        {/* HERO SECTION */}
        <div className="text-center space-y-8 mb-20">
          
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20">
            <Zap className="w-3 h-3 text-cyan-400" />
            <span className="text-xs text-cyan-300">Free • No sign-up required • Privacy-first</span>
          </div>

          {/* Terminal Title with typing effect */}
          <TerminalTitle />

          {/* Subtitle */}
          <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
            AI-powered OCR translation for{" "}
            <span className="text-white font-medium">Gujarati, Hindi, and Marathi</span> PDFs.
            Perfect for government documents, textbooks, and certificates.
          </p>

          {/* CTA Button */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
            <a
              href="/convert"
              className="group px-8 py-4 rounded-lg text-white font-medium text-lg
                bg-gradient-to-r from-indigo-600 to-cyan-600
                hover:from-indigo-500 hover:to-cyan-500
                transition shadow-lg flex items-center gap-2"
            >
              Start Free Translation
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
            </a>
          </div>

          {/* Trust Indicators */}
          <div className="flex flex-wrap justify-center gap-6 md:gap-8 pt-8 text-sm">
            <TrustBadge icon={<Clock />} text="2-3 min average" />
            <TrustBadge icon={<FileText />} text="Up to 400 pages" />
            <TrustBadge icon={<Shield />} text="Files auto-deleted" />
            <TrustBadge icon={<Languages />} text="3 languages" />
          </div>
        </div>

        {/* FEATURES GRID */}
        <div className="mb-20">
          <h2 className="text-2xl md:text-3xl font-semibold text-white text-center mb-3">
            Everything You Need
          </h2>
          <p className="text-gray-400 text-center mb-10 max-w-2xl mx-auto">
            Built specifically for Indian language documents with advanced AI and OCR technology
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              icon={<FileText className="w-6 h-6" />}
              title="OCR + AI Translation"
              description="Accurately extracts and translates text from scanned government and textbook PDFs. Works with both digital and scanned documents."
              highlight="Scanned PDFs ✓"
            />
            <FeatureCard
              icon={<Globe className="w-6 h-6" />}
              title="Indian Language Focus"
              description="Optimized specifically for Gujarati, Hindi, and Marathi documents with cultural context and regional terminology."
              highlight="3 Languages"
            />
            <FeatureCard
              icon={<Zap className="w-6 h-6" />}
              title="Large PDFs Supported"
              description="Handles long PDFs (300-400 pages) with reliable progress tracking and batch processing. No size limits."
              highlight="300+ Pages"
            />
          </div>
        </div>

        {/* HOW IT WORKS */}
        <div className="mb-20">
          <h2 className="text-2xl md:text-3xl font-semibold text-white text-center mb-3">
            Simple 3-Step Process
          </h2>
          <p className="text-gray-400 text-center mb-10">
            Translation made easy - no technical knowledge required
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <ProcessStep
              number="1"
              title="Upload PDF"
              description="Drag & drop your Gujarati, Hindi, or Marathi PDF. Supports both scanned and text-based files up to 25MB."
            />
            <ProcessStep
              number="2"
              title="AI Processing"
              description="Our AI extracts text using OCR and translates while preserving formatting, structure, and context. Takes 2-3 minutes."
            />
            <ProcessStep
              number="3"
              title="Download Result"
              description="Get your translated English PDF. Review side-by-side with original. Files are automatically deleted after download."
            />
          </div>
        </div>

        {/* USE CASES */}
        <div className="mb-20">
          <h2 className="text-2xl md:text-3xl font-semibold text-white text-center mb-3">
            Perfect For
          </h2>
          <p className="text-gray-400 text-center mb-10">
            Trusted by students, professionals, and organizations across India
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
            <UseCase emoji="🏛️" text="Government Documents & Certificates" />
            <UseCase emoji="📚" text="Educational Textbooks & Study Material" />
            <UseCase emoji="⚖️" text="Legal & Compliance Documents" />
            <UseCase emoji="🏥" text="Healthcare & Medical Records" />
            <UseCase emoji="💼" text="Business & Financial Reports" />
            <UseCase emoji="📰" text="News Articles & Publications" />
          </div>
        </div>

        {/* LANGUAGE SUPPORT DETAIL */}
        <div className="mb-20">
          <div className="max-w-4xl mx-auto rounded-2xl bg-white/5 border border-white/10 p-8 md:p-12">
            <h2 className="text-2xl md:text-3xl font-semibold text-white text-center mb-6">
              Supported Languages
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
              <LanguageCard
                language="Gujarati"
                native="ગુજરાતી"
                details="Government docs, NCERT textbooks"
              />
              <LanguageCard
                language="Hindi"
                native="हिन्दी"
                details="Most widely requested"
              />
              <LanguageCard
                language="Marathi"
                native="मराठी"
                details="Regional government forms"
              />
            </div>
            <p className="text-center text-sm text-gray-500 mt-8">
              More Indian languages coming soon. Request your language in feedback.
            </p>
          </div>
        </div>

        {/* TRANSLATION MODES */}
        <div className="mb-20">
          <h2 className="text-2xl md:text-3xl font-semibold text-white text-center mb-10">
            Choose Your Translation Mode
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <ModeCard
              title="General Translation"
              description="Best for everyday documents, personal letters, articles, and general content"
              features={["Fast processing", "Natural language", "Everyday vocabulary"]}
              recommended="Letters, articles, personal docs"
            />
            <ModeCard
              title="Government / NCERT"
              description="Specialized for official documents with formal terminology and technical accuracy"
              features={["Formal language", "Technical terms", "Official formatting"]}
              recommended="Govt docs, certificates, textbooks"
            />
          </div>
        </div>

        {/* WHY CHOOSE US */}
        <div className="mb-20">
          <h2 className="text-2xl md:text-3xl font-semibold text-white text-center mb-10">
            Why Choose Our Translator?
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <BenefitCard
              icon="🔒"
              title="100% Private"
              text="Files auto-deleted after translation"
            />
            <BenefitCard
              icon="⚡"
              title="Lightning Fast"
              text="Results in 2-3 minutes"
            />
            <BenefitCard
              icon="🎯"
              title="High Accuracy"
              text="AI-powered precision"
            />
            <BenefitCard
              icon="💰"
              title="Free Forever"
              text="No hidden charges"
            />
          </div>
        </div>

        {/* FAQ PREVIEW */}
        <div className="mb-20">
          <h2 className="text-2xl md:text-3xl font-semibold text-white text-center mb-10">
            Common Questions
          </h2>
          
          <div className="max-w-3xl mx-auto space-y-4">
            <FAQItem
              question="What file types are supported?"
              answer="We currently support PDF files only (both scanned and text-based). Maximum file size is 25MB."
            />
            <FAQItem
              question="How accurate is the translation?"
              answer="Our AI achieves 95%+ accuracy for printed text. Handwritten content may have lower accuracy depending on clarity."
            />
            <FAQItem
              question="Is my data safe?"
              answer="Yes! Files are processed temporarily and automatically deleted after download. We never store your documents."
            />
            <FAQItem
              question="How long does translation take?"
              answer="Average processing time is 2-3 minutes for typical documents. Larger PDFs (300+ pages) may take longer."
            />
          </div>
        </div>

        {/* FINAL CTA */}
        <div className="text-center space-y-6 py-12 px-6 rounded-2xl bg-gradient-to-r from-indigo-600/10 to-cyan-600/10 border border-white/10">
          <h2 className="text-2xl md:text-4xl font-bold text-white">
            Ready to Translate Your PDFs?
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto text-lg">
            Join users translating important documents every day. 
            <br />
            No account needed. Start in seconds.
          </p>
          <a
            href="/convert"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-lg text-white font-medium text-lg
              bg-gradient-to-r from-indigo-600 to-cyan-600
              hover:from-indigo-500 hover:to-cyan-500
              transition shadow-lg"
          >
            Translate Now - It's Free
            <ArrowRight className="w-5 h-5" />
          </a>
          <p className="text-sm text-gray-500 pt-2">
            ✓ No registration required  ✓ Files auto-deleted  ✓ Free forever
          </p>
        </div>

        {/* Built by */}
        <div className="pt-12 text-center text-sm text-gray-500">
          Built with ❤️ by{" "}
          <a 
            href="https://my-portfolio2-peach-six.vercel.app/" 
            target="_blank"
            className="text-gray-300 font-medium hover:text-cyan-400 transition"
          >
            Hemant Solanki
          </a>
        </div>

      </div>
    </main>
  );
}

type TrustBadgeProps = {
  icon: ReactNode;
  text: string;
};

function TrustBadge({ icon, text }: TrustBadgeProps) {
  return (
    <div className="flex items-center gap-2 text-gray-300">
      <div className="w-5 h-5 text-green-400">{icon}</div>
      <span className="text-sm">{text}</span>
    </div>
  );
}


type FeatureCardProps = {
  icon: ReactNode;
  title: string;
  description: string;
  highlight: string;
};

function FeatureCard({
  icon,
  title,
  description,
  highlight,
}: FeatureCardProps) {
  return (
    <div className="relative group rounded-xl bg-white/5 border border-white/10 p-6 hover:bg-white/10 transition">
      <div className="absolute -top-3 -right-3 px-3 py-1 rounded-full bg-cyan-500/20 border border-cyan-500/30 text-xs text-cyan-300 font-medium">
        {highlight}
      </div>

      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 flex items-center justify-center text-cyan-400 mb-4 group-hover:scale-110 transition">
        {icon}
      </div>

      <h3 className="text-white font-semibold mb-2 text-lg">{title}</h3>
      <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
    </div>
  );
}


type ProcessStepProps = {
  number: string;
  title: string;
  description: string;
};

function ProcessStep({ number, title, description }: ProcessStepProps) {
  return (
    <div className="relative">
      {number !== "3" && (
        <div className="hidden md:block absolute top-8 left-[calc(50%+2rem)] w-[calc(100%-4rem)] h-[2px] bg-gradient-to-r from-cyan-500/30 to-transparent" />
      )}

      <div className="relative text-center space-y-3">
        <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center text-white text-2xl font-bold shadow-lg">
          {number}
        </div>
        <h3 className="text-white font-semibold text-lg">{title}</h3>
        <p className="text-gray-400 text-sm leading-relaxed max-w-xs mx-auto">
          {description}
        </p>
      </div>
    </div>
  );
}


type UseCaseProps = {
  emoji: string;
  text: string;
};

function UseCase({ emoji, text }: UseCaseProps) {
  return (
    <div className="flex items-center gap-3 px-5 py-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 hover:border-cyan-500/30 transition group">
      <span className="text-2xl group-hover:scale-110 transition">
        {emoji}
      </span>
      <span className="text-gray-300 text-sm font-medium">{text}</span>
    </div>
  );
}


type LanguageCardProps = {
  language: string;
  native: string;
  details: string;
};

function LanguageCard({ language, native, details }: LanguageCardProps) {
  return (
    <div className="space-y-2">
      <div className="text-3xl font-bold text-white">{language}</div>
      <div className="text-xl text-cyan-400">{native}</div>
      <div className="text-xs text-gray-500">{details}</div>
    </div>
  );
}


type ModeCardProps = {
  title: string;
  description: string;
  features: string[];
  recommended: string;
};

function ModeCard({
  title,
  description,
  features,
  recommended,
}: ModeCardProps) {
  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-6 hover:border-cyan-500/30 transition">
      <h3 className="text-white font-semibold text-lg mb-2">{title}</h3>
      <p className="text-gray-400 text-sm mb-4">{description}</p>

      <div className="space-y-2 mb-4">
        {features.map((feature, i) => (
          <div key={i} className="flex items-center gap-2 text-sm text-gray-300">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span>{feature}</span>
          </div>
        ))}
      </div>

      <div className="pt-3 border-t border-white/10">
        <p className="text-xs text-gray-500">
          Best for: <span className="text-cyan-400">{recommended}</span>
        </p>
      </div>
    </div>
  );
}


type BenefitCardProps = {
  icon: ReactNode;
  title: string;
  text: string;
};

function BenefitCard({ icon, title, text }: BenefitCardProps) {
  return (
    <div className="text-center p-6 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-white font-semibold mb-1">{title}</h3>
      <p className="text-gray-400 text-sm">{text}</p>
    </div>
  );
}


type FAQItemProps = {
  question: string;
  answer: string;
};

function FAQItem({ question, answer }: FAQItemProps) {
  return (
    <details className="group rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition">
      <summary className="cursor-pointer p-4 text-white font-medium flex justify-between items-center">
        {question}
        <span className="text-cyan-400 group-open:rotate-180 transition">
          ▼
        </span>
      </summary>
      <div className="px-4 pb-4 text-gray-400 text-sm leading-relaxed">
        {answer}
      </div>
    </details>
  );
}
