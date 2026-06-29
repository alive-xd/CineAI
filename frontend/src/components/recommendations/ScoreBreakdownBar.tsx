"use client";
// src/components/recommendations/ScoreBreakdownBar.tsx
import type { ScoreBreakdown } from "@/types";

interface Props { score: ScoreBreakdown; }

const SIGNALS = [
  { key: "semantic",      label: "Semantic AI",   colour: "#00d4ff", bg: "rgba(0,212,255,0.12)" },
  { key: "content",       label: "Content",        colour: "#a78bfa", bg: "rgba(167,139,250,0.12)" },
  { key: "collaborative", label: "Collaborative",  colour: "#34d399", bg: "rgba(52,211,153,0.12)" },
  { key: "popularity",    label: "Popularity",     colour: "#fbbf24", bg: "rgba(251,191,36,0.12)" },
] as const;

export default function ScoreBreakdownBar({ score }: Props) {
  return (
    <div className="space-y-2.5 rounded-2xl p-4" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-3">
        Why this recommendation
      </p>
      {SIGNALS.map(({ key, label, colour, bg }) => {
        const value = score[key];
        const pct = Math.round(value * 100);
        return (
          <div key={key}>
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full" style={{ background: colour }} />
                <span className="text-[11px] text-zinc-400">{label}</span>
              </div>
              <span className="text-[11px] font-mono font-semibold" style={{ color: colour }}>
                {pct}%
              </span>
            </div>
            <div className="h-1 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${pct}%`, background: colour }}
              />
            </div>
          </div>
        );
      })}
      <div className="pt-2 mt-1 border-t border-white/6 flex items-center justify-between">
        <span className="text-[11px] text-zinc-500">Overall match</span>
        <span className="text-sm font-black text-white">
          {Math.round(score.composite * 100)}%
        </span>
      </div>
    </div>
  );
}
