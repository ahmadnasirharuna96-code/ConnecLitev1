import { ArrowRight, Smartphone } from "lucide-react";
import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <main className="min-h-screen bg-night-900 text-mist-100">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16">
        <div className="mb-6 flex items-center gap-2 text-signal">
          <span className="signal-bars"><span></span><span></span><span></span><span></span></span>
          <span className="text-sm font-semibold uppercase tracking-widest">ConnectLite</span>
        </div>

        <h1 className="font-display max-w-3xl text-4xl font-bold leading-tight sm:text-6xl">
          Connect with people,{" "}
          <span className="text-signal">even without internet.</span>
        </h1>

        <p className="mt-6 max-w-xl text-lg text-mist-300">
          Dating, friendship, and community — for everyone, not just the connected.
          Smartphone or feature phone. Web, USSD, or SMS.
        </p>

        <div className="mt-10 flex flex-wrap gap-4">
          <Link
            to="/register"
            className="flex items-center gap-2 rounded-lg bg-signal px-6 py-3 font-semibold text-night-950 transition hover:bg-signal-soft"
          >
            Get started <ArrowRight size={18} />
          </Link>
          <Link
            to="/login"
            className="rounded-lg border border-night-600 px-6 py-3 font-semibold text-mist-100 hover:border-mist-500"
          >
            Log in
          </Link>
        </div>

        {/* Signature element: the smartphone <-> feature-phone connectivity bridge */}
        <div className="mt-16 grid max-w-2xl grid-cols-[1fr_auto_1fr] items-center gap-4 rounded-2xl border border-night-700 bg-night-800 p-6">
          <div className="flex flex-col items-center gap-2 text-center">
            <Smartphone size={28} className="text-pulse" />
            <p className="text-sm font-medium">Smartphone</p>
            <p className="text-xs text-mist-500">Full app experience</p>
          </div>
          <div className="flex flex-col items-center gap-1 text-signal">
            <span className="signal-bars"><span></span><span></span><span></span><span></span></span>
            <p className="text-[10px] uppercase tracking-widest">SMS · USSD</p>
          </div>
          <div className="flex flex-col items-center gap-2 text-center">
            <span className="font-display text-2xl">☎</span>
            <p className="text-sm font-medium">Feature phone</p>
            <p className="text-xs text-mist-500">USSD & SMS access</p>
          </div>
        </div>
      </div>
    </main>
  );
}
