export default function AboutPage() {
    return (
      <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">
  
        {/* Background glow (same as Home / Convert / Contact) */}
        <div className="pointer-events-none absolute inset-0 flex justify-center">
          <div className="w-[700px] h-[700px] bg-cyan-500/15 blur-[150px] rounded-full -translate-y-1/3" />
        </div>
  
        {/* Content */}
        <div className="relative max-w-3xl mx-auto pt-28 pb-24 space-y-14 text-gray-300">
  
          {/* Header */}
          <header className="space-y-4 text-center">
            <h1 className="text-2xl font-medium text-white tracking-tight">
              <b> What it does?  </b>
            </h1>
            <p className="text-gray-400 leading-relaxed">
              A focused AI system for translating complex PDF documents
              while preserving meaning, structure, and intent.
            </p>
          </header>
  
          {/* Main content */}
          <section className="space-y-6 leading-relaxed">
            <p>
              This tool is built to handle multilingual PDFs that are
              commonly used in education, government, and academic
              environments, where accuracy and consistency matter more
              than stylistic rewriting.
            </p>
  
            <p>
              It supports both scanned and text-based documents by
              combining optical character recognition with language
              models trained to work reliably on long-form content.
              Pages that already contain usable text are processed
              directly, while OCR is applied only when necessary.
            </p>
  
            <p>
              The translation process is designed to retain paragraph
              structure, terminology, and contextual meaning, making the
              output suitable for study, reference, and professional use.
            </p>
  
            <p>
              Instead of simplifying or paraphrasing content, the system
              prioritizes fidelity to the source document, ensuring that
              the translated version remains as close as possible to the
              original.
            </p>
          </section>
  
          {/* Key principles */}
          <section className="rounded-2xl bg-white/5 backdrop-blur-md
            border border-white/10 shadow-xl p-8 space-y-4">
  
            <h2 className="text-base font-medium text-gray-200">
              Design principles
            </h2>
  
            <ul className="list-disc list-inside space-y-2 text-sm text-gray-400">
              <li>Accuracy over summarization</li>
              <li>Minimal OCR usage for performance and quality</li>
              <li>Consistent terminology across long documents</li>
              <li>Readable output suitable for academic and official use</li>
            </ul>
          </section>
  
          {/* Footer line */}
          <footer className="text-sm text-gray-500 border-t border-white/10 pt-6 text-center">
            Built for clarity. Designed for real-world documents.
          </footer>
  
        </div>
      </main>
    );
  }
  