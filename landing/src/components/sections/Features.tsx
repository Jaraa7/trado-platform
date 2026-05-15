"use client";

import { motion } from "framer-motion";
import { Brain, Shield, Zap, BarChart3, Bell, Globe } from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "87 وكيل AI متخصص",
    description: "كل وكيل خبير في مجاله: التحليل الفني، المخاطر، الأخبار، الحيتان — يعملون كفريق واحد",
    color: "emerald",
  },
  {
    icon: Shield,
    title: "حماية رأس المال أولاً",
    description: "Risk Guardian يفحص كل صفقة قبل التنفيذ. حد 2% لكل صفقة، 6% خسارة يومية، 3x رافعة كحد أقصى",
    color: "blue",
  },
  {
    icon: Zap,
    title: "إشارات في ثوانٍ",
    description: "Scanner Pro يفحص 500+ زوج كل دقيقة، Analyst Master يحلل في 30 ثانية بأقل من 4 سنتات",
    color: "gold",
  },
  {
    icon: BarChart3,
    title: "تحليل متعدد الإطارات",
    description: "Weekly + Daily + 4H + 1H + 15m. نقطة دخول دقيقة بعد تأكيد من 5 إطارات زمنية",
    color: "purple",
  },
  {
    icon: Bell,
    title: "إشعارات Telegram فورية",
    description: "كل إشارة تصلك خلال ثوانٍ على Telegram. أوامر تنفيذ ذكية: /analyze BTC و /scan",
    color: "pink",
  },
  {
    icon: Globe,
    title: "مصمم للسوق العربي",
    description: "واجهة عربية كاملة، دعم 24/7 بالعربية، تكامل مع KNET و mada، توقيت الخليج",
    color: "emerald",
  },
];

export function Features() {
  return (
    <section id="features" className="py-32 px-6 relative">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <p className="text-emerald-400 text-sm font-mono mb-3 tracking-widest uppercase">
            ما يميزنا
          </p>
          <h2 className="font-display text-4xl md:text-5xl font-semibold mb-6">
            ليست منصة تداول عادية
          </h2>
          <p className="text-lg text-ink-50/60 max-w-2xl mx-auto">
            بنينا TradoAI من الصفر كأول AI-Native trading platform عربية.
            كل ميزة مدروسة لحمايتك ومضاعفة فرصك.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="group relative glass rounded-2xl p-8 hover:bg-white/[0.06] transition-all hover:-translate-y-1"
            >
              <div
                className={`inline-flex items-center justify-center w-12 h-12 rounded-xl mb-6 bg-${f.color}-500/10 text-${f.color}-400 group-hover:scale-110 transition`}
              >
                <f.icon size={24} />
              </div>
              <h3 className="font-display text-xl font-semibold mb-3">{f.title}</h3>
              <p className="text-ink-50/60 leading-relaxed">{f.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
