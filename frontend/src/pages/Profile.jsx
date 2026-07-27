import { useEffect, useState } from "react";
import { Settings as SettingsIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { ProfileAPI } from "../api/resources";
import LoadingState from "../components/LoadingState.jsx";

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [interests, setInterests] = useState([]);
  const [form, setForm] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    ProfileAPI.getMine().then((data) => {
      setProfile(data);
      setForm({
        bio: data.bio || "",
        occupation: data.occupation || "",
        location: data.location || "",
        interest_ids: data.interests.map((i) => i.id),
      });
    });
    ProfileAPI.listInterests().then(setInterests);
  }, []);

  function toggleInterest(id) {
    setForm((prev) => ({
      ...prev,
      interest_ids: prev.interest_ids.includes(id)
        ? prev.interest_ids.filter((i) => i !== id)
        : [...prev.interest_ids, id],
    }));
  }

  async function handleSave(e) {
    e.preventDefault();
    const updated = await ProfileAPI.update(form);
    setProfile(updated);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  if (!profile || !form) return <LoadingState label="Loading profile" />;

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">My Profile</h1>
          <p className="text-sm text-mist-500">
            {profile.phone_number} · {profile.verification_status === "verified" ? "✅ Verified" : "Unverified"}
          </p>
        </div>
        <Link to="/settings" className="rounded-lg border border-night-600 p-2 text-mist-300 hover:text-signal">
          <SettingsIcon size={18} />
        </Link>
      </header>

      <form onSubmit={handleSave} className="flex flex-col gap-4">
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wide text-mist-500">Bio</label>
          <textarea
            value={form.bio}
            onChange={(e) => setForm({ ...form, bio: e.target.value })}
            maxLength={500}
            rows={3}
            className="w-full rounded-lg bg-night-800 px-3 py-2 text-sm outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wide text-mist-500">Occupation</label>
          <input
            value={form.occupation}
            onChange={(e) => setForm({ ...form, occupation: e.target.value })}
            className="w-full rounded-lg bg-night-800 px-3 py-2 text-sm outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wide text-mist-500">Location</label>
          <input
            value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
            className="w-full rounded-lg bg-night-800 px-3 py-2 text-sm outline-none"
          />
        </div>
        <div>
          <label className="mb-2 block text-xs uppercase tracking-wide text-mist-500">Interests</label>
          <div className="flex flex-wrap gap-2">
            {interests.map((interest) => {
              const active = form.interest_ids.includes(interest.id);
              return (
                <button
                  type="button"
                  key={interest.id}
                  onClick={() => toggleInterest(interest.id)}
                  className={`rounded-full border px-3 py-1 text-xs font-medium ${
                    active ? "border-signal bg-signal/10 text-signal" : "border-night-600 text-mist-500"
                  }`}
                >
                  {interest.name}
                </button>
              );
            })}
          </div>
        </div>
        <button className="self-start rounded-lg bg-signal px-5 py-2 text-sm font-semibold text-night-950">
          {saved ? "Saved ✓" : "Save changes"}
        </button>
      </form>
    </div>
  );
}
