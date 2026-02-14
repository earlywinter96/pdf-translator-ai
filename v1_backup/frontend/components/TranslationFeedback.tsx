"use client";

import { useState } from "react";
import { ThumbsUp, ThumbsDown, MessageSquare, Send, CheckCircle } from "lucide-react";

interface Props {
  jobId: string;
}

export default function TranslationFeedback({ jobId }: Props) {
  const [rating, setRating] = useState<"good" | "bad" | null>(null);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleRating = (value: "good" | "bad") => {
    setRating(value);
    if (value === "bad") {
      setShowComment(true);
    }
  };

  const handleSubmit = async () => {
    if (!rating) return;

    setSubmitting(true);

    try {
      // Send feedback to backend (implement this endpoint)
      const feedback = {
        job_id: jobId,
        rating,
        comment: comment.trim() || null,
        timestamp: new Date().toISOString()
      };

      // TODO: Implement backend endpoint
      // await fetch(`${API_BASE}/api/feedback`, {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify(feedback)
      // });

      console.log("Feedback submitted:", feedback);
      
      // For now, just show success
      setSubmitted(true);
      
    } catch (error) {
      console.error("Failed to submit feedback:", error);
      alert("Failed to submit feedback. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="rounded-xl bg-green-500/10 border border-green-500/30 p-6 text-center">
        <CheckCircle className="w-12 h-12 mx-auto text-green-400 mb-3" />
        <h3 className="text-white font-semibold mb-2">Thank You!</h3>
        <p className="text-sm text-gray-400">
          Your feedback helps us improve translation quality.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-6 space-y-4">
      
      {/* Header */}
      <div className="text-center">
        <h3 className="text-white font-semibold mb-1">How was the translation?</h3>
        <p className="text-xs text-gray-500">Your feedback helps us improve</p>
      </div>

      {/* Rating Buttons */}
      {!rating && (
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => handleRating("good")}
            className="group flex items-center gap-2 px-6 py-3 rounded-lg
              bg-white/5 border border-white/10
              hover:bg-green-500/10 hover:border-green-500/30
              transition"
          >
            <ThumbsUp className="w-5 h-5 text-gray-400 group-hover:text-green-400 transition" />
            <span className="text-sm text-gray-300 group-hover:text-green-300">Good</span>
          </button>

          <button
            onClick={() => handleRating("bad")}
            className="group flex items-center gap-2 px-6 py-3 rounded-lg
              bg-white/5 border border-white/10
              hover:bg-red-500/10 hover:border-red-500/30
              transition"
          >
            <ThumbsDown className="w-5 h-5 text-gray-400 group-hover:text-red-400 transition" />
            <span className="text-sm text-gray-300 group-hover:text-red-300">Needs Work</span>
          </button>
        </div>
      )}

      {/* Selected Rating */}
      {rating && !submitted && (
        <div className="text-center space-y-4">
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${
            rating === "good" 
              ? "bg-green-500/10 border border-green-500/30 text-green-300"
              : "bg-red-500/10 border border-red-500/30 text-red-300"
          }`}>
            {rating === "good" ? (
              <ThumbsUp className="w-5 h-5" />
            ) : (
              <ThumbsDown className="w-5 h-5" />
            )}
            <span className="text-sm font-medium">
              {rating === "good" ? "Glad it helped!" : "We'll do better"}
            </span>
          </div>

          {/* Optional Comment */}
          {rating === "bad" && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-gray-400 justify-center">
                <MessageSquare className="w-4 h-4" />
                <span className="text-xs">Tell us what went wrong (optional)</span>
              </div>
              
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="E.g., Translation was inaccurate, formatting issues, missing text..."
                className="w-full px-4 py-3 rounded-lg bg-[#020617] border border-white/10
                  text-sm text-gray-200 placeholder-gray-500
                  focus:border-cyan-500 focus:outline-none resize-none"
                rows={3}
                maxLength={500}
              />
              <p className="text-xs text-gray-600 text-right">{comment.length}/500</p>
            </div>
          )}

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="px-6 py-2 rounded-lg text-sm font-medium
              bg-cyan-600 text-white hover:bg-cyan-500
              disabled:opacity-50 disabled:cursor-not-allowed
              transition flex items-center justify-center gap-2 mx-auto"
          >
            {submitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Submit Feedback
              </>
            )}
          </button>
        </div>
      )}

    </div>
  );
}