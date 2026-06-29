"use client";
// src/app/(main)/layout.tsx
// Shared layout for authenticated-preferred pages.
// Individual pages handle their own empty/login states.
export default function MainLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
