import { Github, Linkedin, Globe, Mail } from "lucide-react";

export default function ContactPage() {
  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black px-6 overflow-hidden">

      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[700px] h-[700px] bg-cyan-500/15 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      <div className="relative max-w-3xl mx-auto pt-28 pb-24 space-y-14">

        {/* Title */}
        <header className="space-y-4 text-center">
          <h1 className="text-2xl font-medium text-white tracking-tight">
            <b> Let's Connect </b>
          </h1>
          <p className="text-gray-400 leading-relaxed">
            This tool is designed for accuracy, clarity, and real-world use.
            Feedback, questions, and collaboration ideas are always welcome.
          </p>
        </header>

        {/* Contact Purpose */}
        <section className="space-y-6 text-gray-300 leading-relaxed">
          <p>
            If you are using this tool for academic work, government material,
            or research documents and have suggestions for improvement,
            feel free to reach out.
          </p>

          <p>
            You can also contact me regarding feature requests, translation
            quality feedback, or potential collaboration around document AI
            systems.
          </p>
        </section>

        {/* Contact Methods */}
        <section className="rounded-2xl bg-white/5 backdrop-blur-md
          border border-white/10 shadow-xl p-8 space-y-6">

          <h2 className="text-base font-medium text-gray-200">
            Ways to connect
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

            <ContactItem
              icon={<Mail size={18} />}
              label="Email"
              value="Reach out for feedback or questions"
              href="mailto:your-email@example.com"
            />

            <ContactItem
              icon={<Linkedin size={18} />}
              label="LinkedIn"
              value="Professional updates and discussions"
              href="https://www.linkedin.com/in/hemant-solanki-366462199/"
            />

            <ContactItem
              icon={<Github size={18} />}
              label="GitHub"
              value="Source code and technical work"
              href="https://github.com/earlywinter96"
            />

            <ContactItem
              icon={<Globe size={18} />}
              label="Portfolio"
              value="Projects, background, and experience"
              href="https://my-portfolio-ten-sable-21.vercel.app/"
            />
          </div>
        </section>

        {/* Closing note */}
        <footer className="text-sm text-gray-500 border-t border-white/10 pt-6">
          This tool is continuously improving. Thoughtful feedback helps
          make it more accurate, reliable, and useful for everyone.
        </footer>

      </div>
    </main>
  );
}

function ContactItem({
  icon,
  label,
  value,
  href,
}: {
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
      className="flex items-start gap-3 p-4 rounded-xl
        bg-white/5 border border-white/10
        hover:bg-white/10 transition"
    >
      <div className="text-cyan-400 mt-0.5">
        {icon}
      </div>
      <div className="space-y-1">
        <div className="text-sm font-medium text-gray-200">
          {label}
        </div>
        <div className="text-xs text-gray-400">
          {value}
        </div>
      </div>
    </a>
  );
}
