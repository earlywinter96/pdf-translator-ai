"use client";

import Link from "next/link";
import { Github, Linkedin, Globe } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-30 bg-[#020617]/90 backdrop-blur-md border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">

        {/* Left: Logo / Brand */}
          <Link
            href="/"
            aria-label="LipiTranslate PDF Translator for Indian Languages"
            className="flex items-center gap-2 text-sm font-semibold
              text-gray-100 tracking-wide
              hover:text-cyan-400 transition"
          >
            <span className="text-cyan-400">▸</span>
            <span className="hidden sm:inline">
              LipiTranslate – PDF Translator
            </span>
            <span className="sm:hidden">
              LipiTranslate
            </span>
          </Link>

        {/* Right: Nav + Icons */}
        <div className="flex items-center gap-5 text-sm text-gray-300">

          <Link
            href="/about"
            className="relative hover:text-white transition
              after:absolute after:-bottom-1 after:left-0
              after:h-[1px] after:w-0 after:bg-cyan-400
              hover:after:w-full after:transition-all"
          >
            About
          </Link>

          <Link
            href="/contact"
            className="relative hover:text-white transition
              after:absolute after:-bottom-1 after:left-0
              after:h-[1px] after:w-0 after:bg-cyan-400
              hover:after:w-full after:transition-all"
          >
            Contact
          </Link>

          {/* Divider */}
          <span className="h-4 w-px bg-white/10" />

          {/* Icons */}
          <IconLink
            href="https://www.linkedin.com/in/hemant-solanki-366462199/"
            label="LinkedIn"
          >
            <Linkedin size={18} />
          </IconLink>

          <IconLink
            href="https://github.com/earlywinter96"
            label="GitHub"
          >
            <Github size={18} />
          </IconLink>

          <IconLink
            href="https://my-portfolio2-peach-six.vercel.app/"
            label="Portfolio"
          >
            <Globe size={18} />
          </IconLink>
        </div>
      </div>
      {/* 🔍 SEO INTERNAL LINKS (HIDDEN BUT VALID) */}
      <div className="sr-only">
        <Link href="/convert">OCR PDF Translator</Link>
        <Link href="/convert">Translate Hindi PDF to English</Link>
        <Link href="/convert">Gujarati PDF Translation</Link>
        <Link href="/convert">Marathi PDF to English</Link>
        </div>
    </nav>
  );
}

function IconLink({
  href,
  label,
  children,
}: {
  href: string;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      className="text-gray-300 hover:text-cyan-400 transition"
    >
      {children}
    </a>
  );
}
