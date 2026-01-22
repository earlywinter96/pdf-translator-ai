"use client";

interface Props {
  progress: number;
}

export default function ProgressBar({ progress }: Props) {
  return (
    <div className="space-y-2">

      {/* Label */}
      <div className="flex justify-between text-xs text-gray-500">
        <span>Processing document</span>
        <span>{progress}%</span>
      </div>

      {/* Bar */}
      <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-cyan-400/80 to-indigo-500/80
          transition-all duration-700 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

    </div>
  );
}
