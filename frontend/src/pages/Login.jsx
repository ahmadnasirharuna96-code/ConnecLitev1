import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [phone_number, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(phone_number, password);
      navigate("/discover");
    } catch (err) {
      setError(err.response?.data?.error || "Login failed. Check your phone number and password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6 text-mist-100">
      <h1 className="font-display text-2xl font-bold">Log in to ConnectLite</h1>
      {error && <p className="rounded-lg bg-red-950 p-2 text-sm text-red-300">{error}</p>}
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input
          placeholder="Phone number (+234...)"
          required
          value={phone_number}
          onChange={(e) => setPhone(e.target.value)}
          className="rounded-lg bg-night-800 px-3 py-2 outline-none"
        />
        <input
          type="password"
          placeholder="Password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="rounded-lg bg-night-800 px-3 py-2 outline-none"
        />
        <button disabled={submitting} className="rounded-lg bg-signal p-2 font-semibold text-night-950 disabled:opacity-50">
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>
      <p className="text-sm text-mist-500">
        New here? <Link to="/register" className="text-signal">Create an account</Link>
      </p>
    </main>
  );
}
