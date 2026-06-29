"use client";
// src/app/(auth)/login/page.tsx
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Film, Eye, EyeOff, Sparkles } from "lucide-react";
import { useAuthStore } from "@/store/authStore";

export default function LoginPage() {
  const router = useRouter();
  const login  = useAuthStore(s => s.login);

  const [form,    setForm]    = useState({ email: "", password: "" });
  const [showPw,  setShowPw]  = useState(false);
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form);
      router.push("/");
    } catch (err: any) {
      setError(err?.detail ?? "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ background: "var(--surface)" }}>

      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden"
        style={{ background: "var(--surface-card)", borderRight: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse at 30% 70%, rgba(229,9,20,0.06) 0%, transparent 60%)" }} />
        <Link href="/" className="flex items-center gap-2.5 relative z-10">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: "rgba(229,9,20,0.15)" }}>
            <Film className="w-5 h-5 text-brand" />
          </div>
          <span className="text-xl font-black">Cine<span className="text-brand">AI</span></span>
        </Link>
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-brand" />
            <span className="text-xs text-zinc-500 uppercase tracking-widest font-medium">AI-powered</span>
          </div>
          <h2 className="text-3xl font-black leading-tight mb-3">
            Discover movies <br />that match your taste
          </h2>
          <p className="text-zinc-500 text-sm leading-relaxed max-w-xs">
            Semantic search, personalised recommendations, and explainable AI — built for cinephiles.
          </p>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center px-5 py-12">
        <div className="w-full max-w-sm">

          {/* Mobile logo */}
          <Link href="/" className="flex items-center gap-2 mb-10 lg:hidden">
            <Film className="w-7 h-7 text-brand" />
            <span className="text-xl font-black">Cine<span className="text-brand">AI</span></span>
          </Link>

          <h1 className="text-2xl font-black mb-1">Welcome back</h1>
          <p className="text-zinc-500 text-sm mb-8">Sign in to your account</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="text-sm rounded-xl px-4 py-3 animate-in slide-in-from-top-2 duration-300"
                style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", color: "#f87171" }}>
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-2 uppercase tracking-wide">Email</label>
              <input
                type="email" required autoFocus
                value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                className="input-base"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-2 uppercase tracking-wide">Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"} required
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  className="input-base pr-11"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(v => !v)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-zinc-300 transition-colors"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 mt-2"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="text-center text-sm text-zinc-600 mt-6">
            No account?{" "}
            <Link href="/register" className="text-brand hover:underline font-medium">Create one free</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
