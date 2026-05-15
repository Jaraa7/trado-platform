"use client";

import { motion } from "framer-motion";
import { Check, Star } from "lucide-react";
import { useState } from "react";

const tiers = [
  {
    name: "Micro",
    emoji: "🌱",
    price: { monthly: 29, annual: 290 },
    target: "$500 - $5,000",
    features: [
      "5 إشارات/يوم",
      "منصة واحدة",
      "جميع الـ 87 وكيل",
      "Telegram Bot",
      "Mobile App",
      "Knowledge Base كامل",
    ],
    cta: "ابدأ التجربة",
    popular: false,
  },
  {
    name: "Starter",
    emoji: "🚀",
    price: { monthly: 59, annual: 590 },
    target: "$2K - $20K",
    features: [
      "15 إشارة/يوم",
      "2 منصات",
      "Whale Tracker live",
      "Sentiment Dashboard",
      "Backtesting محدود",
      "Chat support 12h",
    ],
    cta: "اختر Starter",
    popular: false,
  },
  {
    name: "Pro",
    emoji: "💎",
    price: { monthly: 99, annual: 990 },
    target: "$10K - $100K",
    features: [
      "50 إشارة/يوم",
      "3 منصات",
      "Backtesting unlimited",
      "Custom Strategy Builder",
      "Portfolio Manager",
      "Live chat 1h response",
      "Weekly PDF Report",
    ],
    cta: "اختر Pro",
    popular: true,
    badge: "الأكثر شعبية",
  },
  {
    name: "Elite",
    emoji: "👑",
    price: { monthly: 199, annual: 1990 },
    target: "$50K - $500K",
    features: [
      "إشارات unlimited",
      "5 منصات",
      "Tax Reporting",
      "API Access",
      "1-on-1 Onboarding",
      "Priority 15min response",
      "Multi-portfolio",
    ],
    cta: "اختر Elite",
    popular: false,
  },
];

export function Pricing() {
  const [annual, setAnnual] = useState(false);

  return (
    <section id="pricing" className="py-32 px-6 relative">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <p className="text-emerald-400 text-sm font-mono mb-3 tracking-widest uppercase">
            الأسعار
          </p>
          <h2 className="font-display text-4xl md:text-5xl font-semibold mb-6">
            سعر يناسب طموحك
          </h2>
          <p className="text-lg text-ink-50/60 max-w-2xl mx-auto mb-8">
            8 باقات — من المبتدئ إلى الصناديق المؤسسية.
            جميع الـ 87 وكيل متاحون في كل باقة.
          </p>

          {/* Billing toggle */}
          <div className="inline-flex items-center gap-4 bg-white/5 rounded-full p-1.5">
            <button
              onClick={() => setAnnual(false)}
              className={`px-6 py-2 rounded-full text-sm font-semibold transition ${
                !annual ? "bg-emerald-500 text-ink-950" : "text-ink-50/60"
              }`}
            >
              شهري
            </button>
            <button
              onClick={() => setAnnual(true)}
              className={`px-6 py-2 rounded-full text-sm font-semibold transition flex items-center gap-2 ${
                annual ? "bg-emerald-500 text-ink-950" : "text-ink-50/60"
              }`}
            >
              سنوي
              <span className="text-xs px-2 py-0.5 rounded-full bg-gold-400 text-ink-950">
                وفّر 17%
              </span>
            </button>
          </div>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {tiers.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`relative rounded-2xl p-8 transition ${
                t.popular
                  ? "bg-gradient-to-b from-emerald-500/10 to-emerald-700/5 border-2 border-emerald-500/50 glow-emerald scale-105"
                  : "glass hover:bg-white/[0.06]"
              }`}
            >
              {t.popular && (
                <div className="absolute -top-3 right-1/2 translate-x-1/2 bg-gold-400 text-ink-950 px-4 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                  <Star size={12} fill="currentColor" />
                  {t.badge}
                </div>
              )}

              <div className="mb-6">
                <div className="text-3xl mb-2">{t.emoji}</div>
                <h3 className="font-display text-2xl font-semibold mb-1">{t.name}</h3>
                <p className="text-xs text-ink-50/50 font-mono">{t.target}</p>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold font-mono">
                    ${annual ? Math.floor(t.price.annual / 12) : t.price.monthly}
                  </span>
                  <span className="text-ink-50/50 text-sm">/شهر</span>
                </div>
                {annual && (
                  <p className="text-xs text-emerald-400 mt-1">
                    ${t.price.annual} سنوياً
                  </p>
                )}
              </div>

              <button
                className={`w-full py-3 rounded-xl font-semibold mb-6 transition ${
                  t.popular
                    ? "bg-emerald-500 hover:bg-emerald-400 text-ink-950"
                    : "bg-white/10 hover:bg-white/20 text-ink-50"
                }`}
              >
                {t.cta}
              </button>

              <ul className="space-y-3">
                {t.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <Check
                      size={16}
                      className="text-emerald-400 shrink-0 mt-0.5"
                    />
                    <span className="text-ink-50/80">{f}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-12 grid md:grid-cols-2 gap-6 max-w-3xl mx-auto"
        >
          <div className="glass rounded-xl p-6 text-center">
            <p className="text-2xl mb-2">🐋</p>
            <h4 className="font-display font-semibold mb-1">Whale + Institutional</h4>
            <p className="text-sm text-ink-50/60 mb-3">
              للمحافظ الكبيرة والصناديق ($200K - $5M+)
            </p>
            <p className="font-mono text-emerald-400 font-semibold">$499 - $1,499/شهر</p>
          </div>
          <div className="glass rounded-xl p-6 text-center">
            <p className="text-2xl mb-2">🌟</p>
            <h4 className="font-display font-semibold mb-1">Founder's Circle</h4>
            <p className="text-sm text-ink-50/60 mb-3">
              100 مقعد فقط — مزايا حصرية مدى الحياة
            </p>
            <p className="font-mono text-gold-400 font-semibold">$2,999/شهر</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
