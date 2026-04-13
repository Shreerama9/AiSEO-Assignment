"use client";

import { useEffect, useState } from "react";

interface ScoreRingProps {
  score: number; // 0–100
  band: string;
}

function getBandColor(score: number): string {
  if (score >= 85) return "#00C9A7";
  if (score >= 65) return "#845EC2";
  if (score >= 40) return "#FFB347";
  return "#FF6B6B";
}

export default function ScoreRing({ score, band }: ScoreRingProps) {
  const [displayed, setDisplayed] = useState(0);

  // Animate counter
  useEffect(() => {
    let frame = 0;
    const duration = 1200;
    const start = performance.now();
    const tick = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayed(Math.round(eased * score));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const radius = 52;
  const circumference = 2 * Math.PI * radius; // ≈ 326.7
  const offset = circumference * (1 - score / 100);
  const color = getBandColor(score);

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative w-40 h-40">
        <svg
          viewBox="0 0 120 120"
          className="w-full h-full -rotate-90"
          aria-label={`AEO Score: ${score}`}
        >
          {/* Track */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke="rgba(45,31,71,0.8)"
            strokeWidth="10"
          />
          {/* Fill */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference}
            className="score-ring-circle"
            style={
              {
                "--target-offset": offset,
                filter: `drop-shadow(0 0 8px ${color}80)`,
              } as React.CSSProperties
            }
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center rotate-0">
          <span
            className="text-4xl font-bold tabular-nums"
            style={{ color }}
          >
            {displayed}
          </span>
          <span className="text-xs text-text-lo mt-0.5 font-medium">/100</span>
        </div>
      </div>
      <div className="text-center">
        <p
          className="text-sm font-semibold tracking-wide"
          style={{ color }}
        >
          {band}
        </p>
      </div>
    </div>
  );
}
