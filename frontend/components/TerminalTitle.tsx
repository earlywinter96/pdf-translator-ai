"use client";

import { useEffect, useState } from "react";

/**
 * SEO NOTE:
 * - Visible text keeps terminal style
 * - Hidden h1 ensures Google always reads full keywords
 */

const TERMINAL_TEXT = "< LipiTranslate–PDF & OCR Translator >";
const SEO_TEXT =
  "LipiTranslate – PDF & OCR Translator for Gujarati, Hindi and Marathi";

export default function TerminalTitle() {
  const [displayed, setDisplayed] = useState("");
  const [showCursor, setShowCursor] = useState(true);

  // Typing effect
  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      setDisplayed(TERMINAL_TEXT.slice(0, index + 1));
      index++;

      if (index === TERMINAL_TEXT.length) {
        clearInterval(interval);
      }
    }, 60);

    return () => clearInterval(interval);
  }, []);

  // Cursor blink
  useEffect(() => {
    const cursorInterval = setInterval(() => {
      setShowCursor((prev) => !prev);
    }, 500);

    return () => clearInterval(cursorInterval);
  }, []);

  return (
    <>
      {/* ✅ SEO-safe H1 (invisible, crawler-readable) */}
      <h1 className="sr-only">{SEO_TEXT}</h1>

      {/* ✅ Terminal-style visual H1 */}
      <h1
        aria-hidden="true"
        className="
          text-lg
          sm:text-xl
          md:text-4xl
          lg:text-5xl
          font-mono
          font-semibold
          tracking-tight
          text-white
          flex justify-center items-center
          drop-shadow-[0_0_14px_rgba(56,189,248,0.35)]
          whitespace-nowrap
        "
      >
        {displayed}
        <span className={`ml-1 ${showCursor ? "opacity-100" : "opacity-0"}`}>
          _
        </span>
      </h1>
    </>
  );
}
