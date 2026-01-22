"use client";

import { useRouter } from "next/navigation";

export default function HomeClient() {
  const router = useRouter();

  return (
    <main className="min-h-screen bg-gradient-to-br from-[#020617] to-black flex items-center justify-center px-6">
      <div className="max-w-4xl mx-auto pt-24 pb-20 space-y-14 text-center">

        <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
          AI PDF Translator
        </h1>

        <p className="text-gray-400 text-lg">
          Translate scanned and text-based PDFs from
          <span className="text-white font-medium">
            {" "}Gujarati, Hindi, and Marathi
          </span>{" "}
          into accurate English using AI.
        </p>

        <div className="pt-6">
          <button
            onClick={() => router.push("/convert")}
            className="px-8 py-4 rounded-lg text-white font-medium
              bg-gradient-to-r from-indigo-600 to-cyan-600
              hover:from-indigo-500 hover:to-cyan-500
              transition shadow-lg"
          >
            Convert PDF →
          </button>
        </div>

      </div>
    </main>
  );
}
