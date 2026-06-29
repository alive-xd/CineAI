"use client";
// src/components/layout/Navbar.tsx
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { Film, Search, Bookmark, User, LogOut, ChevronDown, Sparkles, Home, Compass } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";

const NAV_LINKS = [
  { href: "/",       label: "Home",     icon: Home },
  { href: "/movies", label: "Movies",   icon: Film },
  { href: "/search", label: "Discover", icon: Compass },
];

export default function Navbar() {
  const pathname  = usePathname();
  const router    = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();

  const [scrolled,  setScrolled]  = useState(false);
  const [menuOpen,  setMenuOpen]  = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleLogout = async () => {
    setMenuOpen(false);
    await logout();
    router.push("/login");
  };

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-500",
        scrolled
          ? "glass-strong shadow-2xl shadow-black/40"
          : "bg-gradient-to-b from-black/80 via-black/30 to-transparent"
      )}
    >
      <nav className="max-w-screen-2xl mx-auto px-5 md:px-8 h-16 flex items-center gap-6">

        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0 group">
          <div className="relative w-8 h-8 flex items-center justify-center">
            <div className="absolute inset-0 bg-brand rounded-lg opacity-20 group-hover:opacity-40 transition-opacity blur-sm" />
            <Film className="w-5 h-5 text-brand relative z-10" />
          </div>
          <span className="text-lg font-black tracking-tight">
            Cine<span className="text-brand">AI</span>
          </span>
        </Link>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                  active
                    ? "text-white"
                    : "text-zinc-400 hover:text-white hover:bg-white/5"
                )}
              >
                {active && (
                  <span className="absolute inset-0 bg-white/8 rounded-lg" />
                )}
                <span className="relative">{label}</span>
                {active && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-brand" />
                )}
              </Link>
            );
          })}
        </div>

        <div className="flex-1" />

        {/* Right actions */}
        <div className="flex items-center gap-2">

          <Link
            href="/search"
            className="btn-icon"
            title="Search"
          >
            <Search className="w-4 h-4" />
          </Link>

          {isAuthenticated ? (
            <>
              <Link href="/watchlist" className="btn-icon" title="Watchlist">
                <Bookmark className="w-4 h-4" />
              </Link>

              {/* User menu */}
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setMenuOpen(v => !v)}
                  className={cn(
                    "flex items-center gap-2 pl-1 pr-2.5 py-1 rounded-xl transition-all duration-200",
                    "border border-transparent hover:border-white/10 hover:bg-white/5",
                    menuOpen && "border-white/10 bg-white/5"
                  )}
                >
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand to-brand-dark flex items-center justify-center text-xs font-bold shadow-lg shadow-brand/30">
                    {user?.username?.[0]?.toUpperCase()}
                  </div>
                  <ChevronDown
                    className={cn(
                      "w-3.5 h-3.5 text-zinc-400 transition-transform duration-200",
                      menuOpen && "rotate-180"
                    )}
                  />
                </button>

                {menuOpen && (
                  <div className="absolute right-0 mt-2 w-52 animate-slide-down">
                    <div className="glass-strong rounded-2xl overflow-hidden shadow-2xl shadow-black/60 border border-white/8">
                      {/* User info */}
                      <div className="px-4 py-3 border-b border-white/6">
                        <p className="text-sm font-semibold text-white">{user?.username}</p>
                        <p className="text-xs text-zinc-500 truncate mt-0.5">{user?.email}</p>
                      </div>

                      {/* Menu items */}
                      <div className="p-1.5 space-y-0.5">
                        <Link
                          href="/profile"
                          onClick={() => setMenuOpen(false)}
                          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-zinc-300 hover:text-white hover:bg-white/6 transition-all duration-150"
                        >
                          <Sparkles className="w-4 h-4 text-brand" />
                          <span>Taste Profile</span>
                        </Link>
                        <Link
                          href="/watchlist"
                          onClick={() => setMenuOpen(false)}
                          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-zinc-300 hover:text-white hover:bg-white/6 transition-all duration-150"
                        >
                          <Bookmark className="w-4 h-4 text-zinc-400" />
                          <span>Watchlist</span>
                        </Link>
                      </div>

                      <div className="p-1.5 border-t border-white/6">
                        <button
                          onClick={handleLogout}
                          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-red-400 hover:bg-red-500/10 transition-all duration-150"
                        >
                          <LogOut className="w-4 h-4" />
                          <span>Sign out</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login" className="btn-ghost text-sm py-2 px-4">
                Sign in
              </Link>
              <Link
                href="/register"
                className="btn-primary text-sm py-2 px-4"
              >
                Get started
              </Link>
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}
