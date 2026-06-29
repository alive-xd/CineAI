"use client";
// src/app/(auth)/register/page.tsx
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Film, Eye, EyeOff, Check, X, Sparkles } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";

function Rule({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className={cn("flex items-center gap-1.5 text-xs", ok ? "text-green-400" : "text-zinc-600")}>
      {ok ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
      {label}
    </div>
  );
}

export default function RegisterPage() {
  const router   = useRouter();
  const register = useAuthStore(s => s.register);

  const [form,    setForm]    = useState({ email: "", username: "", password: "" });
  const [showPw,  setShowPw]  = useState(false);
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(false);

  const pw    = form.password;
  const rules = { length: pw.length >= 8, uppercase: /[A-Z]/.test(pw), digit: /\d/.test(pw) };
  const valid = Object.values(rules).every(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!valid) { setError("Please meet all password requirements"); return; }
    setError("");
    setLoading(true);
    try {
      await register(form);
      router.push("/");
    } catch (err: any) {
      const d = err?.detail;
      setError(typeof d === "string" ? d : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ background: "var(--surface)" }}>

      {/* Left branding */}
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
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-brand" />
            <span className="text-xs text-zinc-500 uppercase tracking-widest font-medium">Free forever</span>
          </div>
          {[
            "AI semantic movie search",
            "Personalised hybrid recommendations",
            "Explainable AI taste profile",
            "Semantic mood-based discovery",
          ].map(f => (
            <div key={f} className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0"
                style={{ background: "rgba(34,197,94,0.12)" }}>
                <Check className="w-2.5 h-2.5 text-green-400" />
              </div>
              <span className="text-sm text-zinc-400">{f}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right form */}
      <div className="flex-1 flex items-center justify-center px-5 py-12">
        <div className="w-full max-w-sm">

          <Link href="/" className="flex items-center gap-2 mb-10 lg:hidden">
            <Film className="w-7 h-7 text-brand" />
            <span className="text-xl font-black">Cine<span className="text-brand">AI</span></span>
          </Link>

          <h1 className="text-2xl font-black mb-1">Create account</h1>
          <p className="text-zinc-500 text-sm mb-8">Start your AI movie journey</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="text-sm rounded-xl px-4 py-3"
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
              <label className="block text-xs font-medium text-zinc-400 mb-2 uppercase tracking-wide">Username</label>
              <input
                type="text" required minLength={3} maxLength={50} pattern="[a-zA-Z0-9_]+"
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                className="input-base"
                placeholder="cinephile42"
              />
              <p className="text-xs text-zinc-700 mt-1.5">Letters, numbers, underscores only</p>
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
                <button type="button" onClick={() => setShowPw(v => !v)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-zinc-300 transition-colors">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {form.password && (
                <div className="mt-2 space-y-1">
                  <Rule ok={rules.length}    label="At least 8 characters" />
                  <Rule ok={rules.uppercase} label="One uppercase letter" />
                  <Rule ok={rules.digit}     label="One number" />
                </div>
              )}
            </div>

            <button type="submit" disabled={loading || !valid} className="btn-primary w-full py-3 mt-2">
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="text-center text-sm text-zinc-600 mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-brand hover:underline font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
