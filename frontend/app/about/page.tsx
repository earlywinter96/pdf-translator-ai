import Link from "next/link";
import { FileText, Zap, Target, Shield, Languages, CheckCircle2 } from "lucide-react";

export default function AboutPage() {
  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">

      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[700px] h-[700px] bg-cyan-500/15 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      {/* Content */}
      <div className="relative max-w-4xl mx-auto pt-28 pb-24 space-y-12">

        {/* Header */}
        <header className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-4">
            <Zap className="w-3 h-3 text-cyan-400" />
            <span className="text-xs text-cyan-300">AI-Powered Translation</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
            Translation built for Indian documents
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
            LipiTranslate helps students, professionals, and organisations translate PDFs with a clear preview before they pay for the full document.
          </p>
        </header>

        {/* Main content */}
        <section className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 shadow-xl p-8 md:p-10 space-y-6 text-gray-300 leading-relaxed">
          <h2 className="text-2xl font-semibold text-white">Made for documents that matter</h2>
          <p>
            LipiTranslate is designed for the PDFs people actually need to understand: study material, forms, notes, government documents, reports, and professional files. Gujarati, Hindi, Marathi and English translation are currently available; additional Indian languages are being quality-tested for a future release.
          </p>
          <p>
            Every document starts with a <span className="text-cyan-300 font-medium">free one-page preview</span>. You can check the translation quality, language direction, and visual result before choosing to unlock the remaining pages.
          </p>
          <p>
            For text-based PDFs, LipiTranslate keeps the original page as the canvas and replaces the selectable text in place. This helps preserve headings, tables, coloured backgrounds, images, and the document&apos;s overall layout. Scanned PDFs use OCR to read the page first, so results can depend on scan clarity.
          </p>
        </section>

        <section className="grid md:grid-cols-3 gap-5">
          <TrustPoint title="Preview before payment" description="Review a translated first page before paying for a full document." />
          <TrustPoint title="Sarvam AI translation" description="Indian-language translation is powered by Sarvam AI, chosen for this use case." />
          <TrustPoint title="Secure payment flow" description="Full translation starts only after the matching payment is verified on the server." />
        </section>

        {/* Key Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FeatureCard
            icon={<Target className="w-6 h-6" />}
            title="Meaning before decoration"
            description="The service aims to preserve wording, questions, options, and context instead of turning a document into a loose summary."
          />
          <FeatureCard
            icon={<FileText className="w-6 h-6" />}
            title="OCR for scanned PDFs"
            description="When a PDF is an image or scan, OCR extracts its text before translation. A cleaner scan produces a more reliable result."
          />
          <FeatureCard
            icon={<Zap className="w-6 h-6" />}
            title="Layout-aware output"
            description="For digital PDFs, the original visual design is retained where the source text has usable positioning information."
          />
          <FeatureCard
            icon={<Shield className="w-6 h-6" />}
            title="Practical document handling"
            description="Files are processed for the requested translation and made available for download during the processing window."
          />
        </div>

        <section className="rounded-2xl bg-gradient-to-br from-cyan-500/10 to-indigo-500/10 border border-cyan-500/20 p-8 md:p-10 text-center">
          <div className="w-12 h-12 mx-auto rounded-xl bg-cyan-500/15 text-cyan-300 flex items-center justify-center mb-4">
            <Languages className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-semibold text-white">Built by Hemant Solanki</h2>
          <p className="text-gray-300 max-w-2xl mx-auto mt-3 leading-relaxed">
            LipiTranslate was founded by Hemant Solanki to make Indian-language documents easier to access, understand, and share—without forcing users to choose between translation quality and a usable PDF.
          </p>
          <Link href="/convert" className="inline-flex items-center gap-2 mt-6 rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-slate-950 hover:bg-cyan-400 transition">
            Try the free preview <CheckCircle2 className="w-4 h-4" />
          </Link>
        </section>

        {/* Footer */}
        <footer className="text-center text-sm text-gray-500 border-t border-white/10 pt-6">
          Built for clarity. Designed for real-world documents.
        </footer>

      </div>
    </main>
  );
}

function TrustPoint({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-5">
      <p className="text-white font-semibold">{title}</p>
      <p className="text-gray-400 text-sm leading-relaxed mt-2">{description}</p>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-6 hover:bg-white/10 transition space-y-3">
      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 flex items-center justify-center text-cyan-400">
        {icon}
      </div>
      <h3 className="text-white font-semibold">{title}</h3>
      <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
    </div>
  );
}
