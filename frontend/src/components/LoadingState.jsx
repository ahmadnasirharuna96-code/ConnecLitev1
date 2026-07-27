export default function LoadingState({ label = "Loading" }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-mist-500">
      <span className="signal-bars text-signal">
        <span></span><span></span><span></span><span></span>
      </span>
      <p className="text-sm">{label}…</p>
    </div>
  );
}
