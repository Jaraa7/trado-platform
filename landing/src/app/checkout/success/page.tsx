"use client";

import { useEffect, useState } from "react";
import { CheckCircle, ArrowLeft, Bot } from "lucide-react";

export default function CheckoutSuccessPage() {
  const [count, setCount] = useState(5);

  useEffect(() => {
    const t = setInterval(() => setCount((c) => c - 1), 1000);
    const r = setTimeout(() => window.location.href = "/dashboard", 5000);
    return () => { clearInterval(t); clearTimeout(r); };
  }, []);

  return (
    <div className="min-h-screen bg-ink-975 flex items-center justify-center px-6">
      <div className="max-w-md w-full text-center">
        <div className="w-20 h-20 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
          <CheckCircle size={40} className="text-emerald-400" />
        </div>

        <h1 className="font-display text-4xl font-semibold mb-4">
          مرحباً بك في TradoAI! 🎉
        </h1>
        <p className="text-ink-50/70 mb-8 leading-relaxed">
          تم تفعيل اشتراكك بنجاح. فريقك من 87 وكيل AI جاهز للعمل.
        </p>

        <div className="glass rounded-2xl p-6 mb-8 text-right space-y-4">
          <div className="flex items-center gap-3">
            <Bot size={20} className="text-emerald-400 shrink-0" />
            <p className="text-sm text-ink-50/80">
              <strong>الخطوة 1:</strong> افتح Telegram وابحث عن @TradoAIBot
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ArrowLeft size={20} className="text-emerald-400 shrink-0" />
            <p className="text-sm text-ink-50/80">
              <strong>الخطوة 2:</strong> اضغط /start واربط حسابك
            </p>
          </div>
          <div className="flex items-center gap-3">
            <CheckCircle size={20} className="text-emerald-400 shrink-0" />
            <p className="text-sm text-ink-50/80">
              <strong>الخطوة 3:</strong> ربط منصة التداول (Bybit/Binance/OKX)
            </p>
          </div>
        </div>

        <a
          href="/dashboard"
          className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-ink-950 font-bold transition"
        >
          انتقل للـ Dashboard
        </a>

        <p className="mt-4 text-sm text-ink-50/40">
          ينتقل تلقائياً خلال {count} ثواني
        </p>
      </div>
    </div>
  );
}
