import { useEffect, useState } from "react";
import { MatchingAPI } from "../api/resources";
import EmptyState from "../components/EmptyState.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ProfileCard from "../components/ProfileCard.jsx";

export default function Discover() {
  const [candidates, setCandidates] = useState(null);
  const [sentTo, setSentTo] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    MatchingAPI.discover()
      .then(setCandidates)
      .catch(() => setError("Could not load connections. Please try again."));
  }, []);

  async function handleConnect(userId) {
    try {
      const result = await MatchingAPI.sendRequest(userId);
      setSentTo((prev) => ({ ...prev, [userId]: result.match ? "matched" : "sent" }));
    } catch {
      setSentTo((prev) => ({ ...prev, [userId]: "error" }));
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <header className="mb-6">
        <h1 className="font-display text-2xl font-bold">Discover</h1>
        <p className="text-sm text-mist-500">Ranked by compatibility — location, shared interests, and age.</p>
      </header>

      {!candidates && !error && <LoadingState label="Finding your connections" />}
      {error && <p className="rounded-lg bg-red-950 p-3 text-sm text-red-300">{error}</p>}

      {candidates && candidates.length === 0 && (
        <EmptyState
          title="No new connections right now"
          body="Check back soon, or invite a friend to join ConnectLite."
        />
      )}

      <div className="flex flex-col gap-4">
        {candidates?.map((item) => {
          const state = sentTo[item.profile.id];
          return (
            <ProfileCard
              key={item.profile.id}
              profile={item.profile}
              score={item.compatibility_score}
              footer={
                <button
                  onClick={() => handleConnect(item.profile.id)}
                  disabled={!!state}
                  className="mt-1 self-start rounded-lg bg-signal px-4 py-2 text-sm font-semibold text-night-950 disabled:opacity-50"
                >
                  {state === "matched"
                    ? "It's a match! 🎉"
                    : state === "sent"
                    ? "Request sent"
                    : state === "error"
                    ? "Try again"
                    : "Connect"}
                </button>
              }
            />
          );
        })}
      </div>
    </div>
  );
}
