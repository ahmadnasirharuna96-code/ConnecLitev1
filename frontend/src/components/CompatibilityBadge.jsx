export default function CompatibilityBadge({ score }) {
  const tone = score >= 75 ? "text-pulse border-pulse/40 bg-pulse/10" : score >= 50 ? "text-signal border-signal/40 bg-signal/10" : "text-mist-500 border-mist-700 bg-night-800";
  return (
    <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${tone}`}>
      {score}% compatible
    </span>
  );
}
