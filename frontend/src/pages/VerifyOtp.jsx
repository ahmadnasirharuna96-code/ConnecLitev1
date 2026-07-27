import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function VerifyOtp() {
  const { verifyOtp, requestOtp } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const phoneFromState = location.state?.phone_number || "";
  const purpose = location.state?.purpose || "registration";

  const [phone_number, setPhone] = useState(phoneFromState);
  const [code, setCode] = useState("");
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await verifyOtp(phone_number, code, purpose);
      navigate("/discover");
    } catch (err) {
      setError(err.response?.data?.error || "Invalid or expired code.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setError(null);
    setInfo(null);
    try {
      await requestOtp(phone_number, purpose);
      setInfo("A new code has been sent.");
    } catch (err) {
      setError(err.response?.data?.error || "Could not resend code — please wait a moment and try again.");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6 text-mist-100">
      <h1 className="font-display text-2xl font-bold">Verify your phone number</h1>
      <p className="text-sm text-mist-500">
        Enter the code we sent to your phone via SMS.
      </p>
      {error && <p className="rounded-lg bg-red-950 p-2 text-sm text-red-300">{error}</p>}
      {info && <p className="rounded-lg bg-pulse/10 p-2 text-sm text-pulse">{info}</p>}
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input
          placeholder="Phone number"
          required
          value={phone_number}
          onChange={(e) => setPhone(e.target.value)}
          className="rounded-lg bg-night-800 px-3 py-2 outline-none"
        />
        <input
          placeholder="6-digit code"
          required
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className="rounded-lg bg-night-800 px-3 py-2 tracking-widest outline-none"
        />
        <button disabled={submitting} className="rounded-lg bg-signal p-2 font-semibold text-night-950 disabled:opacity-50">
          {submitting ? "Verifying…" : "Verify"}
        </button>
      </form>
      <button onClick={handleResend} className="text-sm text-signal underline">
        Resend code
      </button>
    </main>
  );
}
