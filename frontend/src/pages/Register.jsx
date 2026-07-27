import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const initialForm = {
  phone_number: "",
  email: "",
  password: "",
  full_name: "",
  date_of_birth: "",
  gender: "",
  location: "",
  referred_by_code: "",
};

export default function Register() {
  const { register, requestOtp } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(form);
      await requestOtp(form.phone_number, "registration");
      navigate("/verify-otp", { state: { phone_number: form.phone_number, purpose: "registration" } });
    } catch (err) {
      setError(err.response?.data?.error || "Registration failed. Please check your details.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6 py-10 text-mist-100">
      <h1 className="font-display text-2xl font-bold">Create your ConnectLite account</h1>
      {error && <p className="rounded-lg bg-red-950 p-2 text-sm text-red-300">{error}</p>}
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input name="full_name" placeholder="Full name" required onChange={handleChange} className="rounded-lg bg-night-800 px-3 py-2 outline-none" />
        <input name="phone_number" placeholder="Phone number (+234...)" required onChange={handleChange} className="rounded-lg bg-night-800 px-3 py-2 outline-none" />
        <input name="email" type="email" placeholder="Email (optional)" onChange={handleChange} className="rounded-lg bg-night-800 px-3 py-2 outline-none" />
        <input name="password" type="password" placeholder="Password" required onChange={handleChange} className="rounded-lg bg-night-800 px-3 py-2 outline-none" />
        <input name="date_of_birth" type="date" onChange={handleChange} className="rounded-lg bg-night-800 px-3 py-2 outline-none" />
        <select name="gender" onChange={handleChange} className="rounded-lg bg-night-800 px-3 py-2 outline-none">
          <option value="">Select gender</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
          <option value="prefer_not_to_say">Prefer not to say</option>
        </select>
        <input name="location" placeholder="Location" onChange={handleChange} className="rounded-lg bg-night-800 px-3 py-2 outline-none" />
        <input
          name="referred_by_code"
          placeholder="Referral code (optional)"
          onChange={handleChange}
          className="rounded-lg bg-night-800 px-3 py-2 uppercase outline-none placeholder:normal-case"
        />
        <button disabled={submitting} className="rounded-lg bg-signal p-2 font-semibold text-night-950 disabled:opacity-50">
          {submitting ? "Creating account…" : "Register"}
        </button>
      </form>
    </main>
  );
}
