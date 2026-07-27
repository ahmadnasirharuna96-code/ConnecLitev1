import { useEffect, useState } from "react";
import { Plus, Users } from "lucide-react";
import { CommunitiesAPI } from "../api/resources";
import EmptyState from "../components/EmptyState.jsx";
import LoadingState from "../components/LoadingState.jsx";

const CATEGORIES = ["university", "technology", "business", "professional", "interest", "local", "other"];

export default function Communities() {
  const [communities, setCommunities] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", category: "other" });

  function load() {
    CommunitiesAPI.list().then(setCommunities).catch(() => setCommunities([]));
  }

  useEffect(load, []);

  async function toggleMembership(c) {
    if (c.is_member) await CommunitiesAPI.leave(c.id);
    else await CommunitiesAPI.join(c.id);
    load();
  }

  async function handleCreate(e) {
    e.preventDefault();
    await CommunitiesAPI.create(form);
    setForm({ name: "", description: "", category: "other" });
    setShowCreate(false);
    load();
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">Communities</h1>
          <p className="text-sm text-mist-500">University groups, tech circles, and local networks.</p>
        </div>
        <button
          onClick={() => setShowCreate((v) => !v)}
          className="flex items-center gap-1 rounded-lg bg-signal px-3 py-2 text-sm font-semibold text-night-950"
        >
          <Plus size={16} /> New
        </button>
      </header>

      {showCreate && (
        <form onSubmit={handleCreate} className="mb-6 flex flex-col gap-3 rounded-xl border border-night-700 bg-night-800 p-4">
          <input
            required
            placeholder="Community name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="rounded-lg bg-night-700 px-3 py-2 text-sm outline-none"
          />
          <textarea
            placeholder="Description"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="rounded-lg bg-night-700 px-3 py-2 text-sm outline-none"
          />
          <select
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            className="rounded-lg bg-night-700 px-3 py-2 text-sm outline-none"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <button type="submit" className="self-start rounded-lg bg-pulse px-4 py-2 text-sm font-semibold text-night-950">
            Create community
          </button>
        </form>
      )}

      {!communities && <LoadingState label="Loading communities" />}
      {communities?.length === 0 && <EmptyState title="No communities yet" body="Be the first to create one." />}

      <div className="flex flex-col gap-3">
        {communities?.map((c) => (
          <div key={c.id} className="rounded-xl border border-night-700 bg-night-800 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-display font-semibold">{c.name}</p>
                <p className="text-xs uppercase tracking-wide text-mist-500">{c.category}</p>
              </div>
              <button
                onClick={() => toggleMembership(c)}
                className={`shrink-0 rounded-lg px-3 py-1.5 text-sm font-semibold ${
                  c.is_member ? "border border-night-600 text-mist-300" : "bg-signal text-night-950"
                }`}
              >
                {c.is_member ? "Leave" : "Join"}
              </button>
            </div>
            {c.description && <p className="mt-2 text-sm text-mist-300">{c.description}</p>}
            <p className="mt-2 flex items-center gap-1 text-xs text-mist-500">
              <Users size={14} /> {c.member_count} member{c.member_count === 1 ? "" : "s"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
