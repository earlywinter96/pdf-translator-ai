import { FileText, Zap, Target, Shield } from "lucide-react";

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
            About This Tool
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
            A focused AI system for translating complex PDF documents while preserving meaning, structure, and intent.
          </p>
        </header>

        {/* Main content */}
        <section className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 shadow-xl p-8 md:p-10 space-y-6 text-gray-300 leading-relaxed">
          <p>
            This tool is built to handle multilingual PDFs commonly used in education, government, and academic environments—where accuracy and consistency matter more than stylistic rewriting.
          </p>

          <p>
            It supports both scanned and text-based documents by combining optical character recognition (OCR) with language models trained for long-form content. Pages with existing text are processed directly, while OCR is applied only when necessary.
          </p>

          <p>
            The translation process retains paragraph structure, terminology, and contextual meaning, making the output suitable for study, reference, and professional use.
          </p>

          <p>
            Instead of simplifying content, the system prioritizes fidelity to the source document, ensuring the translated version remains as close as possible to the original.
          </p>
        </section>

        {/* Key Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FeatureCard
            icon={<Target className="w-6 h-6" />}
            title="Accuracy First"
            description="Prioritizes faithful translation over paraphrasing, ensuring technical and academic content remains precise."
          />
          <FeatureCard
            icon={<FileText className="w-6 h-6" />}
            title="OCR When Needed"
            description="Intelligent text extraction only applies OCR to scanned pages, preserving quality and speed."
          />
          <FeatureCard
            icon={<Zap className="w-6 h-6" />}
            title="Context Preservation"
            description="Maintains document structure, formatting, and terminology consistency across hundreds of pages."
          />
          <FeatureCard
            icon={<Shield className="w-6 h-6" />}
            title="Privacy Focused"
            description="Documents are processed temporarily and deleted immediately after translation completes."
          />
        </div>

        {/* Footer */}
        <footer className="text-center text-sm text-gray-500 border-t border-white/10 pt-6">
          Built for clarity. Designed for real-world documents.
        </footer>

      </div>
    </main>
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