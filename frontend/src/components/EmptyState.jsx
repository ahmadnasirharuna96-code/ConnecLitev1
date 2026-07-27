export default function EmptyState({ title, body, action }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-night-600 px-6 py-14 text-center">
      <h3 className="font-display text-lg font-semibold text-mist-100">{title}</h3>
      {body && <p className="max-w-sm text-sm text-mist-500">{body}</p>}
      {action}
    </div>
  );
}
