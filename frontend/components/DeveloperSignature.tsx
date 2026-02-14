"use client";

export default function DeveloperSignature({
  variant = "footer",
}: {
  variant?: "navbar" | "hero" | "footer";
}) {
  const base =
    "font-mono tracking-tight flex items-center gap-2 select-none";

  const variants = {
    navbar:
      "text-xs text-cyan-400/80 hover:text-cyan-300 transition",
    hero:
      "text-sm md:text-base text-cyan-400 drop-shadow-[0_0_10px_rgba(34,211,238,0.35)]",
    footer:
      "text-xs text-gray-400 hover:text-cyan-400 transition",
  };

  return (
    <div className={`${base} ${variants[variant]}`}>
      <span className="text-green-400">$</span>
      <span className="opacity-80">developed_by</span>

      <a
        href="https://my-portfolio2-peach-six.vercel.app/"
        target="_blank"
        rel="noopener noreferrer"
        className="text-white font-semibold hover:text-cyan-300 transition underline underline-offset-4 decoration-cyan-500/40 hover:decoration-cyan-400"
      >
        Hemant&nbsp;Solanki
      </a>

      <span className="text-cyan-500">;</span>
    </div>
  );
}
