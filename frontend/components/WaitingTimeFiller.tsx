"use client";

import { useState, useEffect } from "react";
import { Brain, Zap, Target, Trophy } from "lucide-react";

interface Props {
  progress: number;
}

export default function WaitingTimeFiller({ progress }: Props) {
  const [currentActivity, setCurrentActivity] = useState<'trivia' | 'guess' | 'tips'>('trivia');
  const [triviaIndex, setTriviaIndex] = useState(0);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(false);

  // AI & Tech Trivia Questions
  const triviaQuestions = [
    {
      question: "Which AI model was the first to pass the Turing Test convincingly?",
      options: ["GPT-3", "ELIZA", "Eugene Goostman", "Watson"],
      correct: 2,
      explanation: "Eugene Goostman, a chatbot, convinced 33% of judges it was a 13-year-old boy in 2014."
    },
    {
      question: "How many languages does Google Translate support?",
      options: ["75", "108", "133", "150"],
      correct: 2,
      explanation: "Google Translate supports 133 languages as of 2024!"
    },
    {
      question: "What does OCR stand for?",
      options: ["Optical Character Reading", "Online Content Recognition", "Optical Character Recognition", "Organized Character Reading"],
      correct: 2,
      explanation: "OCR = Optical Character Recognition, the technology converting images to text."
    },
    {
      question: "Which country has the most AI startups per capita?",
      options: ["USA", "China", "Israel", "India"],
      correct: 2,
      explanation: "Israel leads with the highest concentration of AI startups per capita globally!"
    },
    {
      question: "What year was the PDF format invented?",
      options: ["1983", "1993", "2003", "2013"],
      correct: 1,
      explanation: "Adobe invented PDF in 1993 to make documents portable across platforms."
    }
  ];

  // Productivity Tips
  const productivityTips = [
    {
      icon: "⚡",
      title: "Batch Similar Tasks",
      tip: "Group similar translation or document tasks together. You'll work 25% faster by reducing context switching!",
    },
    {
      icon: "🎯",
      title: "Use Keyboard Shortcuts",
      tip: "Ctrl+S to save, Ctrl+F to find. Mastering 10 shortcuts can save you 8 days per year!",
    },
    {
      icon: "🧠",
      title: "Take Smart Breaks",
      tip: "Use the Pomodoro technique: 25 minutes work, 5 minute break. Your brain retains 40% more information this way.",
    },
    {
      icon: "📊",
      title: "Organize Your Files",
      tip: "Use descriptive file names like 'Invoice_ClientName_2024-01.pdf' instead of 'Document1.pdf'. You'll find files 10x faster!",
    },
    {
      icon: "💡",
      title: "AI Prompting Pro Tip",
      tip: "Be specific with AI! Instead of 'translate this', try 'translate this legal document from Gujarati to formal English'. Clarity = Better results.",
    }
  ];

  const currentTrivia = triviaQuestions[triviaIndex];

  const handleAnswer = (selectedIndex: number) => {
    if (!answered) {
      setAnswered(true);
      if (selectedIndex === currentTrivia.correct) {
        setScore(score + 1);
      }
      
      // Move to next question after 3 seconds
      setTimeout(() => {
        setTriviaIndex((triviaIndex + 1) % triviaQuestions.length);
        setAnswered(false);
      }, 3000);
    }
  };

  // Auto-rotate activities during processing
  useEffect(() => {
    if (progress > 0 && progress < 100) {
      const interval = setInterval(() => {
        setCurrentActivity(prev => {
          if (prev === 'trivia') return 'tips';
          if (prev === 'tips') return 'trivia';
          return 'trivia';
        });
      }, 20000); // Switch every 20 seconds

      return () => clearInterval(interval);
    }
  }, [progress]);

  if (progress >= 100 || progress === 0) return null;

  return (
    <div className="space-y-4">
      
      {/* Activity Tabs */}
      <div className="flex gap-2 justify-center">
        <button
          onClick={() => setCurrentActivity('trivia')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
            currentActivity === 'trivia'
              ? 'bg-purple-600 text-white'
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          <Brain className="w-4 h-4" />
          Trivia
        </button>
        <button
          onClick={() => setCurrentActivity('tips')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
            currentActivity === 'tips'
              ? 'bg-purple-600 text-white'
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
          }`}
        >
          <Zap className="w-4 h-4" />
          Pro Tips
        </button>
      </div>

      {/* Trivia Game */}
      {currentActivity === 'trivia' && (
        <div className="rounded-xl border border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-pink-500/10 p-6 space-y-4">
          
          {/* Score */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-400" />
              <span className="text-sm font-semibold text-white">
                Score: {score}/{triviaIndex + (answered ? 1 : 0)}
              </span>
            </div>
            <span className="text-xs text-purple-400">
              Question {triviaIndex + 1}/{triviaQuestions.length}
            </span>
          </div>

          {/* Question */}
          <div className="space-y-3">
            <p className="text-white font-medium">
              {currentTrivia.question}
            </p>

            {/* Options */}
            <div className="space-y-2">
              {currentTrivia.options.map((option, idx) => {
                const isCorrect = idx === currentTrivia.correct;
                const isSelected = answered;
                
                return (
                  <button
                    key={idx}
                    onClick={() => handleAnswer(idx)}
                    disabled={answered}
                    className={`
                      w-full p-3 rounded-lg text-left text-sm transition-all
                      ${!answered 
                        ? 'bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10' 
                        : isCorrect
                        ? 'bg-green-500/20 text-green-300 border border-green-500/40'
                        : 'bg-white/5 text-gray-500 border border-white/10'
                      }
                    `}
                  >
                    {option}
                    {answered && isCorrect && " ✓"}
                  </button>
                );
              })}
            </div>

            {/* Explanation */}
            {answered && (
              <div className="mt-3 p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                <p className="text-xs text-blue-300">
                  💡 {currentTrivia.explanation}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Productivity Tips */}
      {currentActivity === 'tips' && (
        <div className="rounded-xl border border-cyan-500/30 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 p-6 space-y-4">
          
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center text-2xl">
              {productivityTips[triviaIndex % productivityTips.length].icon}
            </div>
            <div>
              <h3 className="text-white font-semibold">
                {productivityTips[triviaIndex % productivityTips.length].title}
              </h3>
              <span className="text-xs text-cyan-400">Productivity Hack</span>
            </div>
          </div>

          <p className="text-gray-300 text-sm leading-relaxed">
            {productivityTips[triviaIndex % productivityTips.length].tip}
          </p>

          <div className="flex gap-1">
            {productivityTips.map((_, idx) => (
              <div
                key={idx}
                className={`h-1 flex-1 rounded-full transition-all ${
                  idx === triviaIndex % productivityTips.length
                    ? 'bg-cyan-400'
                    : 'bg-white/20'
                }`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Fun Message */}
      <p className="text-center text-xs text-gray-500">
        ⏳ While you wait, expand your knowledge!
      </p>

    </div>
  );
}