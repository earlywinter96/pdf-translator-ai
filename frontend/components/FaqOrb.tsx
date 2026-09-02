"use client";

import { useState } from "react";
import { Bot, Send, X } from "lucide-react";
import { trackSiteInteraction } from "@/lib/analytics";

const FAQS = [
  {
    question: "How does the free preview work?",
    answer: "We translate only page 1 for free. Review it first, then pay only to unlock the remaining pages.",
  },
  {
    question: "Why do I need to pay?",
    answer: "Payment covers translation, OCR, PDF processing, and secure delivery of the remaining pages.",
  },
  {
    question: "Which languages are supported?",
    answer: "LipiTranslate supports English and major Indian languages including Gujarati, Hindi, and Marathi.",
  },
  {
    question: "My scanned PDF is unclear",
    answer: "For the best OCR result, upload a sharp scan with straight pages, clear text, and good lighting.",
  },
];

export default function FaqOrb() {
  const [open, setOpen] = useState(false);
  const [answer, setAnswer] = useState(FAQS[0].answer);

  return (
    <div className="fixed bottom-5 right-5 z-40 sm:bottom-7 sm:right-7">
      {open && (
        <section className="mb-3 w-[calc(100vw-2.5rem)] max-w-sm overflow-hidden rounded-2xl border border-cyan-400/30 bg-[#07182a]/95 shadow-2xl shadow-cyan-950/60 backdrop-blur-xl">
          <header className="flex items-center gap-3 border-b border-cyan-400/15 bg-gradient-to-r from-cyan-500/20 to-blue-500/15 px-4 py-3">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-cyan-400 text-slate-950">
              <Bot className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-white">Lipi Assistant</p>
              <p className="text-xs text-cyan-200">FAQ support - no AI chat yet</p>
            </div>
            <button onClick={() => setOpen(false)} className="rounded-lg p-2 text-gray-300 hover:bg-white/10 hover:text-white" aria-label="Close FAQ help">
              <X className="h-4 w-4" />
            </button>
          </header>
          <div className="space-y-3 p-4">
            <p className="rounded-xl rounded-tl-sm bg-cyan-500/10 p-3 text-sm leading-relaxed text-gray-200">{answer}</p>
            <div className="flex flex-wrap gap-2">
              {FAQS.map((faq) => (
                <button key={faq.question} onClick={() => { setAnswer(faq.answer); trackSiteInteraction("faq_question"); }} className="rounded-full border border-cyan-400/25 bg-cyan-500/10 px-3 py-2 text-left text-xs text-cyan-100 transition hover:border-cyan-300 hover:bg-cyan-500/20">
                  {faq.question}
                </button>
              ))}
            </div>
            <p className="flex items-center gap-2 border-t border-white/10 pt-3 text-xs text-gray-400"><Send className="h-3.5 w-3.5 text-cyan-300" /> Need human support? Use the Contact page for now.</p>
          </div>
        </section>
      )}
      <button onClick={() => setOpen((value) => { if (!value) trackSiteInteraction("faq_opened"); return !value; })} className="group flex items-center gap-2 rounded-full border border-cyan-300/60 bg-gradient-to-br from-cyan-300 to-cyan-600 px-2.5 py-2 text-slate-950 shadow-lg shadow-cyan-500/30 transition hover:scale-105" aria-label={open ? "Close FAQ help" : "Open FAQ help"}>
        <span className="relative grid h-9 w-9 place-items-center rounded-full bg-slate-950/15">
          <Bot className="h-5 w-5" />
          <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-cyan-300 bg-emerald-400" />
        </span>
        <span className="pr-1 text-sm font-semibold">Need help?</span>
      </button>
    </div>
  );
}
