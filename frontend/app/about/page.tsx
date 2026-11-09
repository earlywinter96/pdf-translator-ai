import Link from "next/link";
import { FileText, Zap, Target, Shield, Languages, CheckCircle2, Linkedin, Instagram, Globe } from "lucide-react";

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-[#0b0d14] px-6 text-[#eef0f5]">
      <div className="mx-auto max-w-4xl space-y-16 pb-24 pt-28">

        {/* Header */}
        <header className="text-center space-y-4">
          <div className="mb-4 inline-flex items-center gap-2 rounded-md border border-cyan-300/20 bg-cyan-300/10 px-3 py-1.5">
            <Zap className="h-3 w-3 text-cyan-300" />
            <span className="text-xs text-cyan-200">Document translation</span>
          </div>
          <h1 className="text-3xl font-medium tracking-[-0.02em] text-white md:text-4xl">
            Translation built for Indian documents
          </h1>
          <p className="mx-auto max-w-2xl text-lg leading-7 text-[#a3a9b8]">
            LipiTranslate.in helps students, professionals, and organisations translate PDFs with a clear preview before they pay for the full document.
          </p>
        </header>

        {/* Main content */}
        <section className="space-y-6 rounded-2xl border border-white/10 bg-[#11141c] p-8 leading-7 text-[#a3a9b8] md:p-10">
          <h2 className="text-2xl font-medium text-white">Made for documents that matter</h2>
          <p>
            LipiTranslate.in is designed for the PDFs people actually need to understand: study material, forms, notes, government documents, reports, and professional files. Gujarati, Hindi, Marathi and English translation are currently available; additional Indian languages are being quality-tested for a future release.
          </p>
          <p>
            Every document starts with a <span className="text-cyan-300 font-medium">free one-page preview</span>. You can check the translation quality, language direction, and visual result before choosing to unlock the remaining pages.
          </p>
          <p>
            For text-based PDFs, LipiTranslate.in keeps the original page as the canvas and replaces the selectable text in place. This helps preserve headings, tables, coloured backgrounds, images, and the document&apos;s overall layout. Scanned PDFs use OCR to read the page first, so results can depend on scan clarity.
          </p>
        </section>

        <section className="grid gap-5 md:grid-cols-3">
          <TrustPoint title="Preview before payment" description="Review a translated first page before paying for a full document." />
          <TrustPoint title="Sarvam AI translation" description="Indian-language translation is powered by Sarvam AI, chosen for this use case." />
          <TrustPoint title="Secure payment flow" description="Full translation starts only after the matching payment is verified on the server." />
        </section>

        {/* Key Features Grid */}
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
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

        <section className="rounded-2xl border border-cyan-300/20 bg-[#111c25] p-8 text-center md:p-10">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-300/10 text-cyan-300">
            <Languages className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-medium text-white">Built by Hemant Solanki</h2>
          <p className="mx-auto mt-3 max-w-2xl leading-7 text-[#a3a9b8]">
            LipiTranslate.in was founded by Hemant Solanki to make Indian-language documents easier to access, understand, and share—without forcing users to choose between translation quality and a usable PDF.
          </p>
          <div className="flex flex-wrap justify-center gap-3 mt-5">
            <a href="https://www.linkedin.com/in/hemant-solanki-366462199/" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-cyan-300/30 px-4 py-2 text-sm text-cyan-200 transition-colors hover:bg-cyan-300/10">
              <Linkedin className="w-4 h-4" /> Founder LinkedIn
            </a>
            <a href="https://my-portfolio2-peach-six.vercel.app/" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-cyan-300/30 px-4 py-2 text-sm text-cyan-200 transition-colors hover:bg-cyan-300/10">
              <Globe className="w-4 h-4" /> Founder portfolio
            </a>
            <a href="https://www.instagram.com/lipitranslate.in?utm_source=qr&stkn=MTg4YmNheW9xM2ltYg==" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-cyan-300/30 px-4 py-2 text-sm text-cyan-200 transition-colors hover:bg-cyan-300/10">
              <Instagram className="w-4 h-4" /> Instagram
            </a>
          </div>
          <Link href="/convert" className="mt-6 inline-flex items-center gap-2 rounded-lg bg-cyan-300 px-5 py-3 font-medium text-slate-950 transition-colors hover:bg-cyan-200">
            Try the free preview <CheckCircle2 className="h-4 w-4" />
          </Link>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/10 pt-6 text-center text-sm text-[#7a8296]">
          Built for clarity. Designed for real-world documents.
        </footer>

      </div>
    </main>
  );
}

function TrustPoint({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-[#191c24] p-5">
      <p className="font-medium text-white">{title}</p>
      <p className="mt-2 text-sm leading-6 text-[#a3a9b8]">{description}</p>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="space-y-3 rounded-xl border border-white/10 bg-[#191c24] p-6 transition-colors hover:bg-[#202631]">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-300/10 text-cyan-300">
        {icon}
      </div>
      <h3 className="font-medium text-white">{title}</h3>
      <p className="text-sm leading-6 text-[#a3a9b8]">{description}</p>
    </div>
  );
}
