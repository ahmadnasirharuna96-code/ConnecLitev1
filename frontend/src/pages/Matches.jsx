import { useEffect, useState } from "react";
import { MessageCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { MatchingAPI } from "../api/resources";
import CompatibilityBadge from "../components/CompatibilityBadge.jsx";
import EmptyState from "../components/EmptyState.jsx";
import LoadingState from "../components/LoadingState.jsx";

export default function Matches() {
  const [matches, setMatches] = useState(null);
  const [requests, setRequests] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    MatchingAPI.matches().then(setMatches).catch(() => setMatches([]));
    MatchingAPI.connections("incoming").then(setRequests).catch(() => setRequests([]));
  }, []);

  async function respond(id, action) {
    await MatchingAPI.respond(id, action);
    setRequests((prev) => prev.filter((r) => r.id !== id));
    if (action === "accept") {
      MatchingAPI.matches().then(setMatches);
    }
  }

  const pendingIncoming = requests?.filter((r) => r.status === "pending") || [];

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 font-display text-2xl font-bold">Matches</h1>

      {pendingIncoming.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-mist-500">
            Connection requests
          </h2>
          <div className="flex flex-col gap-3">
            {pendingIncoming.map((r) => (
              <div key={r.id} className="flex items-center justify-between rounded-xl border border-night-700 bg-night-800 p-4">
                <div>
                  <p className="font-medium">{r.from_user.full_name}</p>
                  {r.compatibility_score_snapshot != null && (
                    <CompatibilityBadge score={r.compatibility_score_snapshot} />
                  )}
                </div>
                <div className="flex gap-2">
                  <button onClick={() => respond(r.id, "accept")} className="rounded-lg bg-pulse px-3 py-1.5 text-sm font-semibold text-night-950">
                    Accept
                  </button>
                  <button onClick={() => respond(r.id, "reject")} className="rounded-lg border border-night-600 px-3 py-1.5 text-sm">
                    Decline
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {!matches && <LoadingState label="Loading matches" />}
      {matches?.length === 0 && pendingIncoming.length === 0 && (
        <EmptyState title="No matches yet" body="Head to Discover to find compatible connections." />
      )}

      <div className="flex flex-col gap-3">
        {matches?.map((m) => (
          <div key={m.id} className="flex items-center justify-between rounded-xl border border-night-700 bg-night-800 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-night-600 font-display font-semibold">
                {m.other_user.full_name?.[0]}
              </div>
              <div>
                <p className="font-medium">{m.other_user.full_name}</p>
                <CompatibilityBadge score={m.compatibility_score} />
              </div>
            </div>
            <button
              onClick={() => navigate("/messages", { state: { userId: m.other_user.id } })}
              className="rounded-lg border border-night-600 p-2 text-mist-300 hover:text-signal"
              aria-label={`Message ${m.other_user.full_name}`}
            >
              <MessageCircle size={18} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
