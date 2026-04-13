import Link from "next/link";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-base/80 backdrop-blur-md">
      <div className="mx-auto max-w-6xl px-6 h-14 flex items-center justify-between">
        {/* Wordmark */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 rounded-lg bg-purple flex items-center justify-center shadow-[0_0_12px_rgba(132,94,194,0.5)]">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
              <path
                d="M7 1L12 4V10L7 13L2 10V4L7 1Z"
                stroke="white"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <circle cx="7" cy="7" r="1.5" fill="white" />
            </svg>
          </div>
          <span className="text-sm font-bold tracking-wider text-text-hi group-hover:text-white transition-colors">
            AEGIS
          </span>
        </Link>

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          <NavLink href="/aeo">AEO Scorer</NavLink>
          <NavLink href="/fanout">Fan-Out Engine</NavLink>
        </nav>
      </div>
    </header>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="px-3.5 py-1.5 rounded-lg text-sm text-text-lo hover:text-text-hi hover:bg-elevated transition-all duration-150"
    >
      {children}
    </Link>
  );
}
