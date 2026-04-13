"use client";

import { type InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className = "", id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-semibold uppercase tracking-wider text-text-lo"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={[
            "w-full h-11 px-4 rounded-xl bg-elevated border text-text-hi text-sm",
            "placeholder:text-text-lo",
            "transition-colors duration-150",
            error
              ? "border-danger focus:border-danger focus:outline-none"
              : "border-border focus:border-purple focus:outline-none",
            className,
          ].join(" ")}
          {...props}
        />
        {error && <p className="text-xs text-danger">{error}</p>}
        {hint && !error && <p className="text-xs text-text-lo">{hint}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
