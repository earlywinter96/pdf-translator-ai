import Link from "next/link";
import { Github, Linkedin, Globe } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-[#020617]/90">
      <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-400">
        {/* Links */}
        <div className="flex gap-4">
          <Link href="/privacy" className="hover:text-white transition">Privacy</Link>
          <Link href="/terms" className="hover:text-white transition">Terms</Link>
          <Link href="/contact" className="hover:text-white transition">Contact</Link>
        </div>

        {/* Creator Credit - Highlighted */}
        <div className="text-center">
          <span className="text-gray-400">Developed by </span>
          <a 
            href="https://my-portfolio2-peach-six.vercel.app/" 
            target="_blank"
            rel="noopener noreferrer"
            className="text-white font-semibold hover:text-cyan-400 transition-colors duration-300
              px-2 py-1 rounded
              bg-gradient-to-r from-indigo-600/20 to-cyan-600/20
              border-b-2 border-cyan-500/50 hover:border-cyan-400"
          >
            &lt; Hemant Solanki &gt;
          </a>
        </div>

        {/* Social Links */}
        <div className="flex gap-4">
          <a 
            href="https://github.com/earlywinter96" 
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition"
            aria-label="GitHub"
          >
            <Github size={18} />
          </a>
          <a 
            href="https://www.linkedin.com/in/hemant-solanki-366462199/" 
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition"
            aria-label="LinkedIn"
          >
            <Linkedin size={18} />
          </a>
          <a 
            href="https://my-portfolio2-peach-six.vercel.app/" 
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition"
            aria-label="Portfolio"
          >
            <Globe size={18} />
          </a>
        </div>
      </div>
    </footer>
  );
}