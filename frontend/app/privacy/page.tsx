import Link from "next/link";

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[#0b0d14] px-6 text-[#eef0f5]">
      <div className="mx-auto max-w-3xl space-y-10 pb-24 pt-28">

        {/* Header */}
        <header className="text-center space-y-3">
          <h1 className="text-3xl font-medium tracking-[-0.02em] text-white md:text-4xl">
            Privacy Policy
          </h1>
          <p className="text-[#a3a9b8]">
            How your documents are handled and protected
          </p>
        </header>

        {/* Content */}
        <section className="space-y-6 rounded-2xl border border-white/10 bg-[#11141c] p-8 leading-7 text-[#a3a9b8] md:p-10">
          
          <div>
            <h2 className="mb-3 text-lg font-medium text-white">Document processing</h2>
            <p>
              This tool is designed with document privacy as a core principle. Uploaded PDFs are processed only for translation and are not retained beyond the processing window.
            </p>
          </div>

          <div>
            <h2 className="mb-3 text-lg font-medium text-white">Automatic deletion</h2>
            <p>
              Files are stored temporarily during translation and are automatically deleted after processing completes. Translated outputs are generated for immediate download only.
            </p>
          </div>

          <div>
            <h2 className="mb-3 text-lg font-medium text-white">No data reuse</h2>
            <p>
              We do not analyze, reuse, or share uploaded documents. Content is not used for training AI models, analytics, or third-party services beyond the translation process itself.
            </p>
          </div>

          <div>
            <h2 className="mb-3 text-lg font-medium text-white">Third-party AI</h2>
            <p>
              PDF translation and scanned-document OCR use Sarvam AI (Sarvam Translate and Sarvam Vision). Google Gemini is used only when you explicitly choose the separate PDF visualization feature; it is not used to translate PDFs. No document data is permanently stored by this service. Requests are processed in real-time and discarded immediately.
            </p>
          </div>

          <div className="rounded-xl border border-cyan-300/20 bg-[#111c25] p-4">
            <p className="text-sm text-cyan-100">
              <strong className="font-medium text-white">Security note:</strong> All file transfers use encrypted connections. Documents exist only in memory during processing and are never written to permanent storage.
            </p>
          </div>

        </section>

        {/* Footer */}
        <footer className="border-t border-white/10 pt-6 text-center text-sm text-[#7a8296]">
          Last updated: January 2026 • If you have privacy questions, please{" "}
          <Link href="/contact" className="text-cyan-200 underline decoration-cyan-300/50 underline-offset-4 hover:text-cyan-100">contact us</Link>
        </footer>

      </div>
    </main>
  );
}
