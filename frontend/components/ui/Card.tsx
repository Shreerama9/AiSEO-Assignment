import { type HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
}

export default function Card({ elevated = false, className = "", children, ...props }: CardProps) {
  return (
    <div
      className={[
        "rounded-2xl border",
        elevated
          ? "bg-elevated border-border-hi"
          : "bg-surface border-border",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}
