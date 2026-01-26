export default function PrivacyPage() {
  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">

      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[700px] h-[700px] bg-cyan-500/15 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      <div className="relative max-w-3xl mx-auto pt-28 pb-24 space-y-10">

        {/* Header */}
        <header className="text-center space-y-3">
          <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
            Privacy Policy
          </h1>
          <p className="text-gray-400">
            How your documents are handled and protected
          </p>
        </header>

        {/* Content */}
        <section className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 shadow-xl p-8 md:p-10 space-y-6 text-gray-300 leading-relaxed">
          
          <div>
            <h2 className="text-lg font-semibold text-white mb-3">Document Processing</h2>
            <p>
              This tool is designed with document privacy as a core principle. Uploaded PDFs are processed only for translation and are not retained beyond the processing window.
            </p>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-white mb-3">Automatic Deletion</h2>
            <p>
              Files are stored temporarily during translation and are automatically deleted after processing completes. Translated outputs are generated for immediate download only.
            </p>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-white mb-3">No Data Reuse</h2>
            <p>
              We do not analyze, reuse, or share uploaded documents. Content is not used for training AI models, analytics, or third-party services beyond the translation process itself.
            </p>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-white mb-3">Third-Party AI</h2>
            <p>
              Translations are generated using third-party AI language models (Google Gemini). No document data is permanently stored by this service. Translation requests are processed in real-time and discarded immediately.
            </p>
          </div>

          <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
            <p className="text-sm text-cyan-200">
              <strong>🔒 Security Note:</strong> All file transfers use encrypted connections. Documents exist only in memory during processing and are never written to permanent storage.
            </p>
          </div>

        </section>

        {/* Footer */}
        <footer className="text-center text-sm text-gray-400 border-t border-white/10 pt-6">
          Last updated: January 2026 • If you have privacy questions, please{" "}
          <a href="/contact" className="text-cyan-400 hover:text-cyan-300 underline">contact us</a>
        </footer>

      </div>
    </main>
  );
}

