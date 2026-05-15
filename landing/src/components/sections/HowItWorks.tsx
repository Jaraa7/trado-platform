"use client";

import { motion } from "framer-motion";

const steps = [
  {
    n: "01",
    title: "اشترك واربط منصتك",
    description: "ربط آمن مع Binance, Bybit, OKX — صلاحية قراءة وتداول فقط. لا نلمس أموالك أبداً.",
  },
  {
    n: "02",
    title: "الوكلاء يبدأون العمل",
    description: "Scanner يفحص السوق 24/7، Analyst يحلل، Risk Guardian يحمي، Executioner ينفذ.",
  },
  {
    n: "03",
    title: "أنت تتحكم بكل شيء",
    description: "اختر: تأكيد يدوي أو تنفيذ تلقائي. توقف في أي لحظة. عاين قبل وبعد كل صفقة.",
  },
];

export function HowItWorks() {
  return (
    <section className="py-32 px-6 bg-gradient-to-b from-transparent via-emerald-950/20 to-transparent">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-emerald-400 text-sm font-mono mb-3 tracking-widest uppercase">
            كيف يعمل
          </p>
          <h2 className="font-display text-4xl md:text-5xl font-semibold mb-6">
            ثلاث خطوات. هذا كل ما يلزم.
          </h2>
        </motion.div>

        <div className="space-y-8">
          {steps.map((s, i) => (
            <motion.div
              key={s.n}
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.2 }}
              className="flex items-start gap-8 glass rounded-2xl p-8"
            >
              <div className="font-display text-6xl font-bold text-emerald-400/30 leading-none">
                {s.n}
              </div>
              <div className="flex-1">
                <h3 className="font-display text-2xl font-semibold mb-3">{s.title}</h3>
                <p className="text-ink-50/70 leading-relaxed">{s.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
