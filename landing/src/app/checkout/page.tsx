"use client";

import { useState } from "react";
import { Check, Loader2, Shield, Zap } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "https://trado-bot.fly.dev";

const PLANS = {
  micro:         { name: "Micro",         price_m: 29,   price_y: 290  },
  starter:       { name: "Starter",       price_m: 59,   price_y: 590  },
  pro:           { name: "Pro",           price_m: 99,   price_y: 990  },
  elite:         { name: "Elite",         price_m: 199,  price_y: 1990 },
  whale:         { name: "Whale",         price_m: 499,  price_y: 4990 },
  institutional: { name: "Institutional", price_m: 1499, price_y: 14990 },
  founder:       { name: "Founder",       price_m: 2999, price_y: null },
};

export default async function CheckoutPage({
  searchParams,
}: {
  searchParams: Promise<{ tier?: string; billing?: string }>;
}) {
  const params = await searchParams;
  const tier = params.tier || "pro";
  const billing = params.billing || "monthly";
  const plan = PLANS[tier as keyof typeof PLANS] || PLANS.pro;

  const price = billing === "annual" ? plan.price_y : plan.price_m;
  const monthlyPrice = billing === "annual" ? Math.floor((plan.price_y || 0) / 12) : plan.price_m;

  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");

  const handleCheckout = async () => {
    if (!email || !email.includes("@")) {
      setError("أدخل بريداً إلكترونياً صحيحاً");
      return;
    }
    setLoading(true);
    setError("");

    try {
      // 1. تسجيل أو تسجيل دخول سريع
      const authRes = await fetch(`${API}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: Math.random().toString(36).slice(2) + "Aa1!" }),
      });
      const authData = await authRes.json();
      const token = authData.access_token;

      // 2. إنشاء checkout URL
      const checkoutRes = await fetch(`${API}/payments/checkout?tier=${tier}&billing=${billing}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
      });
      const { checkout_url } = await checkoutRes.json();

      // 3. التوجيه لـ Lemon Squeezy
      window.location.href = checkout_url;
    } catch (e) {
      setError("حدث خطأ. حاول مرة أخرى.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-ink-975 flex items-center justify-center px-6 py-24">
      <div className="max-w-lg w-full">
        <div className="text-center mb-8">
          <a href="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center font-bold text-white">
              T
            </div>
            <span className="font-display text-xl font-semibold">
              Trado<span className="text-emerald-400">AI</span>
            </span>
          </a>
          <h1 className="text-3xl font-display font-semibold mb-2">
            باقة {plan.name}
          </h1>
          <p className="text-ink-50/60">
            {billing === "annual" ? "فاتورة سنوية" : "فاتورة شهرية"}
          </p>
        </div>

        {/* Price Card */}
        <div className="glass rounded-2xl p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-ink-50/60 text-sm mb-1">تدفع</p>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold font-mono">${monthlyPrice}</span>
                <span className="text-ink-50/50">/شهر</span>
              </div>
              {billing === "annual" && (
                <p className="text-emerald-400 text-sm mt-1">${price} تُدفع سنوياً</p>
              )}
            </div>
            <div className="text-left">
              <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-sm border border-emerald-500/20">
                {billing === "annual" ? "وفّر 17%" : "شهري"}
              </span>
            </div>
          </div>

          <div className="space-y-3 mb-6 pb-6 border-b border-white/10">
            {[
              "87 وكيل AI كاملون",
              "تحليل تقني 24/7",
              "إشعارات Telegram فورية",
              "Risk Guardian لحماية رأس مالك",
              "إلغاء في أي وقت",
            ].map((f) => (
              <div key={f} className="flex items-center gap-3 text-sm">
                <Check size={16} className="text-emerald-400 shrink-0" />
                <span className="text-ink-50/80">{f}</span>
              </div>
            ))}
          </div>

          {/* Email Input */}
          <div className="space-y-3">
            <label className="block text-sm text-ink-50/70">
              بريدك الإلكتروني
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-400/20 transition placeholder:text-ink-50/30 text-right"
              dir="ltr"
            />
            {error && <p className="text-red-400 text-sm">{error}</p>}

            <button
              onClick={handleCheckout}
              disabled={loading}
              className="w-full py-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-ink-950 font-bold flex items-center justify-center gap-2 transition"
            >
              {loading ? (
                <><Loader2 size={20} className="animate-spin" /> جاري التحضير...</>
              ) : (
                <><Zap size={20} /> اشترك الآن — ${price}</>
              )}
            </button>
          </div>
        </div>

        {/* Trust badges */}
        <div className="flex items-center justify-center gap-6 text-xs text-ink-50/40">
          <div className="flex items-center gap-1">
            <Shield size={14} />
            <span>مدفوعات آمنة</span>
          </div>
          <span>•</span>
          <span>إلغاء فوري</span>
          <span>•</span>
          <span>ضمان 14 يوم</span>
        </div>
      </div>
    </div>
  );
}
