export default function FanoutLoading() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12 space-y-10 animate-pulse">
      {/* Header skeleton */}
      <div className="space-y-3">
        <div className="h-3 w-24 rounded-full skeleton" />
        <div className="h-8 w-64 rounded-xl skeleton" />
        <div className="h-4 w-full rounded-full skeleton" />
        <div className="h-4 w-2/3 rounded-full skeleton" />
      </div>
      {/* Intent legend skeleton */}
      <div className="grid grid-cols-3 gap-2">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-14 rounded-xl skeleton" />
        ))}
      </div>
      {/* Input card skeleton */}
      <div className="rounded-2xl border border-border bg-surface p-6 space-y-5">
        <div className="h-11 w-full rounded-xl skeleton" />
        <div className="h-10 w-full rounded-xl skeleton" />
      </div>
    </div>
  );
}
