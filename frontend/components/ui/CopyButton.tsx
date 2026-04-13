"use client";

import { useState } from "react";

interface CopyButtonProps {
  getValue: () => string;
  label?: string;
  className?: string;
}

export default function CopyButton({ getValue, label = "Copy", className = "" }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(getValue());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard not available (non-HTTPS / denied)
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={[
        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold",
        "border border-border bg-elevated text-text-lo",
        "hover:border-border-hi hover:text-text-mid transition-all duration-150 cursor-pointer",
        className,
      ].join(" ")}
      aria-label={copied ? "Copied!" : label}
    >
      {copied ? (
        <>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden>
            <path d="M2 6l3 3 5-5" stroke="#00C9A7" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span style={{ color: "#00C9A7" }}>Copied!</span>
        </>
      ) : (
        <>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden>
            <rect x="4" y="1" width="7" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
            <path d="M1 4h2M1 4v7h7V9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
          </svg>
          {label}
        </>
      )}
    </button>
  );
}
