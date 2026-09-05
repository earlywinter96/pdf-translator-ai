"use client";

import { FormEvent, useState } from "react";
import { Bot, LoaderCircle, Send, X } from "lucide-react";
import { trackSiteInteraction } from "@/lib/analytics";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://pdf-translator-ai-ggqe.onrender.com";
const MAX_CONVERSATIONS = 5;

type ChatMessage = { role: "assistant" | "user"; content: string };

export default function FaqOrb() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hi! I’m Lipi Assistant. Ask about your free preview, payments, PDF quality, languages, or LipiTranslate." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [askedCount, setAskedCount] = useState(0);
  // A browser refresh starts a fresh, anonymous five-question support session.
  const [chatSessionId] = useState(() => crypto.randomUUID());

  const askQuestion = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || loading || askedCount >= MAX_CONVERSATIONS) return;

    const previousMessages = messages;
    const nextMessages: ChatMessage[] = [...previousMessages, { role: "user", content: trimmed }];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    const nextCount = askedCount + 1;
    setAskedCount(nextCount);
    trackSiteInteraction("faq_chat_message");

    try {
      const response = await fetch(`${API_BASE}/api/support/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, history: previousMessages, session_id: chatSessionId }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to answer right now");
      setMessages((current) => [...current, { role: "assistant", content: data.answer }]);
    } catch {
      setMessages((current) => [...current, {
        role: "assistant",
        content: "I couldn’t connect just now. Please email lipitranslate.general@gmail.com with your question or suggestion.",
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void askQuestion(input);
  };

  return (
    <div className="fixed bottom-5 right-5 z-40 sm:bottom-7 sm:right-7">
      {open && (
        <section className="mb-3 flex max-h-[min(38rem,calc(100dvh-7.5rem))] w-[calc(100vw-2.5rem)] max-w-sm flex-col overflow-hidden rounded-2xl border border-cyan-400/30 bg-[#07182a]/95 shadow-2xl shadow-cyan-950/60 backdrop-blur-xl">
          <header className="flex items-center gap-3 border-b border-cyan-400/15 bg-gradient-to-r from-cyan-500/20 to-blue-500/15 px-4 py-3">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-cyan-400 text-slate-950">
              <Bot className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-white">Lipi Assistant</p>
              <p className="text-xs text-cyan-200">LipiTranslate support · {Math.max(MAX_CONVERSATIONS - askedCount, 0)} questions left</p>
            </div>
            <button onClick={() => setOpen(false)} className="rounded-lg p-2 text-gray-300 hover:bg-white/10 hover:text-white" aria-label="Close FAQ help">
              <X className="h-4 w-4" />
            </button>
          </header>
          <div className="flex min-h-0 flex-1 flex-col gap-3 p-4">
            <div className="min-h-0 flex-1 space-y-2 overflow-y-auto overscroll-contain pr-1 touch-pan-y [scrollbar-gutter:stable]" aria-live="polite">
              {messages.map((message, index) => (
                <p key={`${message.role}-${index}`} className={`max-w-[92%] whitespace-pre-wrap rounded-xl p-3 text-sm leading-relaxed ${message.role === "assistant" ? "rounded-tl-sm bg-cyan-500/10 text-gray-100" : "ml-auto rounded-br-sm bg-blue-500/25 text-white"}`}>
                  {message.content}
                </p>
              ))}
              {loading && <p className="flex w-fit items-center gap-2 rounded-xl rounded-tl-sm bg-cyan-500/10 p-3 text-sm text-cyan-100"><LoaderCircle className="h-4 w-4 animate-spin" /> Checking LipiTranslate support…</p>}
            </div>

            {askedCount < MAX_CONVERSATIONS ? (
              <>
                <form onSubmit={handleSubmit} className="flex gap-2 border-t border-white/10 pt-3">
                  <input value={input} onChange={(event) => setInput(event.target.value)} maxLength={600} disabled={loading} placeholder="Ask about LipiTranslate…" className="min-w-0 flex-1 rounded-xl border border-cyan-400/20 bg-slate-950/70 px-3 py-2 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-300 disabled:opacity-60" />
                  <button type="submit" disabled={loading || !input.trim()} className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-400 text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-40" aria-label="Send support question"><Send className="h-4 w-4" /></button>
                </form>
              </>
            ) : (
              <div className="rounded-xl border border-cyan-300/20 bg-slate-950/40 p-3 text-sm text-gray-200">
                <p className="font-medium text-white">Quick support limit reached.</p>
                <p className="mt-1 leading-relaxed">Please email your query or suggestion to <a href="mailto:lipitranslate.general@gmail.com" className="text-cyan-300 underline underline-offset-2">lipitranslate.general@gmail.com</a>.</p>
              </div>
            )}
          </div>
        </section>
      )}
      <button onClick={() => setOpen((value) => { if (!value) { trackSiteInteraction("faq_opened"); trackSiteInteraction("faq_chat_started"); } return !value; })} className="group flex items-center gap-2 rounded-full border border-cyan-300/60 bg-gradient-to-br from-cyan-300 to-cyan-600 px-2.5 py-2 text-slate-950 shadow-lg shadow-cyan-500/30 transition hover:scale-105" aria-label={open ? "Close FAQ help" : "Open FAQ help"}>
        <span className="relative grid h-9 w-9 place-items-center rounded-full bg-slate-950/15">
          <Bot className="h-5 w-5" />
          <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-cyan-300 bg-emerald-400" />
        </span>
        <span className="pr-1 text-sm font-semibold">Need help?</span>
      </button>
    </div>
  );
}
