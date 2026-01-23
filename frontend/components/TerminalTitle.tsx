"use client";

import { useEffect, useState } from "react";

const TEXT = "< AI PDF Translator >";

export default function TerminalTitle() {
  const [displayed, setDisplayed] = useState("");
  const [showCursor, setShowCursor] = useState(true);

  // Typing effect
  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      setDisplayed(TEXT.slice(0, index + 1));
      index++;

      if (index === TEXT.length) {
        clearInterval(interval);
      }
    }, 60); // typing speed

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
    <h1 className="
      text-lg            /* 📱 mobile */
      sm:text-xl
      md:text-4xl        /* 💻 laptop */
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
      <span
        className={`ml-1 ${showCursor ? "opacity-100" : "opacity-0"}`}
      >
        _
      </span>
    </h1>
  );
}
