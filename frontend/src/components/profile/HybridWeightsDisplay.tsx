"use client";
// src/components/profile/HybridWeightsDisplay.tsx

interface Props {
  weights: { semantic: number; content: number; collaborative: number; popularity: number };
}

const SIGNALS = [
  { key: "semantic",      label: "Semantic AI",    desc: "Embedding-space similarity",     colour: "#00d4ff", bg: "rgba(0,212,255,0.1)"  },
  { key: "content",       label: "Content",         desc: "Genre, director, cast",          colour: "#a78bfa", bg: "rgba(167,139,250,0.1)" },
  { key: "collaborative", label: "Collaborative",   desc: "Users with similar taste",       colour: "#34d399", bg: "rgba(52,211,153,0.1)"  },
  { key: "popularity",    label: "Popularity",      desc: "Critically acclaimed & trending", colour: "#fbbf24", bg: "rgba(251,191,36,0.1)"  },
] as const;

export default function HybridWeightsDisplay({ weights }: Props) {
  return (
    <div className="space-y-4">
      {SIGNALS.map(({ key, label, desc, colour, bg }) => {
        const pct = Math.round((weights[key] ?? 0) * 100);
        return (
          <div key={key}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-lg flex items-center justify-center shrink-0"
                  style={{ background: bg }}>
                  <div className="w-1.5 h-1.5 rounded-full" style={{ background: colour }} />
                </div>
                <div>
                  <span className="text-sm font-medium text-white">{label}</span>
                  <span className="ml-2 text-xs text-zinc-600">{desc}</span>
                </div>
              </div>
              <span className="text-xs font-mono font-semibold" style={{ color: colour }}>{pct}%</span>
            </div>
            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${pct}%`, background: colour }}
              />
            </div>
          </div>
        );
      })}
      <p className="text-xs text-zinc-700 pt-1">
        Weights shift automatically as you interact with recommendations.
      </p>
    </div>
  );
}
