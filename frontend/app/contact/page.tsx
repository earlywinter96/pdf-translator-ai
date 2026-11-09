import { Github, Linkedin, Globe, Mail, Instagram, Users, Building2, LifeBuoy, ArrowUpRight } from "lucide-react";

export default function ContactPage() {
  return (
    <main className="min-h-screen bg-[#0b0d14] px-6 text-[#eef0f5]">
      <div className="mx-auto max-w-4xl space-y-16 pb-24 pt-28">

        {/* Header */}
        <header className="text-center space-y-4">
          <h1 className="text-3xl font-medium tracking-[-0.02em] text-white md:text-4xl">
            Let&apos;s Connect
          </h1>
          <p className="mx-auto max-w-2xl leading-7 text-[#a3a9b8]">
            This tool is designed for accuracy, clarity, and real-world use. Feedback, questions, and collaboration ideas are always welcome.
          </p>
        </header>

        {/* Purpose */}
        <section className="space-y-4 rounded-2xl border border-white/10 bg-[#11141c] p-8 text-[#a3a9b8]">
          <h2 className="text-lg font-medium text-white">Get in touch</h2>
          <p className="leading-7">
            If you&apos;re using this tool for academic work, government documents, or research and have suggestions for improvement, feel free to reach out.
          </p>
          <p className="leading-7">
            You can also contact me regarding feature requests, translation quality feedback, or potential collaboration around document AI systems.
          </p>
        </section>

        {/* Contact Methods */}
        <section className="space-y-4">
          <h2 className="text-center text-lg font-medium text-white">Ways to connect</h2>
          <div className="space-y-8">
            <div className="space-y-4 rounded-2xl border border-white/10 bg-[#11141c] p-5 md:p-6">
              <h3 className="flex items-center gap-2 text-sm font-medium text-cyan-300"><Users className="h-4 w-4" /> Founder profiles</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <ContactCard
                  icon={<Linkedin size={20} />}
                  label="Hemant Solanki on LinkedIn"
                  value="Connect with the founder"
                  href="https://www.linkedin.com/in/hemant-solanki-366462199/"
                />
                <ContactCard
                  icon={<Globe size={20} />}
                  label="Hemant Solanki portfolio"
                  value="Projects, background, and experience"
                  href="https://my-portfolio2-peach-six.vercel.app/"
                />
              </div>
            </div>

            <div className="space-y-4 rounded-2xl border border-white/10 bg-[#11141c] p-5 md:p-6">
              <h3 className="flex items-center gap-2 text-sm font-medium text-cyan-300"><Building2 className="h-4 w-4" /> Company profiles</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <ContactCard
                  icon={<Linkedin size={20} />}
                  label="LipiTranslate.in on LinkedIn"
                  value="Product updates and announcements"
                  href="https://www.linkedin.com/company/lipitranslate.in?trk=public_post_follow-view-profile"
                />
                <ContactCard
                  icon={<Instagram size={20} />}
                  label="LipiTranslate.in on Instagram"
                  value="Follow product news and updates"
                  href="https://www.instagram.com/lipitranslate.in?utm_source=qr&stkn=MTg4YmNheW9xM2ltYg=="
                />
              </div>
            </div>

            <div className="space-y-4 rounded-2xl border border-white/10 bg-[#11141c] p-5 md:p-6">
              <h3 className="flex items-center gap-2 text-sm font-medium text-cyan-300"><LifeBuoy className="h-4 w-4" /> Support and code</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <ContactCard
                  icon={<Mail size={20} />}
                  label="Support email"
                  value="lipitranslate.general@gmail.com"
                  href="mailto:lipitranslate.general@gmail.com"
                />
                <ContactCard
                  icon={<Github size={20} />}
                  label="GitHub"
                  value="Source code and technical work"
                  href="https://github.com/earlywinter96"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/10 pt-6 text-center text-sm text-[#7a8296]">
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
      className="group flex items-start gap-4 rounded-xl border border-white/10 bg-[#191c24] p-5 transition-colors duration-150 hover:border-cyan-300/40 hover:bg-[#202631]"
    >
      <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-cyan-400/10 text-cyan-300">
        {icon}
      </div>
        <div className="min-w-0 flex-1 space-y-1">
        <div className="text-sm font-medium text-white">
          {label}
        </div>
        <ArrowUpRight className="h-4 w-4 shrink-0 text-[#7a8296] transition-colors group-hover:text-cyan-300" />
        <div className="text-xs text-[#a3a9b8]">
          {value}
        </div>
      </div>
    </a>
  );
}
