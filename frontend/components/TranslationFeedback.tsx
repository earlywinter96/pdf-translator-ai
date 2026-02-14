"use client";

import { ThumbsUp, ThumbsDown, Send } from "lucide-react";
import { useState } from "react";

interface Props {
  jobId: string;
}

export default function TranslationFeedback({ jobId }: Props) {
  const [rating, setRating] = useState<"good" | "bad" | null>(null);
  const [feedback, setFeedback] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (!rating) return;

    try {
      // You can implement API endpoint for feedback here
      console.log("Feedback submitted:", { jobId, rating, feedback });
      setSubmitted(true);
    } catch (error) {
      console.error("Failed to submit feedback:", error);
    }
  };

  if (submitted) {
    return (
      <div className="rounded-xl bg-green-500/10 border border-green-500/30 p-6 text-center">
        <p className="text-green-400 font-medium">
          Thank you for your feedback! 🎉
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-6 space-y-4">
      <h3 className="text-white font-semibold text-center">
        How was the translation?
      </h3>

      <div className="flex justify-center gap-4">
        <button
          onClick={() => setRating("good")}
          className={`p-4 rounded-lg border transition ${
            rating === "good"
              ? "border-green-500 bg-green-500/20 text-green-400"
              : "border-white/10 text-gray-400 hover:border-green-500/50"
          }`}
        >
          <ThumbsUp className="w-6 h-6" />
        </button>
        <button
          onClick={() => setRating("bad")}
          className={`p-4 rounded-lg border transition ${
            rating === "bad"
              ? "border-red-500 bg-red-500/20 text-red-400"
              : "border-white/10 text-gray-400 hover:border-red-500/50"
          }`}
        >
          <ThumbsDown className="w-6 h-6" />
        </button>
      </div>

      {rating && (
        <>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Tell us more (optional)..."
            className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition resize-none"
            rows={3}
          />
          <button
            onClick={handleSubmit}
            className="w-full px-6 py-3 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-medium transition shadow-lg flex items-center justify-center gap-2"
          >
            <Send className="w-4 h-4" />
            Submit Feedback
          </button>
        </>
      )}
    </div>
  );
}