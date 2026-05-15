"use client";
import { TIERS as TIER_CONFIGS, TIER_ROW_1, TIER_ROW_2, getDisplayPrice } from "@/lib/tiers";
import { useEffect, useState } from "react";
import { getLocale, rtlLocales, translations, type Locale } from "@/lib/i18n";
import { Check, ChevronDown, Menu, X, TrendingUp, Shield, Zap, BarChart3, Bell, Globe, ArrowRight, Star } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "https://trado-bot.fly.dev";

// TIERS loaded from @/lib/tiers — single source of truth
const TIER_NAMES: Record<string,Record<Locale,string>> = {
  trial:         {en:"Trial",        ar:"تجريبي",      tr:"Deneme",      fr:"Essai",        es:"Prueba",       ru:"Пробный"},
  micro:         {en:"Micro",        ar:"Micro",        tr:"Micro",       fr:"Micro",        es:"Micro",        ru:"Micro"},
  starter:       {en:"Starter",      ar:"Starter",      tr:"Starter",     fr:"Starter",      es:"Starter",      ru:"Starter"},
  pro:           {en:"Pro",          ar:"Pro",          tr:"Pro",         fr:"Pro",          es:"Pro",          ru:"Pro"},
  elite:         {en:"Elite",        ar:"Elite",        tr:"Elite",       fr:"Elite",        es:"Elite",        ru:"Elite"},
  whale:         {en:"Whale",        ar:"Whale",        tr:"Whale",       fr:"Whale",        es:"Whale",        ru:"Whale"},
  institutional: {en:"Institutional",ar:"Institutional",tr:"Kurumsal",    fr:"Institutionnel",es:"Institucional",ru:"Институциональный"},
  founder:       {en:"Founder",      ar:"Founder",      tr:"Kurucu",      fr:"Fondateur",    es:"Fundador",     ru:"Основатель"},
};

const FAQS: Record<Locale,{q:string;a:string}[]> = {
  en:[
    {q:"Do I need trading experience?",a:"No. Our 87 AI tools guide you at every step, from understanding signals to managing risk. Beginners and professionals both benefit equally."},
    {q:"Is my capital safe? Can you withdraw it?",a:"Never. We only request read and trade API permissions. Withdrawal permission is never requested. Your funds stay on your exchange at all times."},
    {q:"What makes TradoAI different?",a:"Unlike rule-based bots, our 87 AI tools reason like professional analysts — reading news, understanding context, and finding opportunities others miss. They work as a coordinated team, 24/7."},
    {q:"Can I cancel anytime?",a:"Yes. Cancel instantly, no questions asked. Full refund within 14 days if you used less than 50% of your signals."},
    {q:"How accurate are the signals?",a:"Our multi-timeframe confirmation system significantly reduces false signals. Every signal includes a confidence score, risk metrics, and full AI reasoning."},
    {q:"What is the Founder tier?",a:"Only 100 seats ever. Founders lock in today's price forever, shape the product roadmap, and get every future feature at no extra cost. Once full, it's gone."},
  ],
  ar:[
    {q:"هل أحتاج خبرة في التداول؟",a:"لا. 87 أداة AI ترشدك في كل خطوة، من فهم الإشارات إلى إدارة المخاطر. المبتدئون والمحترفون يستفيدون على حد سواء."},
    {q:"هل رأس مالي آمن؟",a:"نطلب فقط صلاحية القراءة والتداول. صلاحية السحب غير مطلوبة إطلاقاً. أموالك تبقى على منصتك في جميع الأوقات."},
    {q:"ما الذي يميز TradoAI؟",a:"على عكس البوتات العادية، 87 أداة AI لدينا تفكر كمحللين محترفين — تقرأ الأخبار، تفهم السياق، وتجد الفرص التي يغفلها الآخرون. تعمل كفريق متناسق 24/7."},
    {q:"هل يمكنني الإلغاء في أي وقت؟",a:"نعم. الإلغاء فوري بدون أسئلة. استرداد كامل خلال 14 يوم إذا استخدمت أقل من 50% من الإشارات."},
    {q:"ما دقة الإشارات؟",a:"نظام تأكيد متعدد الإطارات يقلل الإشارات الخاطئة بشكل كبير. كل إشارة تتضمن درجة الثقة، مقاييس المخاطر، والتحليل الكامل للـ AI."},
    {q:"ما هي باقة Founder؟",a:"100 مقعد فقط للأبد. يثبّت المؤسسون سعر اليوم إلى الأبد، يشكّلون خارطة طريق المنتج، ويحصلون على كل الميزات المستقبلية بدون تكلفة إضافية. عندما تمتلئ، لن تعود."},
  ],
  tr:[
    {q:"Deneyim gerekiyor mu?",a:"Hayır. 87 AI aracımız her adımda size rehberlik eder."},
    {q:"Sermayem güvende mi?",a:"Asla para çekme izni istemiyoruz. Fonlarınız her zaman borsanızda kalır."},
    {q:"TradoAI'yi farklı kılan nedir?",a:"87 AI aracımız profesyonel analistler gibi düşünür — haberleri okur, bağlamı anlar, fırsatları bulur."},
    {q:"İstediğimde iptal edebilir miyim?",a:"Evet, anında iptal. 14 gün içinde tam iade."},
    {q:"Sinyaller ne kadar doğru?",a:"Çok zaman dilimli sistem yanlış sinyalleri önemli ölçüde azaltır."},
    {q:"Founder nedir?",a:"Sadece 100 koltuk. Fiyatı sonsuza kadar sabitler ve tüm gelecek özellikleri ücretsiz alırsınız."},
  ],
  fr:[
    {q:"Ai-je besoin d'expérience?",a:"Non. Nos 87 outils IA vous guident à chaque étape."},
    {q:"Mon capital est-il sécurisé?",a:"Jamais de permission de retrait. Vos fonds restent sur votre exchange."},
    {q:"Qu'est-ce qui différencie TradoAI?",a:"87 outils IA pensent comme des analystes professionnels, 24/7."},
    {q:"Puis-je annuler à tout moment?",a:"Oui, annulation instantanée et remboursement sous 14 jours."},
    {q:"Quelle est la précision?",a:"Notre système multi-temporel réduit significativement les faux signaux."},
    {q:"Qu'est-ce que Founder?",a:"100 sièges seulement. Prix bloqué à vie et toutes les futures fonctionnalités gratuites."},
  ],
  es:[
    {q:"¿Necesito experiencia?",a:"No. Nuestras 87 herramientas IA te guían en cada paso."},
    {q:"¿Mi capital está seguro?",a:"Nunca solicitamos permiso de retiro. Tus fondos permanecen en tu exchange."},
    {q:"¿Qué diferencia a TradoAI?",a:"87 herramientas IA piensan como analistas profesionales, 24/7."},
    {q:"¿Puedo cancelar?",a:"Sí, cancelación instantánea y reembolso en 14 días."},
    {q:"¿Qué tan precisas son las señales?",a:"Nuestro sistema multi-temporal reduce significativamente las señales falsas."},
    {q:"¿Qué es Founder?",a:"Solo 100 asientos. Precio bloqueado de por vida y todas las funciones futuras gratis."},
  ],
  ru:[
    {q:"Нужен ли опыт?",a:"Нет. 87 инструментов ИИ направляют вас на каждом шагу."},
    {q:"Мой капитал в безопасности?",a:"Мы никогда не запрашиваем разрешение на вывод. Ваши средства остаются на бирже."},
    {q:"Чем отличается TradoAI?",a:"87 инструментов ИИ мыслят как профессиональные аналитики, 24/7."},
    {q:"Могу отменить?",a:"Да, мгновенная отмена и возврат в течение 14 дней."},
    {q:"Точность сигналов?",a:"Многотаймфреймная система значительно снижает ложные сигналы."},
    {q:"Что такое Founder?",a:"Только 100 мест. Цена зафиксирована навсегда, все будущие функции бесплатно."},
  ],
};

export default function HomePage() {
  const [locale, setLocale]   = useState<Locale>("en");
  const [dir, setDir]         = useState<"ltr"|"rtl">("ltr");
  const [annual, setAnnual]   = useState(false);
  const [openFaq, setOpenFaq] = useState<number|null>(0);
  const [email, setEmail]     = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [menuOpen, setMenuOpen]   = useState(false);
  const [scrolled, setScrolled]   = useState(false);

  const t = (k:string) => translations[locale]?.[k] ?? translations.en[k] ?? k;

  useEffect(()=>{
    const l = getLocale(navigator.language||"en");
    setLocale(l);
    const isRtl = rtlLocales.includes(l);
    setDir(isRtl?"rtl":"ltr");
    document.documentElement.dir  = isRtl?"rtl":"ltr";
    document.documentElement.lang = l;
  },[]);

  useEffect(()=>{
    const fn = ()=>setScrolled(window.scrollY>30);
    window.addEventListener("scroll",fn);
    return ()=>window.removeEventListener("scroll",fn);
  },[]);

  const handleWaitlist = async (e:React.FormEvent)=>{
    e.preventDefault();
    if(!email.includes("@")) return;
    setSubmitted(true);
    try{ await fetch(`${API}/waitlist`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email})}); }catch{}
  };

  const features = [
    {icon:Zap,       title:t("f1_title"),desc:t("f1_desc")},
    {icon:Shield,    title:t("f2_title"),desc:t("f2_desc")},
    {icon:TrendingUp,title:t("f3_title"),desc:t("f3_desc")},
    {icon:BarChart3, title:t("f4_title"),desc:t("f4_desc")},
    {icon:Bell,      title:t("f5_title"),desc:t("f5_desc")},
    {icon:Globe,     title:t("f6_title"),desc:t("f6_desc")},
  ];

  return (
    <div style={{direction:dir}}>

      {/* NAV */}
      <header className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${scrolled?"bg-[#050810]/90 backdrop-blur-xl border-b border-white/5":""}`}>
        <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <a href="/" className="flex items-center gap-3">
            <svg width="40" height="40" viewBox="0 0 100 100">
              <defs>
                <linearGradient id="lg1" x1="0%" y1="100%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#0ea5e9"/>
                  <stop offset="100%" stopColor="#10b981"/>
                </linearGradient>
                <linearGradient id="lg2" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.15"/>
                  <stop offset="100%" stopColor="#10b981" stopOpacity="0.05"/>
                </linearGradient>
              </defs>
              <polygon points="50,6 96,90 4,90" fill="url(#lg2)" stroke="url(#lg1)" strokeWidth="3.5" strokeLinejoin="round"/>
              <circle cx="50" cy="52" r="10" fill="none" stroke="url(#lg1)" strokeWidth="2"/>
              <circle cx="50" cy="52" r="3.5" fill="url(#lg1)"/>
              <line x1="50" y1="30" x2="50" y2="42" stroke="url(#lg1)" strokeWidth="1.8" strokeLinecap="round"/>
              <line x1="42" y1="60" x2="26" y2="76" stroke="url(#lg1)" strokeWidth="1.8" strokeLinecap="round"/>
              <line x1="58" y1="60" x2="74" y2="76" stroke="url(#lg1)" strokeWidth="1.8" strokeLinecap="round"/>
              <line x1="40" y1="52" x2="28" y2="52" stroke="url(#lg1)" strokeWidth="1.5" strokeLinecap="round"/>
              <line x1="60" y1="52" x2="72" y2="52" stroke="url(#lg1)" strokeWidth="1.5" strokeLinecap="round"/>
              <circle cx="50" cy="27" r="3" fill="#10b981"/>
              <circle cx="24" cy="78" r="3" fill="#0ea5e9"/>
              <circle cx="76" cy="78" r="3" fill="#0ea5e9"/>
              <circle cx="25" cy="52" r="2" fill="#0ea5e9" opacity="0.7"/>
              <circle cx="75" cy="52" r="2" fill="#0ea5e9" opacity="0.7"/>
            </svg>
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
              <a key={k} href={`#${k}`} onClick={()=>setMenuOpen(false)} className="block py-2 text-white/60">{t(`nav_${k}`)}</a>
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

      {/* AI TOOLS */}
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
        <div className="max-w-7xl mx-auto">
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

          {/* Row 1: Trial + Micro + Starter + Pro */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            {TIER_ROW_1.map(slugKey=>{
              const tier=TIER_CONFIGS[slugKey];
              const monthlyPrice = annual && tier.price_annual ? Math.floor(tier.price_annual/12) : tier.price_monthly;
              const featureList = tier.highlights[locale] ?? tier.highlights["en"] ?? [];
              return(
                <div key={tier.slug} className={`relative rounded-2xl p-6 transition ${tier.popular?"border border-blue-500/40 bg-gradient-to-b from-blue-950/50 to-[#0d1526]":"glass"}`}>
                  {tier.badge&&<div className={`absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap ${tier.popular?"bg-gradient-to-r from-blue-500 to-emerald-500 text-white":"bg-white/10 text-white/70"}`}>{tier.badge}</div>}
                  <h3 className="font-display text-lg font-bold mb-3 mt-2">{TIER_NAMES[tier.slug]?.[locale] ?? tier.name}</h3>
                  <div className="flex items-baseline gap-1 mb-5">
                    {tier.price_monthly===0
                      ? <span className="text-3xl font-bold font-mono grad">Free</span>
                      : <><span className="text-3xl font-bold font-mono">${monthlyPrice}</span><span className="text-white/35 text-sm">{t("pricing_mo")}</span></>
                    }
                  </div>
                  {annual && tier.price_annual && <p className="text-emerald-400 text-xs -mt-3 mb-4">${tier.price_annual}/yr</p>}
                  <a href={tier.price_monthly===0?"/signup":`/checkout?tier=${tier.slug}&billing=${annual?"annual":"monthly"}`}
                     className={`block text-center py-2.5 rounded-xl text-sm font-semibold mb-5 transition ${tier.popular?"btn-primary":"btn-ghost"}`}>
                    <span>{tier.price_monthly===0?"Start Free":t("pricing_cta")}</span>
                  </a>
                  <ul className="space-y-2">
                    {featureList.map((f:string)=>(
                      <li key={f} className="flex items-start gap-2 text-xs">
                        <Check size={12} className="text-emerald-400 mt-0.5 shrink-0"/>
                        <span className="text-white/50">{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>

          {/* Row 2: Elite + Whale + Institutional + Founder */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {TIER_ROW_2.map(slugKey=>{
              const tier=TIER_CONFIGS[slugKey];
              const monthlyPrice = annual && tier.price_annual ? Math.floor(tier.price_annual/12) : tier.price_monthly;
              const isFounder = tier.slug==="founder";
              const isInstitutional = tier.slug==="institutional";
              const featureList = tier.highlights[locale] ?? tier.highlights["en"] ?? [];
              return(
                <div key={tier.slug} className={`relative rounded-2xl p-6 transition ${isFounder?"border border-amber-500/40 bg-gradient-to-b from-amber-950/20 to-[#0d1526]":isInstitutional?"border border-violet-500/30 bg-gradient-to-b from-violet-950/20 to-[#0d1526]":"glass"}`}>
                  {tier.badge&&<div className={`absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap ${isFounder?"bg-gradient-to-r from-amber-500 to-yellow-400 text-black":isInstitutional?"bg-gradient-to-r from-violet-500 to-blue-500 text-white":"bg-white/10 text-white/70"}`}>{tier.badge}</div>}
                  <h3 className={`font-display text-lg font-bold mb-3 mt-2 ${isFounder?"grad-gold":""}`}>{TIER_NAMES[tier.slug]?.[locale] ?? tier.name}</h3>
                  <div className="flex items-baseline gap-1 mb-5">
                    {isFounder&&!annual
                      ? <><span className="text-3xl font-bold font-mono grad-gold">${tier.price_monthly}</span><span className="text-white/35 text-sm">{t("pricing_mo")}</span></>
                      : tier.price_annual===null
                      ? <span className="text-3xl font-bold font-mono grad-gold">${tier.price_monthly}<span className="text-white/35 text-sm text-base font-normal"> {t("pricing_mo")}</span></span>
                      : <><span className="text-3xl font-bold font-mono">${monthlyPrice}</span><span className="text-white/35 text-sm">{t("pricing_mo")}</span></>
                    }
                  </div>
                  {annual && tier.price_annual && <p className="text-emerald-400 text-xs -mt-3 mb-4">${tier.price_annual}/yr</p>}
                  {isFounder&&<p className="text-amber-400/70 text-xs -mt-3 mb-4">Annual billing only</p>}
                  <a href={`/checkout?tier=${tier.slug}&billing=${annual?"annual":"monthly"}`}
                     className={`block text-center py-2.5 rounded-xl text-sm font-semibold mb-5 transition ${isFounder?"bg-gradient-to-r from-amber-500 to-yellow-400 text-black hover:opacity-90":isInstitutional?"bg-gradient-to-r from-violet-600 to-blue-600 text-white hover:opacity-90":"btn-ghost"}`}>
                    <span className="flex items-center justify-center gap-2">{isFounder&&<Star size={14} fill="currentColor"/>}{t("pricing_cta")}</span>
                  </a>
                  <ul className="space-y-2">
                    {featureList.map((f:string)=>(
                      <li key={f} className="flex items-start gap-2 text-xs">
                        <Check size={12} className={`mt-0.5 shrink-0 ${isFounder?"text-amber-400":isInstitutional?"text-violet-400":"text-emerald-400"}`}/>
                        <span className="text-white/50">{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
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
                <svg width="34" height="34" viewBox="0 0 100 100">
                  <defs>
                    <linearGradient id="flg" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0ea5e9"/><stop offset="100%" stopColor="#10b981"/></linearGradient>
                    <linearGradient id="flg2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.15"/><stop offset="100%" stopColor="#10b981" stopOpacity="0.05"/></linearGradient>
                  </defs>
                  <polygon points="50,6 96,90 4,90" fill="url(#flg2)" stroke="url(#flg)" strokeWidth="3.5" strokeLinejoin="round"/>
                  <circle cx="50" cy="52" r="10" fill="none" stroke="url(#flg)" strokeWidth="2"/>
                  <circle cx="50" cy="52" r="3.5" fill="url(#flg)"/>
                  <line x1="50" y1="30" x2="50" y2="42" stroke="url(#flg)" strokeWidth="1.8" strokeLinecap="round"/>
                  <line x1="42" y1="60" x2="26" y2="76" stroke="url(#flg)" strokeWidth="1.8" strokeLinecap="round"/>
                  <line x1="58" y1="60" x2="74" y2="76" stroke="url(#flg)" strokeWidth="1.8" strokeLinecap="round"/>
                  <circle cx="50" cy="27" r="3" fill="#10b981"/>
                  <circle cx="24" cy="78" r="3" fill="#0ea5e9"/>
                  <circle cx="76" cy="78" r="3" fill="#0ea5e9"/>
                </svg>
                <span className="font-display text-xl font-bold">Trado<span className="grad">AI</span></span>
              </div>
              <p className="text-white/35 text-xs leading-relaxed">87 specialized AI tools working together to give you a decisive edge in financial markets.</p>
            </div>
            <div className="grid grid-cols-2 gap-x-12 gap-y-3 text-sm text-white/35">
              <a href="#features" className="hover:text-white transition">{t("nav_features")}</a>
              <a href="/privacy"  className="hover:text-white transition">Privacy</a>
              <a href="#pricing"  className="hover:text-white transition">{t("nav_pricing")}</a>
              <a href="/terms"    className="hover:text-white transition">Terms</a>
              <a href="#faq"      className="hover:text-white transition">{t("nav_faq")}</a>
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
