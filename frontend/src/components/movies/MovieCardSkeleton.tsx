// src/components/movies/MovieCardSkeleton.tsx
export default function MovieCardSkeleton() {
  return (
    <div className="rounded-2xl overflow-hidden border border-white/5" style={{ background: "var(--surface-card)" }}>
      <div className="aspect-[2/3] skeleton" />
      <div className="p-3 space-y-2">
        <div className="h-3 skeleton rounded-full w-4/5" />
        <div className="flex gap-1.5 mt-2">
          <div className="h-4 skeleton rounded-full w-12" />
          <div className="h-4 skeleton rounded-full w-14" />
        </div>
      </div>
    </div>
  );
}
