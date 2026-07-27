import { LogOut, Phone, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import { VoiceAPI } from "../api/resources";
import { useState } from "react";

export default function Settings() {
  const { user, logout } = useAuth();
  const [voiceStatus, setVoiceStatus] = useState(null);

  async function handleVoiceVerify() {
    const result = await VoiceAPI.startVerification();
    setVoiceStatus(result.status);
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 font-display text-2xl font-bold">Settings</h1>

      <div className="mb-4 flex items-center gap-3 rounded-xl border border-night-700 bg-night-800 p-4">
        <Phone size={18} className="text-signal" />
        <div>
          <p className="text-sm font-medium">{user?.phone_number}</p>
          <p className="text-xs text-mist-500">Registered via {user?.registration_channel === "ussd" ? "USSD" : "Web"}</p>
        </div>
      </div>

      {user?.referral_code && (
        <div className="mb-4 flex items-center justify-between rounded-xl border border-night-700 bg-night-800 p-4">
          <div>
            <p className="text-sm font-medium">Your referral code</p>
            <p className="text-xs text-mist-500">Share it — you both get an airtime reward once they verify.</p>
          </div>
          <span className="rounded-lg bg-night-700 px-3 py-1.5 font-display font-semibold tracking-widest text-signal">
            {user.referral_code}
          </span>
        </div>
      )}

      <div className="mb-6 flex items-center justify-between rounded-xl border border-night-700 bg-night-800 p-4">
        <div className="flex items-center gap-3">
          <ShieldCheck size={18} className="text-signal" />
          <div>
            <p className="text-sm font-medium">Phone verification</p>
            <p className="text-xs text-mist-500">
              {user?.is_phone_verified ? "Verified" : voiceStatus === "verified" ? "Verified via voice call" : "Not verified"}
            </p>
          </div>
        </div>
        {!user?.is_phone_verified && voiceStatus !== "verified" && (
          <button onClick={handleVoiceVerify} className="rounded-lg border border-night-600 px-3 py-1.5 text-xs">
            Verify by call
          </button>
        )}
      </div>

      <button
        onClick={logout}
        className="flex items-center gap-2 rounded-lg border border-red-900 px-4 py-2 text-sm font-semibold text-red-400"
      >
        <LogOut size={16} /> Log out
      </button>
    </div>
  );
}
