"use client";

import { motion } from "framer-motion";

const departments = [
  { name: "التداول الذكي", count: 15, icon: "📊", color: "emerald" },
  { name: "الهندسة", count: 10, icon: "⚙️", color: "blue" },
  { name: "الأمن", count: 7, icon: "🛡️", color: "red" },
  { name: "المالية", count: 12, icon: "💎", color: "gold" },
  { name: "خدمة العملاء", count: 11, icon: "💬", color: "purple" },
  { name: "التسويق", count: 12, icon: "📢", color: "pink" },
  { name: "التصميم", count: 7, icon: "🎨", color: "amber" },
  { name: "المنتج", count: 7, icon: "🎯", color: "teal" },
  { name: "العمليات", count: 6, icon: "⚡", color: "coral" },
];

const totalAgents = departments.reduce((sum, d) => sum + d.count, 0);

export function Agents() {
  return (
    <section id="agents" className="py-32 px-6 relative">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-emerald-400 text-sm font-mono mb-3 tracking-widest uppercase">
            فريقك الذكي
          </p>
          <h2 className="font-display text-4xl md:text-5xl font-semibold mb-6">
            <span className="gradient-text">{totalAgents}</span> وكيل يعمل لأجلك
          </h2>
          <p className="text-lg text-ink-50/60 max-w-2xl mx-auto">
            موزعون على 9 أقسام متخصصة. كل وكيل يتقن دوره. النتيجة: تداول احترافي من فريق كامل بسعر فرد.
          </p>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {departments.map((d, i) => (
            <motion.div
              key={d.name}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              className="glass rounded-xl p-6 hover:bg-white/[0.06] transition group cursor-default"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-3xl">{d.icon}</span>
                <span className="font-mono text-2xl font-semibold text-emerald-400">
                  {d.count}
                </span>
              </div>
              <p className="text-sm font-semibold mb-1">{d.name}</p>
              <p className="text-xs text-ink-50/50">وكيل متخصص</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-12 text-center"
        >
          <p className="text-ink-50/50 text-sm">
            كل وكيل يستخدم Claude Sonnet 4.5 — أحدث نموذج ذكاء اصطناعي في العالم
          </p>
        </motion.div>
      </div>
    </section>
  );
}
