import Link from "next/link";
import { Github, Linkedin, Globe } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-[#020617]/90">
      <div className="max-w-7xl mx-auto px-6 py-6
        flex flex-col sm:flex-row items-center
        justify-between gap-4 text-sm text-gray-400">

        <div className="flex gap-4">
          <Link href="/privacy" className="hover:text-white">Privacy</Link>
          <Link href="/terms" className="hover:text-white">Terms</Link>
          <Link href="/contact" className="hover:text-white">Contact</Link>
        </div>

        <div className="flex gap-4">
          <a href="https://github.com/earlywinter96" target="_blank"><Github size={18} /></a>
          <a href="https://www.linkedin.com/in/hemant-solanki-366462199/" target="_blank"><Linkedin size={18} /></a>
          <a href="https://my-portfolio2-peach-six.vercel.app/" target="_blank"><Globe size={18} /></a>
        </div>
      </div>
    </footer>
  );
}
