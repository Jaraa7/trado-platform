"use client";
import { useEffect, useState } from "react";
import Image from "next/image";
import { getLocale, rtlLocales, translations, type Locale } from "@/lib/i18n";
import { Check, ChevronDown, Menu, X, TrendingUp, Shield, Zap, BarChart3, Bell, Globe, ArrowRight } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "https://trado-bot.fly.dev";

const TIERS = [
  { slug:"micro",   monthly:29,  annual:290,  popular:false },
  { slug:"starter", monthly:59,  annual:590,  popular:false },
  { slug:"pro",     monthly:99,  annual:990,  popular:true  },
  { slug:"elite",   monthly:199, annual:1990, popular:false },
];

const FAQS: Record<Locale, {q:string;a:string}[]> = {
  en:[
    {q:"Do I need trading experience?",a:"No. Our 87 AI tools guide you at every step, from understanding signals to managing risk."},
    {q:"Is my capital safe? Can you withdraw it?",a:"Never. We only request read and trade API permissions. Withdrawal permission is never requested. Your funds stay on your exchange at all times."},
    {q:"What makes TradoAI different?",a:"Unlike rule-based bots, our 87 AI tools reason like professional analysts — reading news, understanding context, and finding opportunities others miss."},
    {q:"Can I cancel anytime?",a:"Yes. Cancel instantly, no questions asked. Full refund within 14 days if under 50% signals used."},
    {q:"How accurate are the signals?",a:"Our multi-timeframe confirmation system significantly reduces false signals. Every signal includes confidence score and full risk metrics."},
  ],
  ar:[
    {q:"هل أحتاج خبرة في التداول؟",a:"لا. 87 أداة AI ترشدك في كل خطوة، من فهم الإشارات إلى إدارة المخاطر."},
    {q:"هل رأس مالي آمن؟",a:"نطلب فقط صلاحية القراءة والتداول. صلاحية السحب غير مطلوبة إطلاقاً. أموالك تبقى على منصتك في جميع الأوقات."},
    {q:"ما الذي يميز TradoAI؟",a:"87 أداة AI تفكر كمحللين محترفين — تقرأ الأخبار، تفهم السياق، وتجد الفرص التي يغفلها الآخرون."},
    {q:"هل يمكنني الإلغاء في أي وقت؟",a:"نعم. الإلغاء فوري بدون أسئلة. استرداد كامل خلال 14 يوم إذا استخدمت أقل من 50% من الإشارات."},
    {q:"ما دقة الإشارات؟",a:"نظام تأكيد متعدد الإطارات الزمنية يقلل الإشارات الخاطئة بشكل كبير. كل إشارة تتضمن درجة الثقة ومقاييس المخاطر الكاملة."},
  ],
  tr:[{q:"Deneyim gerekiyor mu?",a:"Hayır. 87 AI aracımız her adımda rehberlik eder."},{q:"Sermayem güvende mi?",a:"Asla para çekme izni istemiyoruz. Fonlarınız her zaman borsanızda kalır."},{q:"TradoAI'yi farklı kılan nedir?",a:"87 AI aracımız profesyonel analistler gibi düşünür."},{q:"İstediğimde iptal edebilir miyim?",a:"Evet, anında iptal."},{q:"Sinyaller ne kadar doğru?",a:"Çok zaman dilimli sistem yanlış sinyalleri önemli ölçüde azaltır."}],
  fr:[{q:"Ai-je besoin d'expérience?",a:"Non. Nos 87 outils IA vous guident à chaque étape."},{q:"Mon capital est-il sécurisé?",a:"Jamais de permission de retrait. Vos fonds restent sur votre exchange."},{q:"Qu'est-ce qui différencie TradoAI?",a:"87 outils IA pensent comme des analystes professionnels."},{q:"Puis-je annuler à tout moment?",a:"Oui, annulation instantanée."},{q:"Quelle est la précision?",a:"Notre système multi-temporel réduit significativement les faux signaux."}],
  es:[{q:"¿Necesito experiencia?",a:"No. Nuestras 87 herramientas IA te guían en cada paso."},{q:"¿Mi capital está seguro?",a:"Nunca solicitamos permiso de retiro."},{q:"¿Qué diferencia a TradoAI?",a:"87 herramientas IA piensan como analistas profesionales."},{q:"¿Puedo cancelar?",a:"Sí, cancelación instantánea."},{q:"¿Qué tan precisas son las señales?",a:"Nuestro sistema multi-temporal reduce los falsos sinyales."}],
  ru:[{q:"Нужен ли опыт?",a:"Нет. 87 инструментов ИИ направляют вас на каждом шагу."},{q:"Мой капитал в безопасности?",a:"Мы никогда не запрашиваем разрешение на вывод средств."},{q:"Чем отличается TradoAI?",a:"87 инструментов ИИ мыслят как профессиональные аналитики."},{q:"Могу отменить?",a:"Да, мгновенная отмена."},{q:"Точность сигналов?",a:"Многотаймфреймная система значительно снижает ложные сигналы."}],
};

export default function HomePage() {
  const [locale, setLocale] = useState<Locale>("en");
  const [dir, setDir]   = useState<"ltr"|"rtl">("ltr");
  const [annual, setAnnual]   = useState(false);
  const [openFaq, setOpenFaq] = useState<number|null>(0);
  const [email, setEmail]     = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [menuOpen, setMenuOpen]   = useState(false);
  const [scrolled, setScrolled]   = useState(false);

  const t = (k: string) => translations[locale]?.[k] ?? translations.en[k] ?? k;

  useEffect(() => {
    const l = getLocale(navigator.language || "en");
    setLocale(l);
    const isRtl = rtlLocales.includes(l);
    setDir(isRtl ? "rtl" : "ltr");
    document.documentElement.dir  = isRtl ? "rtl" : "ltr";
    document.documentElement.lang = l;
  }, []);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", fn);
    return () => window.removeEventListener("scroll", fn);
  }, []);

  const handleWaitlist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes("@")) return;
    setSubmitted(true);
    try { await fetch(`${API}/waitlist`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email})}); } catch {}
  };

  const features = [
    {icon:Zap,       title:t("f1_title"), desc:t("f1_desc")},
    {icon:Shield,    title:t("f2_title"), desc:t("f2_desc")},
    {icon:TrendingUp,title:t("f3_title"), desc:t("f3_desc")},
    {icon:BarChart3, title:t("f4_title"), desc:t("f4_desc")},
    {icon:Bell,      title:t("f5_title"), desc:t("f5_desc")},
    {icon:Globe,     title:t("f6_title"), desc:t("f6_desc")},
  ];

  const tierNames: Record<string,string> = {micro:"Micro",starter:"Starter",pro:"Pro",elite:"Elite"};
  const tierFeatures = [
    [t("f1_title"),"1 exchange","Telegram","Mobile app"],
    ["15 signals/day","2 exchanges","Whale tracker","12h support"],
    ["50 signals/day","3 exchanges","Backtesting","Strategy builder","1h support"],
    ["Unlimited","5 exchanges","Tax reporting","API access","15min support"],
  ];

  return (
    <div style={{direction:dir}}>

      {/* NAV */}
      <header className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${scrolled?"bg-[#050810]/90 backdrop-blur-xl border-b border-white/5":""}`}>
        <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <a href="/" className="flex items-center gap-3">
            <Image src="/logo.png" alt="TradoAI" width={38} height={38} className="rounded-xl"/>
            <span className="font-display text-xl font-bold tracking-tight">Trado<span className="grad">AI</span></span>
          </a>
          <div className="hidden md:flex items-center gap-8">
            {["features","pricing","faq"].map(k=>(
              <a key={k} href={`#${k}`} className="text-sm text-white/60 hover:text-white transition">{t(`nav_${k}`)}</a>
            ))}
          </div>
          <div className="hidden md:flex items-center gap-3">
            <a href="/login" className="text-sm px-4 py-2 text-white/60 hover:text-white transition">{t("nav_login")}</a>
            <a href="#waitlist" className="btn-primary text-sm px-5 py-2.5"><span>{t("nav_cta")}</span></a>
          </div>
          <button className="md:hidden p-2 text-white/70" onClick={()=>setMenuOpen(!menuOpen)}>
            {menuOpen?<X size={22}/>:<Menu size={22}/>}
          </button>
        </nav>
        {menuOpen&&(
          <div className="md:hidden bg-[#080d1a] border-t border-white/5 px-6 py-4 space-y-3">
            {["features","pricing","faq"].map(k=>(
              <a key={k} href={`#${k}`} onClick={()=>setMenuOpen(false)} className="block py-2 text-white/70">{t(`nav_${k}`)}</a>
            ))}
            <a href="#waitlist" onClick={()=>setMenuOpen(false)} className="btn-primary block text-center py-3 mt-2"><span>{t("nav_cta")}</span></a>
          </div>
        )}
      </header>

      {/* HERO */}
      <section className="relative min-h-screen flex items-center pt-24 pb-20 px-6 overflow-hidden mesh">
        <div className="absolute inset-0 grid-bg"/>
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[500px] rounded-full bg-blue-500/8 blur-[120px]"/>
        <div className="relative max-w-4xl mx-auto w-full text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-sm mb-8">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"/>
            <span className="text-white/70">{t("hero_badge")}</span>
          </div>
          <h1 className="font-display text-5xl md:text-7xl font-bold leading-[1.05] mb-6 anim-up">
            {t("hero_h1_1")}<br/><span className="grad">{t("hero_h1_2")}</span>
          </h1>
          <p className="text-lg md:text-xl text-white/55 mb-10 max-w-2xl mx-auto leading-relaxed">{t("hero_sub")}</p>
          <form onSubmit={handleWaitlist} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder={t("hero_email")} required dir="ltr"
              className="flex-1 px-5 py-3.5 rounded-xl bg-white/5 border border-white/10 focus:border-blue-400/50 focus:outline-none transition placeholder:text-white/30 text-sm"/>
            <button type="submit" disabled={submitted} className="btn-primary px-6 py-3.5 text-sm">
              <span className="flex items-center gap-2">{submitted?t("hero_joined"):<>{t("hero_join")}<ArrowRight size={16}/></>}</span>
            </button>
          </form>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-white/35">
            <span>✓ {t("cta_t1")}</span><span>✓ {t("cta_t2")}</span><span>✓ {t("cta_t3")}</span>
          </div>
        </div>
      </section>

      {/* TRUST */}
      <div className="border-y border-white/5 py-10">
        <p className="text-center text-xs text-white/25 tracking-[.2em] uppercase mb-6">{t("trust_label")}</p>
        <div className="flex justify-center flex-wrap gap-x-12 gap-y-3">
          {["Spot","Futures","Perpetuals","Options","DeFi","CFD"].map(m=>(
            <span key={m} className="text-base font-display text-white/20 hover:text-white/40 transition">{m}</span>
          ))}
        </div>
      </div>

      {/* FEATURES */}
      <section id="features" className="py-28 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-xs font-mono text-blue-400 mb-3 tracking-widest uppercase">Features</p>
            <h2 className="font-display text-4xl md:text-5xl font-bold mb-4">{t("feat_title")}</h2>
            <p className="text-white/50 max-w-xl mx-auto text-sm">{t("feat_sub")}</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map(({icon:Icon,title,desc},i)=>(
              <div key={i} className="glass rounded-2xl p-7 hover:border-white/15 transition group">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-emerald-500/10 flex items-center justify-center mb-5 group-hover:scale-110 transition">
                  <Icon size={20} className="text-blue-400"/>
                </div>
                <h3 className="font-display text-base font-semibold mb-2">{title}</h3>
                <p className="text-white/45 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW */}
      <section className="py-24 px-6 bg-gradient-to-b from-transparent via-blue-950/8 to-transparent">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-xs font-mono text-emerald-400 mb-3 tracking-widest uppercase">How it works</p>
            <h2 className="font-display text-4xl font-bold">{t("how_title")}</h2>
          </div>
          <div className="space-y-4">
            {[{n:"01",tk:"h1_t",dk:"h1_d",c:"from-blue-500/15 to-blue-500/5"},{n:"02",tk:"h2_t",dk:"h2_d",c:"from-emerald-500/15 to-emerald-500/5"},{n:"03",tk:"h3_t",dk:"h3_d",c:"from-violet-500/15 to-violet-500/5"}].map(s=>(
              <div key={s.n} className="glass rounded-2xl p-7 flex gap-5 items-start">
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${s.c} flex items-center justify-center flex-shrink-0`}>
                  <span className="font-mono text-xs font-bold text-white/50">{s.n}</span>
                </div>
                <div>
                  <h3 className="font-display text-lg font-semibold mb-1">{t(s.tk)}</h3>
                  <p className="text-white/45 text-sm leading-relaxed">{t(s.dk)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AGENTS */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-xs font-mono text-blue-400 mb-3 tracking-widest uppercase">AI Power</p>
          <h2 className="font-display text-4xl md:text-5xl font-bold mb-4">
            <span className="grad">87</span> {locale==="ar"?"أداة AI. منصة واحدة.":"AI tools. One platform."}
          </h2>
          <p className="text-white/45 max-w-xl mx-auto mb-12 text-sm">{t("agents_sub")}</p>
          <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
            {[{n:15,l:"Trading"},{n:12,l:"Financial"},{n:11,l:"Customer"},{n:10,l:"Engineering"},{n:12,l:"Marketing"},{n:7,l:"Security"},{n:7,l:"Design"},{n:7,l:"Product"},{n:6,l:"Operations"}].map(d=>(
              <div key={d.l} className="glass rounded-xl p-4 hover:border-white/15 transition">
                <p className="font-mono text-2xl font-bold grad mb-1">{d.n}</p>
                <p className="text-white/35 text-xs">{d.l}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="py-24 px-6 bg-gradient-to-b from-transparent via-emerald-950/8 to-transparent">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-xs font-mono text-emerald-400 mb-3 tracking-widest uppercase">Pricing</p>
            <h2 className="font-display text-4xl md:text-5xl font-bold mb-4">{t("pricing_title")}</h2>
            <p className="text-white/45 max-w-xl mx-auto text-sm mb-8">{t("pricing_sub")}</p>
            <div className="inline-flex items-center gap-1 bg-white/5 rounded-xl p-1">
              <button onClick={()=>setAnnual(false)} className={`px-5 py-2 rounded-lg text-sm font-medium transition ${!annual?"bg-white/10 text-white":"text-white/45"}`}>{t("pricing_monthly")}</button>
              <button onClick={()=>setAnnual(true)}  className={`px-5 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 ${annual?"bg-white/10 text-white":"text-white/45"}`}>
                {t("pricing_annual")}<span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400">{t("pricing_save")}</span>
              </button>
            </div>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {TIERS.map((tier,i)=>{
              const price = annual?Math.floor(tier.annual/12):tier.monthly;
              return(
                <div key={tier.slug} className={`relative rounded-2xl p-6 transition ${tier.popular?"border border-blue-500/40 bg-gradient-to-b from-blue-950/50 to-[#0d1526]":"glass"}`}>
                  {tier.popular&&<div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-blue-500 to-emerald-500 text-xs font-bold text-white whitespace-nowrap">Most Popular</div>}
                  <h3 className="font-display text-lg font-bold mb-3">{tierNames[tier.slug]}</h3>
                  <div className="flex items-baseline gap-1 mb-5">
                    <span className="text-3xl font-bold font-mono">${price}</span>
                    <span className="text-white/35 text-sm">{t("pricing_mo")}</span>
                  </div>
                  <a href={`/checkout?tier=${tier.slug}&billing=${annual?"annual":"monthly"}`}
                     className={`block text-center py-2.5 rounded-xl text-sm font-semibold mb-5 transition ${tier.popular?"btn-primary":"btn-ghost"}`}>
                    <span>{t("pricing_cta")}</span>
                  </a>
                  <ul className="space-y-2">
                    {tierFeatures[i].map((f:string)=>(
                      <li key={f} className="flex items-start gap-2 text-xs">
                        <Check size={13} className="text-emerald-400 mt-0.5 shrink-0"/>
                        <span className="text-white/50">{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
          <div className="mt-5 grid md:grid-cols-2 gap-4 max-w-xl mx-auto">
            {[{n:"Whale",p:"$499/mo",s:"$50K–$5M"},{n:"Institutional",p:"$1,499/mo",s:"Funds & institutions"}].map(x=>(
              <div key={x.n} className="glass rounded-xl p-5 text-center hover:border-white/15 transition">
                <p className="font-display font-bold mb-1">{x.n}</p>
                <p className="text-white/35 text-xs mb-2">{x.s}</p>
                <p className="font-mono text-blue-400 font-semibold text-sm">{x.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-xs font-mono text-blue-400 mb-3 tracking-widest uppercase">FAQ</p>
            <h2 className="font-display text-4xl font-bold">{t("faq_title")}</h2>
          </div>
          <div className="space-y-3">
            {(FAQS[locale]??FAQS.en).map((faq,i)=>(
              <div key={i} className="glass rounded-xl overflow-hidden">
                <button onClick={()=>setOpenFaq(openFaq===i?null:i)} className="w-full flex items-center justify-between gap-4 p-5 text-start">
                  <span className="font-medium text-sm">{faq.q}</span>
                  <ChevronDown size={16} className={`text-white/35 shrink-0 transition-transform ${openFaq===i?"rotate-180":""}`}/>
                </button>
                {openFaq===i&&<div className="px-5 pb-5 text-white/50 text-sm leading-relaxed border-t border-white/5 pt-4">{faq.a}</div>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section id="waitlist" className="py-24 px-6 relative overflow-hidden">
        <div className="absolute inset-0 mesh"/>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[250px] bg-blue-500/12 blur-[100px] rounded-full"/>
        <div className="relative max-w-xl mx-auto text-center">
          <h2 className="font-display text-4xl md:text-5xl font-bold mb-4 leading-tight">
            {t("cta_title_1")}<br/><span className="grad">{t("cta_title_2")}</span>
          </h2>
          <p className="text-white/45 mb-8 text-sm">{t("cta_sub")}</p>
          <form onSubmit={handleWaitlist} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto mb-5">
            <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder={t("cta_email")} required dir="ltr"
              className="flex-1 px-5 py-3.5 rounded-xl bg-white/5 border border-white/10 focus:border-blue-400/50 focus:outline-none transition placeholder:text-white/30 text-sm"/>
            <button type="submit" disabled={submitted} className="btn-primary px-6 py-3.5 text-sm"><span>{submitted?t("cta_done"):t("cta_btn")}</span></button>
          </form>
          <div className="flex flex-wrap justify-center gap-5 text-xs text-white/30">
            <span>✓ {t("cta_t1")}</span><span>✓ {t("cta_t2")}</span><span>✓ {t("cta_t3")}</span>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-[#080d1a] border-t border-white/5 py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between gap-8 mb-10">
            <div className="max-w-xs">
              <div className="flex items-center gap-3 mb-4">
                <Image src="/logo.png" alt="TradoAI" width={34} height={34} className="rounded-xl"/>
                <span className="font-display text-xl font-bold">Trado<span className="grad">AI</span></span>
              </div>
              <p className="text-white/35 text-xs leading-relaxed">87 specialized AI tools working together to give you a decisive edge in financial markets.</p>
            </div>
            <div className="grid grid-cols-2 gap-x-12 gap-y-3 text-sm text-white/35">
              <a href="#features" className="hover:text-white transition">{t("nav_features")}</a>
              <a href="/privacy" className="hover:text-white transition">Privacy</a>
              <a href="#pricing" className="hover:text-white transition">{t("nav_pricing")}</a>
              <a href="/terms" className="hover:text-white transition">Terms</a>
              <a href="#faq" className="hover:text-white transition">{t("nav_faq")}</a>
              <a href="mailto:hello@tradoai.net" className="hover:text-white transition">Contact</a>
            </div>
          </div>
          <div className="border-t border-white/5 pt-8">
            <p className="text-white/20 text-xs leading-relaxed mb-4">{t("footer_risk")}</p>
            <div className="flex justify-between items-center text-xs text-white/20">
              <span>© {new Date().getFullYear()} TradoAI. {t("footer_rights")}</span>
              <span className="font-mono">tradoai.net</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
