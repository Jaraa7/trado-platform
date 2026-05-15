"use client";

import { Twitter, Send, Github, Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-ink-950 border-t border-white/5 py-16 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center font-display font-bold text-white">
                T
              </div>
              <span className="font-display text-xl font-semibold">
                Trado<span className="text-emerald-400">AI</span>
              </span>
            </div>
            <p className="text-ink-50/60 mb-6 max-w-md leading-relaxed">
              منصة التداول الذكي الأولى عربياً. 87 وكيل ذكاء اصطناعي يعملون لأجلك 24/7.
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="w-10 h-10 rounded-lg bg-white/5 hover:bg-emerald-500/20 flex items-center justify-center transition">
                <Twitter size={18} />
              </a>
              <a href="#" className="w-10 h-10 rounded-lg bg-white/5 hover:bg-emerald-500/20 flex items-center justify-center transition">
                <Send size={18} />
              </a>
              <a href="https://github.com/Jaraa7/trado-platform" className="w-10 h-10 rounded-lg bg-white/5 hover:bg-emerald-500/20 flex items-center justify-center transition">
                <Github size={18} />
              </a>
              <a href="mailto:hello@tradoai.net" className="w-10 h-10 rounded-lg bg-white/5 hover:bg-emerald-500/20 flex items-center justify-center transition">
                <Mail size={18} />
              </a>
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="font-semibold mb-4">المنصة</h4>
            <ul className="space-y-3 text-sm text-ink-50/60">
              <li><a href="#features" className="hover:text-emerald-400 transition">المزايا</a></li>
              <li><a href="#agents" className="hover:text-emerald-400 transition">الـ 87 وكيل</a></li>
              <li><a href="#pricing" className="hover:text-emerald-400 transition">الأسعار</a></li>
              <li><a href="/docs" className="hover:text-emerald-400 transition">التوثيق</a></li>
              <li><a href="/api" className="hover:text-emerald-400 transition">API</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">الشركة</h4>
            <ul className="space-y-3 text-sm text-ink-50/60">
              <li><a href="/about" className="hover:text-emerald-400 transition">من نحن</a></li>
              <li><a href="/blog" className="hover:text-emerald-400 transition">المدونة</a></li>
              <li><a href="/contact" className="hover:text-emerald-400 transition">تواصل معنا</a></li>
              <li><a href="/privacy" className="hover:text-emerald-400 transition">الخصوصية</a></li>
              <li><a href="/terms" className="hover:text-emerald-400 transition">الشروط</a></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-ink-50/40">
          <p>© 2026 TradoAI. جميع الحقوق محفوظة.</p>
          <p className="font-mono">tradoai.net</p>
        </div>

        {/* Risk disclaimer */}
        <div className="mt-8 p-6 rounded-xl bg-red-500/5 border border-red-500/20">
          <p className="text-xs text-ink-50/60 leading-relaxed text-center">
            ⚠️ <strong className="text-red-400">تنبيه المخاطر:</strong> التداول في العملات الرقمية ينطوي على مخاطر عالية وقد يؤدي إلى خسارة رأس المال.
            الأداء السابق لا يضمن نتائج مستقبلية. TradoAI أداة تحليل وليست نصيحة استثمارية.
            تداول فقط بما تستطيع خسارته.
          </p>
        </div>
      </div>
    </footer>
  );
}
