export default function SkeletonCards() {
  return (
    <>
      {[...Array(4)].map((_, i) => (
        <div
          key={i}
          className="h-16 rounded-xl skeleton"
          style={{ animationDelay: `${i * 0.1}s` }}
        />
      ))}
    </>
  );
}
