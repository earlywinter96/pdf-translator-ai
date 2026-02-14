import { CheckCircle, Loader2, Lightbulb, Sparkles } from "lucide-react";
import { useState, useEffect } from "react";

interface Props {
  progress: number;
}

export default function ProgressBar({ progress }: Props) {
  const [currentFactIndex, setCurrentFactIndex] = useState(0);
  const [fadeIn, setFadeIn] = useState(true);

  // Curated interesting facts about AI, tech, and translation
  const interestingFacts = [
    {
      icon: "🤖",
      title: "AI Translation Milestone",
      fact: "Google Translate processes over 100 billion words daily across 133 languages, making it one of the most-used AI applications worldwide.",
      category: "AI"
    },
    {
      icon: "🧠",
      title: "OCR Innovation",
      fact: "Modern OCR systems can recognize text with 99%+ accuracy, but handwritten text in Indian languages remains challenging due to script complexity and variations.",
      category: "Tech"
    },
    {
      icon: "🌍",
      title: "Language Diversity",
      fact: "India has 22 official languages and over 19,500 dialects. Gujarat alone has 48 distinct dialects of Gujarati!",
      category: "Culture"
    },
    {
      icon: "⚡",
      title: "AI Speed Record",
      fact: "GPT-4 can process and respond to queries in milliseconds, but careful prompt engineering can improve output quality by 40%.",
      category: "AI"
    },
    {
      icon: "📚",
      title: "Digital India",
      fact: "India's Digital Public Infrastructure (DPI) processes over 10 billion UPI transactions monthly, making it the world's largest real-time payment system.",
      category: "Tech"
    },
    {
      icon: "🎯",
      title: "Translation Accuracy",
      fact: "AI translation has reached human-level parity for high-resource languages, but low-resource languages like Marathi still need 30% more training data.",
      category: "AI"
    },
    {
      icon: "💡",
      title: "Tesseract OCR",
      fact: "The OCR engine used here, Tesseract, was originally developed by HP in the 1980s and is now maintained by Google. It supports over 100 languages!",
      category: "Tech"
    },
    {
      icon: "🚀",
      title: "AI Chip Race",
      fact: "NVIDIA's H100 GPU can perform 60 trillion operations per second, but new competitors like Google's TPU v5 are challenging its dominance.",
      category: "Tech"
    },
    {
      icon: "🎨",
      title: "Indian Language AI",
      fact: "AI models trained specifically on Indian languages outperform general models by 25-40% for regional content, highlighting the importance of localized training.",
      category: "AI"
    },
    {
      icon: "🔐",
      title: "AI Safety First",
      fact: "Your PDF is processed in isolated containers and automatically deleted after translation. Modern cloud systems use zero-trust security by default.",
      category: "Security"
    },
    {
      icon: "📊",
      title: "PDF Format",
      fact: "PDFs can contain embedded fonts, images, and metadata. A typical textbook PDF has 20-30 fonts, making accurate text extraction a complex challenge!",
      category: "Tech"
    },
    {
      icon: "🌟",
      title: "AI Benchmark",
      fact: "Claude 3.5 Sonnet (the model family this app uses) achieves 92% on graduate-level reasoning tasks and 96.7% on multilingual math problems.",
      category: "AI"
    },
    {
      icon: "⚙️",
      title: "Cloud Computing",
      fact: "Processing this PDF requires coordinating 5+ microservices: file storage, OCR, translation API, PDF generation, and job queue management.",
      category: "Tech"
    },
    {
      icon: "🎓",
      title: "Learning Curve",
      fact: "AI models need to see ~10,000 examples to learn a new language pattern, but transfer learning can reduce this to just 1,000 examples.",
      category: "AI"
    },
    {
      icon: "🔬",
      title: "OCR Challenge",
      fact: "Gujarati script has 47 unique characters, compared to English's 26. The curved nature of Gujarati letters makes it 35% harder for OCR to recognize.",
      category: "Tech"
    }
  ];

  // Rotate facts every 8 seconds during processing
  useEffect(() => {
    if (progress > 0 && progress < 100) {
      const interval = setInterval(() => {
        setFadeIn(false);
        setTimeout(() => {
          setCurrentFactIndex((prev) => (prev + 1) % interestingFacts.length);
          setFadeIn(true);
        }, 300);
      }, 8000); // Change fact every 8 seconds

      return () => clearInterval(interval);
    }
  }, [progress, interestingFacts.length]);

  const currentFact = interestingFacts[currentFactIndex];

  // Define processing steps
  const steps = [
    { label: "Uploading PDF", threshold: 10, icon: "📤" },
    { label: "Extracting Text (OCR)", threshold: 30, icon: "🔍" },
    { label: "Analyzing Content", threshold: 50, icon: "🧠" },
    { label: "Translating", threshold: 70, icon: "🌐" },
    { label: "Generating PDF", threshold: 90, icon: "📝" },
    { label: "Finalizing", threshold: 100, icon: "✨" },
  ];

  return (
    <div className="space-y-6">
      
      {/* Interesting Fact Card - Only show during processing */}
      {progress > 0 && progress < 100 && (
        <div className={`
          relative overflow-hidden rounded-xl border border-cyan-500/30 
          bg-gradient-to-br from-cyan-500/10 to-indigo-500/10 
          backdrop-blur-sm p-5 transition-opacity duration-300
          ${fadeIn ? 'opacity-100' : 'opacity-50'}
        `}>
          {/* Animated background gradient */}
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-indigo-500/5 animate-pulse" />
          
          <div className="relative space-y-3">
            {/* Header */}
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-full bg-cyan-500/20">
                <Lightbulb className="w-5 h-5 text-cyan-400" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{currentFact.icon}</span>
                  <h3 className="text-sm font-semibold text-cyan-300">
                    {currentFact.title}
                  </h3>
                </div>
                <span className="text-xs text-cyan-500/60 font-medium">
                  {currentFact.category}
                </span>
              </div>
              <Sparkles className="w-4 h-4 text-yellow-400 animate-pulse" />
            </div>
            
            {/* Fact Content */}
            <p className="text-sm text-gray-300 leading-relaxed">
              {currentFact.fact}
            </p>
            
            {/* Progress Indicator */}
            <div className="flex items-center justify-between pt-2 border-t border-white/10">
              <span className="text-xs text-gray-500">
                💡 Did you know?
              </span>
              <div className="flex gap-1">
                {interestingFacts.map((_, idx) => (
                  <div
                    key={idx}
                    className={`h-1 rounded-full transition-all duration-300 ${
                      idx === currentFactIndex 
                        ? 'w-6 bg-cyan-400' 
                        : 'w-1 bg-white/20'
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-gray-400">
          <span className="font-medium">Progress</span>
          <span className="font-mono">{progress}%</span>
        </div>
        <div className="relative w-full h-3 rounded-full bg-white/10 overflow-hidden">
          {/* Animated background */}
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 animate-pulse" />
          
          {/* Progress fill */}
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-400 to-indigo-500 transition-all duration-500 ease-out rounded-full"
            style={{ width: `${progress}%` }}
          >
            {/* Shimmer effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" 
                 style={{ 
                   backgroundSize: '200% 100%',
                   animation: 'shimmer 2s infinite'
                 }} 
            />
          </div>
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {steps.map((step, index) => {
          const isComplete = progress >= step.threshold;
          const isCurrent = progress >= (steps[index - 1]?.threshold || 0) && progress < step.threshold;
          
          return (
            <div
              key={step.label}
              className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-300 ${
                isCurrent
                  ? "bg-cyan-500/10 border border-cyan-500/30 scale-105"
                  : isComplete
                  ? "bg-green-500/5 border border-green-500/20"
                  : "bg-white/5 border border-white/10 opacity-50"
              }`}
            >
              {/* Icon/Status */}
              <div className="flex-shrink-0">
                {isComplete ? (
                  <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                  </div>
                ) : isCurrent ? (
                  <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center">
                    <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-lg">
                    {step.icon}
                  </div>
                )}
              </div>

              {/* Label */}
              <div className="flex-1">
                <p className={`text-sm font-medium transition-colors ${
                  isCurrent
                    ? "text-cyan-300"
                    : isComplete
                    ? "text-green-300"
                    : "text-gray-400"
                }`}>
                  {step.label}
                </p>
                {isCurrent && (
                  <p className="text-xs text-gray-500 mt-0.5">In progress...</p>
                )}
                {isComplete && !isCurrent && (
                  <p className="text-xs text-green-500/60 mt-0.5">Complete ✓</p>
                )}
              </div>

              {/* Progress indicator for current step */}
              {isCurrent && (
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" style={{ animationDelay: '0.2s' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" style={{ animationDelay: '0.4s' }} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Estimated time */}
      <div className="text-center">
        <p className="text-xs text-gray-500">
          {progress < 100 ? (
            <>
              ⏱️ Estimated time remaining: <span className="font-medium text-gray-400">
                {progress < 30 ? "2-3 minutes" : progress < 70 ? "1-2 minutes" : "Less than 1 minute"}
              </span>
            </>
          ) : (
            <span className="text-green-400 font-medium">🎉 All done!</span>
          )}
        </p>
      </div>

    </div>
  );
}