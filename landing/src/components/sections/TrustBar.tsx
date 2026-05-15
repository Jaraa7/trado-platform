"use client";

export function TrustBar() {
  const exchanges = ["Binance", "Bybit", "OKX", "Kucoin", "MEXC", "Bitget"];

  return (
    <section className="border-y border-white/5 py-12 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <p className="text-center text-sm text-ink-50/40 mb-8 uppercase tracking-widest">
          متوافق مع أكبر منصات التداول
        </p>
        <div className="flex justify-center items-center flex-wrap gap-x-12 gap-y-6">
          {exchanges.map((ex) => (
            <span
              key={ex}
              className="text-2xl font-display text-ink-50/30 hover:text-emerald-400/60 transition tracking-tight"
            >
              {ex}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
