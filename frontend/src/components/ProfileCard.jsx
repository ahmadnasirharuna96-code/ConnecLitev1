import CompatibilityBadge from "./CompatibilityBadge.jsx";

export default function ProfileCard({ profile, score, footer }) {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-night-700 bg-night-800 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-night-600 font-display text-lg font-semibold text-mist-100">
            {profile.full_name?.[0] || "?"}
          </div>
          <div>
            <p className="font-display font-semibold">{profile.full_name}{profile.age ? `, ${profile.age}` : ""}</p>
            <p className="text-xs text-mist-500">{profile.location || "Location not set"}</p>
          </div>
        </div>
        {typeof score === "number" && <CompatibilityBadge score={score} />}
      </div>
      {profile.bio && <p className="text-sm text-mist-300">{profile.bio}</p>}
      {profile.interests?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {profile.interests.map((interest) => (
            <span key={interest.id} className="rounded-full bg-night-700 px-2 py-0.5 text-xs text-mist-300">
              {interest.name}
            </span>
          ))}
        </div>
      )}
      {footer}
    </div>
  );
}
