"use client";

import { motion } from "framer-motion";
import { ArrowLeft, Sparkles, TrendingUp, Shield } from "lucide-react";
import { useState } from "react";

export function Hero() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    // TODO: connect to backend
    setSubmitted(true);
    setTimeout(() => {
      setEmail("");
      setSubmitted(false);
    }, 3000);
  };

  return (
    <section className="relative min-h-screen flex items-center pt-24 pb-16 px-6 overflow-hidden">
      {/* Background gradient mesh */}
      <div className="absolute inset-0 bg-mesh opacity-60" />

      {/* Animated grid */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(to right, white 1px, transparent 1px), linear-gradient(to bottom, white 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* Floating orbs */}
      <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-emerald-500/20 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-gold-400/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: "2s" }} />

      <div className="relative max-w-7xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Right side - Text */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-right"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8"
            >
              <Sparkles className="w-4 h-4 text-gold-400" />
              <span className="text-sm text-ink-50/80">
                87 وكيل ذكاء اصطناعي يعمل 24/7
              </span>
            </motion.div>

            <h1 className="font-display text-5xl md:text-6xl lg:text-7xl font-semibold leading-[1.1] mb-6 tracking-tight">
              تداول بـ
              <span className="gradient-text"> ذكاء استثنائي</span>
              <br />
              <span className="text-ink-50/60 text-4xl md:text-5xl font-normal">
                ليس مجرد بوت آخر
              </span>
            </h1>

            <p className="text-lg text-ink-50/70 mb-8 max-w-xl mr-0 leading-relaxed">
              فريق من <span className="text-emerald-400 font-semibold">87 وكيل AI</span> يحلل السوق،
              يكتشف الفرص، يحمي رأس مالك من المخاطر —
              مصمم خصيصاً للمتداول العربي.
            </p>

            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mb-8">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="بريدك الإلكتروني"
                required
                className="flex-1 px-5 py-4 rounded-xl bg-white/5 border border-white/10 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-400/20 transition placeholder:text-ink-50/40 text-right"
              />
              <button
                type="submit"
                disabled={submitted}
                className="px-6 py-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-ink-950 font-semibold flex items-center justify-center gap-2 transition glow-emerald disabled:opacity-50"
              >
                {submitted ? (
                  "✓ تم التسجيل!"
                ) : (
                  <>
                    انضم للقائمة <ArrowLeft size={18} />
                  </>
                )}
              </button>
            </form>

            <div className="flex flex-wrap items-center gap-6 text-sm text-ink-50/60">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                500+ في قائمة الانتظار
              </div>
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-400" />
                بدون بطاقة ائتمان
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-gold-400" />
                7 أيام تجربة
              </div>
            </div>
          </motion.div>

          {/* Left side - Visual */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="relative"
          >
            <div className="relative glass rounded-2xl p-8 glow-emerald">
              {/* Mock dashboard */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/60" />
                  <div className="w-3 h-3 rounded-full bg-gold-400/60" />
                  <div className="w-3 h-3 rounded-full bg-emerald-400/60" />
                </div>
                <span className="text-xs text-ink-50/40 font-mono">tradoai.net</span>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-ink-50/50 mb-1">BTC/USDT</p>
                    <p className="font-mono text-2xl font-semibold ticker">$102,142.50</p>
                  </div>
                  <div className="text-left">
                    <p className="text-xs text-emerald-400 mb-1">+2.45%</p>
                    <p className="text-xs text-ink-50/50">24h</p>
                  </div>
                </div>

                {/* Mock chart */}
                <svg viewBox="0 0 400 120" className="w-full">
                  <defs>
                    <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
                      <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <path
                    d="M0,80 Q50,60 100,70 T200,40 T300,30 T400,20 L400,120 L0,120 Z"
                    fill="url(#chartGrad)"
                  />
                  <path
                    d="M0,80 Q50,60 100,70 T200,40 T300,30 T400,20"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2"
                  />
                </svg>

                {/* AI Signal Card */}
                <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/30 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-emerald-400" />
                      <span className="text-sm font-semibold text-emerald-400">
                        إشارة AI جديدة
                      </span>
                    </div>
                    <span className="text-xs text-ink-50/50 font-mono">منذ ثانية</span>
                  </div>
                  <p className="text-sm text-ink-50/80 mb-3">
                    شراء BTC عند $102,142 — هدف $108,000 — وقف $99,800
                  </p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="rounded bg-white/5 p-2 text-center">
                      <p className="text-ink-50/50">الثقة</p>
                      <p className="font-mono font-semibold text-emerald-400">87%</p>
                    </div>
                    <div className="rounded bg-white/5 p-2 text-center">
                      <p className="text-ink-50/50">R:R</p>
                      <p className="font-mono font-semibold">2.5x</p>
                    </div>
                    <div className="rounded bg-white/5 p-2 text-center">
                      <p className="text-ink-50/50">المخاطرة</p>
                      <p className="font-mono font-semibold">2%</p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-ink-50/60">
                  <span>87 وكيل نشط</span>
                  <div className="flex items-center gap-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Live
                  </div>
                </div>
              </div>
            </div>

            {/* Floating badges */}
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity }}
              className="absolute -top-4 -right-4 glass rounded-xl px-4 py-3"
            >
              <p className="text-xs text-ink-50/60 mb-1">معدل الربح</p>
              <p className="font-mono text-lg font-semibold text-emerald-400">+47.3%</p>
            </motion.div>

            <motion.div
              animate={{ y: [0, 10, 0] }}
              transition={{ duration: 5, repeat: Infinity }}
              className="absolute -bottom-4 -left-4 glass rounded-xl px-4 py-3"
            >
              <p className="text-xs text-ink-50/60 mb-1">دقة الإشارات</p>
              <p className="font-mono text-lg font-semibold text-gold-400">73.8%</p>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
