"use client";

import Link from "next/link";
import Image from "next/image";
import DeveloperSignature from "@/components/DeveloperSignature";
import { trackSiteInteraction } from "@/lib/analytics";
import { ArrowUpRight, Instagram, Linkedin, Mail } from "lucide-react";


export default function Footer() {
  return (
    <footer className="bg-[#020617] border-t border-gray-800 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <Link href="/" className="mb-4 inline-flex items-center gap-3 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/70">
              <Image
                src="/lipitranslate-logo.png"
                alt="LipiTranslate.in logo"
                width={36}
                height={36}
                className="h-10 w-10 rounded-xl border border-cyan-300/20 bg-[#11141c] p-0.5"
              />
              <span className="text-xl font-semibold tracking-[-0.01em] text-white">
                Lipi<span className="text-cyan-500">Translate.in</span>
              </span>
            </Link>
            <p className="text-gray-400 text-sm">
              Free AI-powered PDF translation for Gujarati, Hindi, Marathi, and
              English. OCR support for scanned documents.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/convert"
                  onClick={() => trackSiteInteraction("footer_translate")}
                  className="text-gray-400 hover:text-white text-sm transition-colors"
                >
                  Translate PDF
                </Link>
              </li>
              <li>
                <Link
                  href="/about"
                  onClick={() => trackSiteInteraction("footer_about")}
                  className="text-gray-400 hover:text-white text-sm transition-colors"
                >
                  About Us
                </Link>
              </li>
              <li>
                <Link
                  href="/contact"
                  onClick={() => trackSiteInteraction("footer_contact")}
                  className="text-gray-400 hover:text-white text-sm transition-colors"
                >
                  Contact
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/privacy"
                  className="text-gray-400 hover:text-white text-sm transition-colors"
                >
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link
                  href="/terms"
                  className="text-gray-400 hover:text-white text-sm transition-colors"
                >
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Contact and social links */}
        <div className="mt-10 rounded-2xl border border-cyan-500/15 bg-gradient-to-r from-cyan-500/[0.06] to-indigo-500/[0.06] p-5 sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h4 className="text-white font-semibold">Connect with LipiTranslate.in</h4>
              <p className="mt-1 text-sm text-gray-400">
                Questions, feedback, and product updates — we&apos;re here to help.
              </p>
            </div>
            <Link
              href="/contact"
              onClick={() => trackSiteInteraction("footer_contact_panel")}
              className="inline-flex w-fit items-center gap-1.5 rounded-lg border border-cyan-400/30 px-3 py-2 text-sm font-medium text-cyan-300 transition hover:border-cyan-300 hover:bg-cyan-400/10 hover:text-white"
            >
              View all contact options
              <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>

          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <FooterContactLink
              href="mailto:lipitranslate.general@gmail.com"
              icon={<Mail className="h-4 w-4" aria-hidden="true" />}
              label="Email support"
              value="lipitranslate.general@gmail.com"
            />
            <FooterContactLink
              href="https://www.linkedin.com/company/lipitranslate.in?trk=public_post_follow-view-profile"
              icon={<Linkedin className="h-4 w-4" aria-hidden="true" />}
              label="LinkedIn"
              value="Company updates"
            />
            <FooterContactLink
              href="https://www.instagram.com/lipitranslate.in?utm_source=qr&stkn=MTg4YmNheW9xM2ltYg=="
              icon={<Instagram className="h-4 w-4" aria-hidden="true" />}
              label="Instagram"
              value="Follow our updates"
            />
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-800 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-gray-400">
  <span>
    © 2025 LipiTranslate.in. All rights reserved.
  </span>

  <DeveloperSignature />
</div>
    
      </div>
    </footer>
  );
}

function FooterContactLink({
  href,
  icon,
  label,
  value,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  const external = href.startsWith("http");

  return (
    <a
      href={href}
      {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      className="group flex min-w-0 items-center gap-3 rounded-xl border border-white/10 bg-black/10 px-3 py-3 transition hover:border-cyan-400/40 hover:bg-cyan-400/[0.08]"
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan-400/10 text-cyan-300 transition group-hover:bg-cyan-400/20">
        {icon}
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-medium text-gray-200">{label}</span>
        <span className="block truncate text-xs text-gray-400">{value}</span>
      </span>
    </a>
  );
}
