export default function TermsPage() {
    return (
      <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">
  
        {/* Background glow */}
        <div className="pointer-events-none absolute inset-0 flex justify-center">
          <div className="w-[700px] h-[700px] bg-indigo-500/15 blur-[150px] rounded-full -translate-y-1/3" />
        </div>
  
        <div className="relative max-w-3xl mx-auto pt-28 pb-24 space-y-10 text-gray-300">
  
          <header className="space-y-3 text-center">
            <h1 className="text-2xl font-medium text-white tracking-tight">
              Terms of Use
            </h1>
            <p className="text-gray-400">
              Conditions for using this AI translation tool
            </p>
          </header>
  
          <section className="space-y-6 leading-relaxed text-sm sm:text-base">
            <p>
              This tool is provided to assist with document translation.
              While care is taken to preserve meaning and structure, translated
              output may vary depending on document quality and language
              complexity.
            </p>
  
            <p>
              Users retain full ownership of uploaded documents and all
              translated outputs. This service does not claim ownership
              over any content processed through the tool.
            </p>
  
            <p>
              Users are responsible for ensuring they have the legal right
              to upload and translate documents, including compliance with
              applicable copyright laws.
            </p>
  
            <p>
              This service is provided “as is” and is not intended to replace
              certified human translation for legal, medical, or official
              submissions.
            </p>
          </section>
  
          <footer className="border-t border-white/10 pt-6 text-sm text-gray-400 text-center">
            By using this tool, you agree to these terms.
          </footer>
  
        </div>
      </main>
    );
  }
  