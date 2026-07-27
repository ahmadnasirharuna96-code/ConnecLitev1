import { useEffect, useState } from "react";
import { Zap } from "lucide-react";
import { AirtimeAPI } from "../api/resources";
import EmptyState from "../components/EmptyState.jsx";
import LoadingState from "../components/LoadingState.jsx";

const STATUS_COLOR = {
  success: "text-pulse",
  pending: "text-signal",
  failed: "text-red-400",
};

export default function Airtime() {
  const [transactions, setTransactions] = useState(null);
  const [form, setForm] = useState({ recipient_phone: "", amount: "" });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function loadTransactions() {
    AirtimeAPI.transactions().then(setTransactions).catch(() => setTransactions([]));
  }

  useEffect(loadTransactions, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setSubmitting(true);
    try {
      const txn = await AirtimeAPI.gift(form.recipient_phone, form.amount);
      setResult(txn);
      setForm({ recipient_phone: "", amount: "" });
      loadTransactions();
    } catch (err) {
      setError(err.response?.data?.error || "Could not send airtime.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <header className="mb-6">
        <h1 className="font-display text-2xl font-bold">Airtime</h1>
        <p className="text-sm text-mist-500">Gift airtime to a connection as a small social reward.</p>
      </header>

      <form onSubmit={handleSubmit} className="mb-8 flex flex-col gap-3 rounded-xl border border-night-700 bg-night-800 p-4">
        {error && <p className="rounded bg-red-950 p-2 text-sm text-red-300">{error}</p>}
        {result && (
          <p className="rounded bg-pulse/10 p-2 text-sm text-pulse">
            Sent! Status: {result.status}
            {result.status !== "success" && " — check Transactions below."}
          </p>
        )}
        <input
          required
          placeholder="Recipient phone number"
          value={form.recipient_phone}
          onChange={(e) => setForm({ ...form, recipient_phone: e.target.value })}
          className="rounded-lg bg-night-700 px-3 py-2 text-sm outline-none"
        />
        <input
          required
          type="number"
          min="1"
          step="0.01"
          placeholder="Amount (NGN)"
          value={form.amount}
          onChange={(e) => setForm({ ...form, amount: e.target.value })}
          className="rounded-lg bg-night-700 px-3 py-2 text-sm outline-none"
        />
        <button
          disabled={submitting}
          className="flex items-center justify-center gap-2 rounded-lg bg-signal px-4 py-2 text-sm font-semibold text-night-950 disabled:opacity-50"
        >
          <Zap size={16} /> {submitting ? "Sending…" : "Gift airtime"}
        </button>
      </form>

      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-mist-500">Transaction history</h2>
      {!transactions && <LoadingState label="Loading transactions" />}
      {transactions?.length === 0 && <EmptyState title="No transactions yet" />}
      <div className="flex flex-col gap-2">
        {transactions?.map((t) => (
          <div key={t.id} className="flex items-center justify-between rounded-lg border border-night-700 bg-night-800 px-4 py-3 text-sm">
            <div>
              <p className="font-medium">
                {t.sender_name ? `To ${t.recipient_name}` : `Reward: ${t.recipient_name}`}
              </p>
              <p className="text-xs text-mist-500">{t.purpose.replace("_", " ")}</p>
            </div>
            <div className="text-right">
              <p className="font-display font-semibold">{t.amount} {t.currency}</p>
              <p className={`text-xs ${STATUS_COLOR[t.status] || "text-mist-500"}`}>{t.status}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
