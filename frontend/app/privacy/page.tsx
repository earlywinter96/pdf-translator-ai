export default function PrivacyPage() {
    return (
      <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">
  
        {/* Background glow */}
        <div className="pointer-events-none absolute inset-0 flex justify-center">
          <div className="w-[700px] h-[700px] bg-cyan-500/15 blur-[150px] rounded-full -translate-y-1/3" />
        </div>
  
        <div className="relative max-w-3xl mx-auto pt-28 pb-24 space-y-10 text-gray-300">
  
          <header className="space-y-3 text-center">
            <h1 className="text-2xl font-medium text-white tracking-tight">
              Privacy Policy
            </h1>
            <p className="text-gray-400">
              How your documents are handled and protected
            </p>
          </header>
  
          <section className="space-y-6 leading-relaxed text-sm sm:text-base">
            <p>
              This tool is designed with document privacy as a core principle.
              Uploaded PDFs are processed only for the purpose of translation
              and are not retained beyond the processing window.
            </p>
  
            <p>
              Files are stored temporarily during translation and are
              automatically deleted after processing completes. Translated
              outputs are generated for immediate download only.
            </p>
  
            <p>
              We do not analyze, reuse, or share uploaded documents. Content
              is not used for training AI models, analytics, or third-party
              services beyond the translation process itself.
            </p>
  
            <p>
              Translations are generated using third-party AI language models.
              No document data is permanently stored by this service.
            </p>
          </section>
  
          <footer className="border-t border-white/10 pt-6 text-sm text-gray-400 text-center">
            If you have questions regarding privacy, please contact us.
          </footer>
  
        </div>
      </main>
    );
  }
  