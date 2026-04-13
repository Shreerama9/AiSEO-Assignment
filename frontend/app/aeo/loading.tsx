export default function AEOLoading() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-10 animate-pulse">
      {/* Header skeleton */}
      <div className="space-y-3">
        <div className="h-3 w-24 rounded-full skeleton" />
        <div className="h-8 w-56 rounded-xl skeleton" />
        <div className="h-4 w-full rounded-full skeleton" />
        <div className="h-4 w-3/4 rounded-full skeleton" />
      </div>
      {/* Card skeleton */}
      <div className="rounded-2xl border border-border bg-surface p-6 space-y-5">
        <div className="h-8 w-36 rounded-xl skeleton" />
        <div className="h-11 w-full rounded-xl skeleton" />
        <div className="h-10 w-full rounded-xl skeleton" />
      </div>
    </div>
  );
}
