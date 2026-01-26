import { Github, Linkedin, Globe, Mail } from "lucide-react";

export default function ContactPage() {
  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">

      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[700px] h-[700px] bg-cyan-500/15 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      <div className="relative max-w-3xl mx-auto pt-28 pb-24 space-y-12">

        {/* Header */}
        <header className="text-center space-y-4">
          <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
            Let's Connect
          </h1>
          <p className="text-gray-400 leading-relaxed max-w-2xl mx-auto">
            This tool is designed for accuracy, clarity, and real-world use. Feedback, questions, and collaboration ideas are always welcome.
          </p>
        </header>

        {/* Purpose */}
        <section className="rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 shadow-xl p-8 space-y-4 text-gray-300">
          <h2 className="text-lg font-semibold text-white">Get in Touch</h2>
          <p className="leading-relaxed">
            If you're using this tool for academic work, government documents, or research and have suggestions for improvement, feel free to reach out.
          </p>
          <p className="leading-relaxed">
            You can also contact me regarding feature requests, translation quality feedback, or potential collaboration around document AI systems.
          </p>
        </section>

        {/* Contact Methods */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-white text-center">Ways to Connect</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <ContactCard
              icon={<Mail size={20} />}
              label="Email"
              value="Reach out for feedback or questions"
              href="mailto:hemantsolanki@example.com"
            />

            <ContactCard
              icon={<Linkedin size={20} />}
              label="LinkedIn"
              value="Professional updates and discussions"
              href="https://www.linkedin.com/in/hemant-solanki-366462199/"
            />

            <ContactCard
              icon={<Github size={20} />}
              label="GitHub"
              value="Source code and technical work"
              href="https://github.com/earlywinter96"
            />

            <ContactCard
              icon={<Globe size={20} />}
              label="Portfolio"
              value="Projects, background, and experience"
              href="https://my-portfolio2-peach-six.vercel.app/"
            />
          </div>
        </section>

        {/* Footer */}
        <footer className="text-center text-sm text-gray-500 border-t border-white/10 pt-6">
          This tool is continuously improving. Thoughtful feedback helps make it more accurate, reliable, and useful for everyone.
        </footer>

      </div>
    </main>
  );
}

function ContactCard({ icon, label, value, href }: {
  icon: React.ReactNode;
  label: string;
  value: string;
  href: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-start gap-4 p-5 rounded-xl
        bg-white/5 border border-white/10
        hover:bg-white/10 hover:border-cyan-500/30 transition"
    >
      <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition">
        {icon}
      </div>
      <div className="space-y-1">
        <div className="text-sm font-semibold text-white">
          {label}
        </div>
        <div className="text-xs text-gray-400">
          {value}
        </div>
      </div>
    </a>
  );
}