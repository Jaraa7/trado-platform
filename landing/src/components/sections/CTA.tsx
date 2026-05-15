"use client";

import { motion } from "framer-motion";
import { ArrowLeft, Sparkles } from "lucide-react";
import { useState } from "react";

export function CTA() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  return (
    <section id="waitlist" className="py-32 px-6 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-mesh opacity-40" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-emerald-500/20 rounded-full blur-3xl" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="relative max-w-4xl mx-auto text-center"
      >
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8">
          <Sparkles className="w-4 h-4 text-gold-400" />
          <span className="text-sm text-ink-50/80">قائمة الانتظار مفتوحة</span>
        </div>

        <h2 className="font-display text-4xl md:text-6xl font-semibold mb-6 leading-tight">
          ابدأ التداول
          <br />
          <span className="gradient-text">بذكاء يفوق توقعاتك</span>
        </h2>

        <p className="text-lg text-ink-50/70 mb-10 max-w-xl mx-auto">
          انضم لأول 500 مستخدم واحصل على خصم 30% مدى الحياة + شهر مجاني من Pro tier.
        </p>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            setSubmitted(true);
          }}
          className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto mb-8"
        >
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            required
            className="flex-1 px-5 py-4 rounded-xl bg-white/5 border border-white/10 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-400/20 placeholder:text-ink-50/40 text-center sm:text-right"
          />
          <button
            type="submit"
            disabled={submitted}
            className="px-8 py-4 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-400 hover:from-emerald-400 hover:to-emerald-300 text-ink-950 font-bold flex items-center justify-center gap-2 transition glow-emerald disabled:opacity-50"
          >
            {submitted ? "✓ تم! نراك قريباً" : (
              <>احجز مكانك <ArrowLeft size={18} /></>
            )}
          </button>
        </form>

        <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-ink-50/50">
          <span>✓ بدون بطاقة ائتمان</span>
          <span>✓ 7 أيام تجربة كاملة</span>
          <span>✓ إلغاء فوري في أي وقت</span>
        </div>
      </motion.div>
    </section>
  );
}
