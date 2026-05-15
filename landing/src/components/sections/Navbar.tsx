"use client";

import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const links = [
    { href: "#features", label: "المزايا" },
    { href: "#agents", label: "الوكلاء" },
    { href: "#pricing", label: "الأسعار" },
    { href: "#faq", label: "الأسئلة" },
  ];

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-ink-975/85 backdrop-blur-xl border-b border-white/5"
          : "bg-transparent"
      }`}
    >
      <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <a href="/" className="flex items-center gap-2 group">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center font-display font-bold text-white group-hover:scale-105 transition">
            T
          </div>
          <span className="font-display text-xl font-semibold tracking-tight">
            Trado<span className="text-emerald-400">AI</span>
          </span>
        </a>

        <div className="hidden md:flex items-center gap-8">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm text-ink-50/70 hover:text-emerald-400 transition"
            >
              {l.label}
            </a>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-3">
          <a
            href="#login"
            className="text-sm px-4 py-2 text-ink-50/80 hover:text-emerald-400 transition"
          >
            تسجيل الدخول
          </a>
          <a
            href="#waitlist"
            className="text-sm px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-ink-950 font-semibold transition glow-emerald"
          >
            ابدأ الآن
          </a>
        </div>

        <button
          onClick={() => setOpen(!open)}
          className="md:hidden p-2"
          aria-label="Menu"
        >
          {open ? <X size={24} /> : <Menu size={24} />}
        </button>
      </nav>

      {open && (
        <div className="md:hidden bg-ink-950 border-t border-white/5 px-6 py-4 space-y-3">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="block py-2 text-ink-50/70 hover:text-emerald-400"
            >
              {l.label}
            </a>
          ))}
          <a
            href="#waitlist"
            className="block py-3 text-center rounded-lg bg-emerald-500 text-ink-950 font-semibold"
          >
            ابدأ الآن
          </a>
        </div>
      )}
    </header>
  );
}
