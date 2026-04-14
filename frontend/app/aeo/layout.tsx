import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AEO Content Scorer",
  description:
    "Score any URL or article text across direct-answer quality, heading hierarchy, and Flesch-Kincaid readability. Get a 0–100 AEO score instantly.",
};

export default function AEOLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
