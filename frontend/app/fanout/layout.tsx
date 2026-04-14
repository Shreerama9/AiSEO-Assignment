import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Query Fan-Out Engine",
  description:
    "Fan out any topic into 10–15 intent-mapped sub-queries across 6 intent types. Optionally paste existing content to surface coverage gaps in real time.",
};

export default function FanoutLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
