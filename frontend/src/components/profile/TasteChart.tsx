"use client";
// src/components/profile/TasteChart.tsx
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";
import type { TasteProfile } from "@/types";

interface Props { profile: TasteProfile; }

export default function TasteChart({ profile }: Props) {
  const data = Object.entries(profile.genre_weights)
    .slice(0, 8)
    .map(([genre, weight]) => ({
      genre: genre.length > 10 ? genre.slice(0, 9) + "…" : genre,
      score: Math.round(weight * 100),
    }));

  if (data.length < 3) {
    return (
      <div className="flex items-center justify-center h-48 text-zinc-600 text-sm">
        Rate more movies to see your taste chart
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
        <PolarGrid stroke="rgba(255,255,255,0.06)" />
        <PolarAngleAxis
          dataKey="genre"
          tick={{ fill: "#52525b", fontSize: 11, fontFamily: "var(--font-inter)" }}
        />
        <Radar
          name="Affinity"
          dataKey="score"
          stroke="#E50914"
          fill="#E50914"
          fillOpacity={0.15}
          strokeWidth={1.5}
        />
        <Tooltip
          contentStyle={{
            background: "var(--surface-raised)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "12px",
            fontSize: "12px",
            color: "#fff",
            boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
          }}
          formatter={(v: number) => [`${v}%`, "Affinity"]}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
