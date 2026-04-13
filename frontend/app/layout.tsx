import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "AEGIS — AEO & GEO Content Intelligence",
    template: "%s — AEGIS",
  },
  description:
    "AI-powered content intelligence: AEO scoring and query fan-out analysis for GEO optimization.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full`}
    >
      <body className="min-h-full flex flex-col antialiased">
        <Navbar />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-border py-5">
          <div className="mx-auto max-w-6xl px-6 flex items-center justify-between">
            <p className="text-xs text-text-lo">AEGIS v1.1.0</p>
            <p className="text-xs text-text-lo">
              AEO &amp; GEO Content Intelligence Platform
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
