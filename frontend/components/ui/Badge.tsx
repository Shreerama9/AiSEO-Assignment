type BadgeVariant = "purple" | "teal" | "warn" | "danger" | "neutral";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  purple:  "bg-[rgba(132,94,194,0.2)] text-purple-light border border-[rgba(132,94,194,0.3)]",
  teal:    "bg-[rgba(0,201,167,0.15)] text-teal border border-[rgba(0,201,167,0.25)]",
  warn:    "bg-[rgba(255,179,71,0.15)] text-warn border border-[rgba(255,179,71,0.25)]",
  danger:  "bg-[rgba(255,107,107,0.15)] text-danger border border-[rgba(255,107,107,0.25)]",
  neutral: "bg-elevated text-text-lo border border-border",
};

export default function Badge({ variant = "neutral", className = "", children }: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold",
        variantStyles[variant],
        className,
      ].join(" ")}
    >
      {children}
    </span>
  );
}
