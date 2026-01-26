import { CheckCircle, Loader2 } from "lucide-react";

interface Props {
  progress: number;
}

export default function ProgressBar({ progress }: Props) {
  // Define steps with their completion thresholds
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