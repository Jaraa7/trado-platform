"use client";

import { motion } from "framer-motion";
import { Plus, Minus } from "lucide-react";
import { useState } from "react";

const faqs = [
  {
    q: "هل أحتاج خبرة في التداول لاستخدام TradoAI؟",
    a: "لا، صممنا TradoAI لتناسب كل المستويات. المبتدئ يحصل على إشارات واضحة مع توصيات Risk Management، والمحترف يحصل على تحليلات معمقة وأدوات Backtesting. كل وكيل يشرح قراراته بالتفصيل لتتعلم منه.",
  },
  {
    q: "هل أموالي آمنة؟ هل يمكنكم سحبها؟",
    a: "لا، أبداً. نطلب فقط صلاحية القراءة والتداول من API منصتك. لا نملك صلاحية السحب (Withdrawal) إطلاقاً. أموالك تبقى في حسابك على Binance/Bybit/OKX — نحن فقط نرسل أوامر شراء/بيع. تستطيع إيقاف الـ API في أي ثانية.",
  },
  {
    q: "كم تكلفة AI الفعلية؟ هل ستزيد الأسعار؟",
    a: "تكلفة الـ AI لكل عميل ~$12-75 شهرياً (حسب الباقة). نحن نطبق Smart Caching + Model Routing لتوفير 60% من التكلفة. الأسعار مضمونة لمدة 12 شهر من تاريخ اشتراكك. لو زدنا الأسعار، اشتراكك الحالي محفوظ.",
  },
  {
    q: "هل التداول الآلي مسموح في الكويت/السعودية؟",
    a: "نعم، التداول الآلي للأفراد قانوني في معظم دول الخليج. لكن نوصي بالتحقق من قوانين بلدك. TradoAI لا يقدم نصائح استثمارية رسمية — نحن أداة تحليل وتنفيذ. كل صفقة تنفذها أنت بإرادتك (أو بإذنك المسبق للتنفيذ التلقائي).",
  },
  {
    q: "ماذا لو خسرت في صفقة؟ هل سترجعون أموالي؟",
    a: "نقدم Risk Guardian يحمي من الخسائر الكبيرة (حد 2% لكل صفقة). لكن لا أحد يضمن الربح في التداول. نضمن جودة الـ AI والتحليل، لا نضمن ربحاً معيناً. اقرأ شروط الخدمة بعناية. توصية: ابدأ بـ Testnet أولاً لمدة شهر.",
  },
  {
    q: "هل يمكنني الإلغاء في أي وقت؟",
    a: "نعم، الإلغاء فوري بدون أسئلة. لا التزامات. لو ألغيت خلال أول 14 يوم وكنت استخدمت أقل من 50% من الإشارات، نرد كامل المبلغ. بعد 14 يوم، تستمر الخدمة حتى نهاية الفترة المدفوعة.",
  },
  {
    q: "ما الفرق بين TradoAI و 3Commas/Cryptohopper؟",
    a: "3Commas و Cryptohopper استخدام Rules-Based traditional bots. TradoAI أول AI-Native platform بـ 87 وكيل ذكي يفكرون مثل المحلل البشري — يقرأون الأخبار، يفهمون السياق، يكشفون الفرص الخفية. أيضاً نحن الوحيدون بدعم عربي كامل + KNET + Mada.",
  },
  {
    q: "كيف تختلف باقة Pro عن Elite؟",
    a: "Pro ($99) تناسب محفظة $10K-$100K مع 50 إشارة يومياً و 3 منصات. Elite ($199) تناسب محفظة أكبر مع إشارات unlimited، 5 منصات، tax reporting، API access، 1-on-1 onboarding، ومزايا premium إضافية. الترقية بنقرة واحدة.",
  },
];

export function FAQ() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="faq" className="py-32 px-6">
      <div className="max-w-3xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <p className="text-emerald-400 text-sm font-mono mb-3 tracking-widest uppercase">
            الأسئلة الشائعة
          </p>
          <h2 className="font-display text-4xl md:text-5xl font-semibold">
            كل ما تريد معرفته
          </h2>
        </motion.div>

        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              className="glass rounded-xl overflow-hidden"
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between gap-4 p-6 text-right hover:bg-white/[0.02] transition"
              >
                <span className="font-semibold text-base md:text-lg">{faq.q}</span>
                {open === i ? (
                  <Minus size={20} className="text-emerald-400 shrink-0" />
                ) : (
                  <Plus size={20} className="text-ink-50/40 shrink-0" />
                )}
              </button>
              {open === i && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  className="px-6 pb-6 text-ink-50/70 leading-relaxed border-t border-white/5 pt-4"
                >
                  {faq.a}
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
