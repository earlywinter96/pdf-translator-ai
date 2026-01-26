export default function TermsPage() {
  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">

      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[700px] h-[700px] bg-indigo-500/15 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      <div className="relative max-w-3xl mx-auto pt-28 pb-24 space-y-10">

        {/* Header */}
        <header className="text-center space-y-3">
          <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
            Terms of Use
          </h1>
          <p className="text-gray-400">
            Conditions for using this AI translation tool
          </p>
        </header>

        {/* Content */}
        <section className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 shadow-xl p-8 md:p-10 space-y-6 text-gray-300 leading-relaxed">
          
          <div>
            <h2 className="text-lg font-semibold text-white mb-3">Service Purpose</h2>
            <p>
              This tool is provided to assist with document translation. While care is taken to preserve meaning and structure, translated output may vary depending on document quality and language complexity.
            </p>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-white mb-3">Content Ownership</h2>
            <p>
              Users retain full ownership of uploaded documents and all translated outputs. This service does not claim ownership over any content processed through the tool.
            </p>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-white mb-3">User Responsibility</h2>
            <p>
              Users are responsible for ensuring they have the legal right to upload and translate documents, including compliance with applicable copyright laws. Do not upload copyrighted material without permission.
            </p>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-white mb-3">Service Limitations</h2>
            <p>
              This service is provided "as is" and is not intended to replace certified human translation for legal, medical, or official submissions requiring sworn translation.
            </p>
          </div>

          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <p className="text-sm text-yellow-200">
              <strong>⚠️ Disclaimer:</strong> Translation accuracy depends on source document quality, language complexity, and OCR performance. Always verify critical translations with professional translators.
            </p>
          </div>

        </section>

        {/* Footer */}
        <footer className="text-center text-sm text-gray-400 border-t border-white/10 pt-6">
          By using this tool, you agree to these terms • Last updated: January 2026
        </footer>

      </div>
    </main>
  );
}
