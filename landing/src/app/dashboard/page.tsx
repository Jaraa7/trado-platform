"use client";
import { TIERS as TIER_CONFIGS, hasFeature as tierHasFeature, hasStrategy as tierHasStrategy, canAddExchange as tierCanAddExchange, canAddPair as tierCanAddPair, canAutoExecute as tierCanAutoExecute } from "@/lib/tiers";
import OpportunityHunter from "./opportunity";
import { useState, useEffect, useCallback } from "react";
import {
  BarChart3, Zap, TrendingUp, Shield, Settings, LogOut,
  Menu, X, Bell, Check, Lock, ArrowUpRight, ArrowDownRight,
  Target, Search, RefreshCw, AlertCircle, Loader2
} from "lucide-react";

// ─── Types & Constants ────────────────────────────────────────────
const TIER = "pro";

// ─── Tier limits from central config ────────────────────────────
const limits = TIER_CONFIGS[TIER as keyof typeof TIER_CONFIGS] ?? TIER_CONFIGS.trial;

// Exchange API endpoints لجلب الأزواج
const EXCHANGE_APIS: Record<string,{spot:string;futures:string;perpetuals:string}> = {
  bybit:   {spot:"https://api.bybit.com/v5/market/instruments-info?category=spot",futures:"https://api.bybit.com/v5/market/instruments-info?category=linear",perpetuals:"https://api.bybit.com/v5/market/instruments-info?category=linear"},
  binance: {spot:"https://api.binance.com/api/v3/exchangeInfo",futures:"https://fapi.binance.com/fapi/v1/exchangeInfo",perpetuals:"https://fapi.binance.com/fapi/v1/exchangeInfo"},
  okx:     {spot:"https://www.okx.com/api/v5/public/instruments?instType=SPOT",futures:"https://www.okx.com/api/v5/public/instruments?instType=FUTURES",perpetuals:"https://www.okx.com/api/v5/public/instruments?instType=SWAP"},
  kucoin:  {spot:"https://api.kucoin.com/api/v1/symbols",futures:"https://api-futures.kucoin.com/api/v1/contracts/active",perpetuals:"https://api-futures.kucoin.com/api/v1/contracts/active"},
  mexc:    {spot:"https://api.mexc.com/api/v3/exchangeInfo",futures:"https://contract.mexc.com/api/v1/contract/list",perpetuals:"https://contract.mexc.com/api/v1/contract/list"},
};

// Parser لكل منصة
function parsePairs(exchange: string, market: string, data: any): string[] {
  try {
    if (exchange === "bybit") {
      return (data.result?.list || [])
        .filter((i:any) => i.status === "Trading" || i.status === "Trading" || i.contractStatus === "Trading")
        .map((i:any) => i.symbol.includes("USDT") ? `${i.baseCoin || i.symbol.replace("USDT","")}/USDT` : null)
        .filter(Boolean).slice(0,200);
    }
    if (exchange === "binance") {
      return (data.symbols || [])
        .filter((i:any) => i.status === "TRADING" && i.quoteAsset === "USDT")
        .map((i:any) => `${i.baseAsset}/USDT`)
        .slice(0,200);
    }
    if (exchange === "okx") {
      return (data.data || [])
        .filter((i:any) => i.state === "live")
        .map((i:any) => {
          const parts = i.instId.split("-");
          return parts.length >= 2 ? `${parts[0]}/${parts[1]}` : null;
        })
        .filter(Boolean).slice(0,200);
    }
    if (exchange === "kucoin") {
      return (data.data || [])
        .filter((i:any) => i.enableTrading && (i.quoteCurrency === "USDT" || i.symbol?.includes("USDTM")))
        .map((i:any) => i.baseCurrency ? `${i.baseCurrency}/USDT` : `${i.symbol?.replace("USDTM","")}/USDT`)
        .filter(Boolean).slice(0,200);
    }
    if (exchange === "mexc") {
      return (data.symbols || data.data || [])
        .filter((i:any) => (i.status === "1" || i.isHot) && (i.quoteAsset === "USDT" || i.quoteCoin === "USDT"))
        .map((i:any) => `${i.baseAsset || i.baseCoin}/USDT`)
        .filter(Boolean).slice(0,200);
    }
  } catch {}
  return [];
}

const FALLBACK_PAIRS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","XRP/USDT","AVAX/USDT","DOGE/USDT","ADA/USDT","DOT/USDT","MATIC/USDT","LINK/USDT","LTC/USDT","TRX/USDT","ATOM/USDT","NEAR/USDT","FTM/USDT","SAND/USDT","MANA/USDT","APT/USDT","ARB/USDT","OP/USDT","SUI/USDT","INJ/USDT","WLD/USDT","TIA/USDT","PYTH/USDT","JTO/USDT","BONK/USDT","PEPE/USDT","WIF/USDT"];

const EXCHANGES = [
  {id:"bybit",   name:"Bybit",   logo:"B", color:"#f7a600"},
  {id:"binance", name:"Binance", logo:"₿", color:"#f0b90b"},
  {id:"okx",     name:"OKX",     logo:"O", color:"#0ec6c6"},
  {id:"kucoin",  name:"KuCoin",  logo:"K", color:"#00a550"},
  {id:"mexc",    name:"MEXC",    logo:"M", color:"#1673ff"},
];

const MARKETS = [
  {id:"spot",       name:"Spot",       desc:"Buy/sell directly"},
  {id:"futures",    name:"Futures",    desc:"Time-limited contracts"},
  {id:"perpetuals", name:"Perpetuals", desc:"No-expiry futures"},
  {id:"options",    name:"Options",    desc:"Rights to buy/sell"},
  {id:"defi",       name:"DeFi",       desc:"Decentralized tokens"},
  {id:"cfd",        name:"CFD",        desc:"Contract for difference"},
];

const STRATEGIES = [
  {id:"trend_following", name:"Trend Following",    desc:"Ride strong market trends",       risk:"Medium",win:"67%",icon:"📈"},
  {id:"breakout",        name:"Breakout Hunter",    desc:"Catch key level breakouts",       risk:"High",  win:"61%",icon:"🚀"},
  {id:"mean_reversion",  name:"Mean Reversion",     desc:"Trade overextended moves back",   risk:"Low",   win:"72%",icon:"🔄"},
  {id:"scalping",        name:"Scalping Pro",       desc:"Quick high-frequency entries",    risk:"High",  win:"58%",icon:"⚡"},
  {id:"custom",          name:"Custom Strategy",    desc:"Build your own rules",            risk:"Custom",win:"—",  icon:"🛠️"},
  {id:"multi_strategy",  name:"Multi-Strategy",     desc:"Run multiple strategies in sync", risk:"Medium",win:"74%",icon:"🎯"},
  {id:"institutional",   name:"Institutional Grade",desc:"Quant-level execution",           risk:"Low",   win:"69%",icon:"🏛️"},
];

const SIGNALS = [
  {symbol:"BTC/USDT",dir:"long", entry:"$103,200",sl:"$100,800",tp:"$108,000",conf:87,rr:"2.4",time:"2m ago", hot:true},
  {symbol:"ETH/USDT",dir:"long", entry:"$2,580",  sl:"$2,490",  tp:"$2,720",  conf:79,rr:"1.6",time:"18m ago",hot:false},
  {symbol:"SOL/USDT",dir:"short",entry:"$182",    sl:"$188",    tp:"$170",    conf:72,rr:"2.0",time:"1h ago", hot:false},
];

const OPPS = [
  {symbol:"INJ/USDT", type:"Volume Spike",       detail:"3.2x avg volume, breaking resistance",conf:91,potential:"+18%"},
  {symbol:"WLD/USDT", type:"Pattern Forming",    detail:"Bull flag on 4H, target $4.80",       conf:84,potential:"+22%"},
  {symbol:"TIA/USDT", type:"Whale Accumulation", detail:"$4.2M bought in last 2 hours",        conf:88,potential:"+15%"},
  {symbol:"PYTH/USDT",type:"News Catalyst",      detail:"Major partnership announced",          conf:76,potential:"+31%"},
];

const STATS = [
  {label:"Total P&L",   value:"+$4,821",sub:"+12.4% this month",up:true},
  {label:"Win Rate",    value:"71.3%",  sub:"last 30 days",     up:true},
  {label:"Open Trades", value:"3",      sub:"2 exchanges",       up:null},
  {label:"Signals Used",value:"47",     sub:`of ${limits.signals_per_day===-1?"∞":limits.signals_per_day} today`,up:null},
];

const NAV = [
  {id:"overview",  label:"Overview",          icon:BarChart3},
  {id:"signals",   label:"Signals",            icon:Zap},
  {id:"hunter",    label:"Opportunity Hunter", icon:Target},
  {id:"setup",     label:"Setup",              icon:Settings},
  {id:"trades",    label:"Trades",             icon:TrendingUp},
  {id:"risk",      label:"Risk",               icon:Shield},
];

function hasFeature(f:string)  { return limits.features.includes(f); }
function hasStrategy(s:string) { return limits.strategies.includes(s); }
function hasMarket(m:string)   { return limits.markets.includes(m); }
function canAddExchange(n:number) { const l=limits.exchanges; return l===-1||n<=l; }

function LockedBadge() {
  return <span style={{display:"inline-flex",alignItems:"center",gap:4,padding:"3px 8px",borderRadius:6,background:"rgba(251,191,36,0.15)",border:"1px solid rgba(251,191,36,0.25)",color:"#fbbf24",fontSize:10,fontWeight:600}}><Lock size={9}/> Upgrade</span>;
}

// ─── Main ─────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [active,setActive]           = useState("overview");
  const [sideOpen,setSideOpen]       = useState(false);
  const [selExchanges,setSelExchanges] = useState<string[]>([]);
  const [selMarket,setSelMarket]     = useState("spot");
  const [selPairs,setSelPairs]       = useState<string[]>([]);
  const [selStrategies,setSelStrategies] = useState<string[]>(["trend_following"]);
  const [pairSearch,setPairSearch]   = useState("");
  const [availablePairs,setAvailablePairs] = useState<string[]>([]);
  const [loadingPairs,setLoadingPairs] = useState(false);
  const [pairsError,setPairsError]   = useState("");
  const [pairsSource,setPairsSource] = useState(""); // which exchange/market loaded

  

  // جلب الأزواج من المنصة عند تغيير Exchange أو Market
  const fetchPairs = useCallback(async (exchanges: string[], market: string) => {
    // لا منصات مربوطة → كل الأزواج متاحة (fallback)
    if (exchanges.length === 0) {
      setAvailablePairs(FALLBACK_PAIRS);
      setPairsSource("default");
      return;
    }

    setLoadingPairs(true);
    setPairsError("");

    try {
      const allPairs = new Set<string>();
      const mkt = market as keyof typeof EXCHANGE_APIS[string];

      for (const exId of exchanges) {
        const url = EXCHANGE_APIS[exId]?.[mkt];
        if (!url) continue;
        try {
          const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          const pairs = parsePairs(exId, market, data);
          pairs.forEach(p => allPairs.add(p));
        } catch (e) {
          console.warn(`Failed to fetch ${exId}:`, e);
        }
      }

      const result = Array.from(allPairs).sort();
      if (result.length > 0) {
        setAvailablePairs(result);
        setPairsSource(`${exchanges.join("+")} · ${market}`);
      } else {
        setAvailablePairs(FALLBACK_PAIRS);
        setPairsSource("default (API unavailable)");
        setPairsError("Could not load live pairs — showing defaults");
      }
    } catch {
      setAvailablePairs(FALLBACK_PAIRS);
      setPairsError("Could not connect to exchange API");
    } finally {
      setLoadingPairs(false);
    }
  }, []);

  // تحميل تلقائي عند فتح Setup أو تغيير المنصة/السوق
  useEffect(() => {
    if (active === "setup") {
      fetchPairs(selExchanges, selMarket);
    }
  }, [active, selExchanges, selMarket, fetchPairs]);

  const toggleExchange = (id:string) => {
    if (selExchanges.includes(id)) {
      const next = selExchanges.filter(e=>e!==id);
      setSelExchanges(next);
      setSelPairs([]); // reset pairs عند تغيير المنصة
    } else {
      if (!canAddExchange(selExchanges.length+1)) return;
      const next = [...selExchanges,id];
      setSelExchanges(next);
      setSelPairs([]);
    }
  };

  const togglePair = (p:string) => {
    if (selPairs.includes(p)) {
      setSelPairs(selPairs.filter(x=>x!==p));
    } else {
      // القفل فقط عند الوصول للحد — لو لا حد (pairs===-1) أو لم يصل → مفتوح
      const max = limits.pairs;
      if (max !== -1 && selPairs.length >= max) return;
      setSelPairs([...selPairs,p]);
    }
  };

  const atPairLimit  = limits.pairs !== -1 && selPairs.length >= limits.pairs;
  const filteredPairs = availablePairs.filter(p => p.toLowerCase().includes(pairSearch.toLowerCase()));

  const bg="#050810";
  const card={background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16};

  return (
    <div style={{background:bg,minHeight:"100vh",color:"#f1f5f9",fontFamily:"'Inter',system-ui,sans-serif",display:"flex"}}>

      {/* SIDEBAR */}
      <aside style={{width:sideOpen?220:64,background:"#080d1a",borderRight:"1px solid rgba(255,255,255,0.06)",display:"flex",flexDirection:"column",transition:"width .2s",flexShrink:0,position:"relative",zIndex:20}}>
        <div style={{padding:"18px 14px",borderBottom:"1px solid rgba(255,255,255,0.06)",display:"flex",alignItems:"center",gap:10}}>
          <svg width="32" height="32" viewBox="0 0 100 100" style={{flexShrink:0}}>
            <defs><linearGradient id="sl" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0ea5e9"/><stop offset="100%" stopColor="#10b981"/></linearGradient></defs>
            <polygon points="50,6 96,90 4,90" fill="rgba(14,165,233,0.1)" stroke="url(#sl)" strokeWidth="3.5" strokeLinejoin="round"/>
            <circle cx="50" cy="52" r="10" fill="none" stroke="url(#sl)" strokeWidth="2"/>
            <circle cx="50" cy="52" r="3.5" fill="url(#sl)"/>
            <line x1="50" y1="30" x2="50" y2="42" stroke="url(#sl)" strokeWidth="1.8" strokeLinecap="round"/>
            <line x1="42" y1="60" x2="26" y2="76" stroke="url(#sl)" strokeWidth="1.8" strokeLinecap="round"/>
            <line x1="58" y1="60" x2="74" y2="76" stroke="url(#sl)" strokeWidth="1.8" strokeLinecap="round"/>
            <circle cx="50" cy="27" r="3" fill="#10b981"/>
            <circle cx="24" cy="78" r="3" fill="#0ea5e9"/>
            <circle cx="76" cy="78" r="3" fill="#0ea5e9"/>
          </svg>
          {sideOpen&&<span style={{fontWeight:700,fontSize:15,background:"linear-gradient(135deg,#0ea5e9,#10b981)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent",whiteSpace:"nowrap"}}>TradoAI</span>}
        </div>
        <button onClick={()=>setSideOpen(!sideOpen)} style={{position:"absolute",top:20,right:-12,width:24,height:24,background:"#0d1526",border:"1px solid rgba(255,255,255,0.1)",borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",cursor:"pointer",color:"rgba(255,255,255,0.5)"}}>
          {sideOpen?<X size={11}/>:<Menu size={11}/>}
        </button>
        <nav style={{flex:1,padding:"10px 0"}}>
          {NAV.map(n=>{
            const locked=n.id==="hunter"&&!hasFeature("opportunity_hunter");
            return(
              <button key={n.id} onClick={()=>!locked&&setActive(n.id)} style={{width:"100%",display:"flex",alignItems:"center",gap:10,padding:"10px 14px",border:"none",background:active===n.id?"rgba(14,165,233,0.1)":"transparent",color:locked?"rgba(255,255,255,0.2)":active===n.id?"#0ea5e9":"rgba(255,255,255,0.45)",borderLeft:active===n.id?"2px solid #0ea5e9":"2px solid transparent",cursor:locked?"not-allowed":"pointer",transition:"all .2s",fontSize:13,fontWeight:active===n.id?600:400,whiteSpace:"nowrap",overflow:"hidden"}}>
                <n.icon size={17} style={{flexShrink:0}}/>
                {sideOpen&&<span style={{flex:1}}>{n.label}</span>}
                {sideOpen&&locked&&<Lock size={11} style={{color:"#fbbf24"}}/>}
              </button>
            );
          })}
        </nav>
        <div style={{padding:"14px",borderTop:"1px solid rgba(255,255,255,0.06)"}}>
          <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:10}}>
            <div style={{width:26,height:26,borderRadius:"50%",background:"linear-gradient(135deg,#0ea5e9,#10b981)",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,fontSize:10,fontWeight:700,color:"#020c07"}}>J</div>
            {sideOpen&&<div><p style={{fontSize:12,fontWeight:600}}>Jaraa7</p><p style={{fontSize:10,color:"rgba(255,255,255,0.35)",textTransform:"capitalize"}}>{TIER} plan</p></div>}
          </div>
          <button style={{width:"100%",display:"flex",alignItems:"center",gap:10,background:"transparent",border:"none",color:"rgba(255,255,255,0.3)",cursor:"pointer",padding:"6px 0",fontSize:12}}>
            <LogOut size={14} style={{flexShrink:0}}/>{sideOpen&&"Sign out"}
          </button>
        </div>
      </aside>

      {/* MAIN */}
      <main style={{flex:1,overflow:"auto"}}>
        <div style={{padding:"18px 28px",borderBottom:"1px solid rgba(255,255,255,0.06)",display:"flex",alignItems:"center",justifyContent:"space-between",background:"rgba(8,13,26,0.9)",backdropFilter:"blur(20px)",position:"sticky",top:0,zIndex:10}}>
          <div>
            <h1 style={{fontSize:18,fontWeight:700}}>{NAV.find(n=>n.id===active)?.label}</h1>
            <p style={{fontSize:11,color:"rgba(255,255,255,0.35)",marginTop:1}}>Welcome back, Jaraa7</p>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            <div style={{padding:"6px 12px",background:"rgba(16,185,129,0.1)",border:"1px solid rgba(16,185,129,0.2)",borderRadius:8,display:"flex",alignItems:"center",gap:6}}>
              <span style={{width:6,height:6,borderRadius:"50%",background:"#10b981"}}/>
              <span style={{fontSize:11,color:"#10b981",fontWeight:600,textTransform:"capitalize"}}>{TIER} Plan</span>
            </div>
            <button style={{padding:"8px",background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:8,color:"rgba(255,255,255,0.6)",cursor:"pointer",position:"relative"}}>
              <Bell size={15}/>
              <span style={{position:"absolute",top:4,right:4,width:6,height:6,background:"#ef4444",borderRadius:"50%"}}/>
            </button>
          </div>
        </div>

        <div style={{padding:"28px"}}>

          {/* OVERVIEW */}
          {active==="overview"&&<>
            <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:14,marginBottom:24}}>
              {STATS.map(s=>(
                <div key={s.label} style={{...card,padding:"18px 20px"}}>
                  <p style={{fontSize:10,color:"rgba(255,255,255,0.4)",textTransform:"uppercase",letterSpacing:".07em",marginBottom:6}}>{s.label}</p>
                  <p style={{fontSize:22,fontWeight:700,fontFamily:"monospace",marginBottom:4,color:s.up===true?"#10b981":s.up===false?"#ef4444":"#f1f5f9"}}>{s.value}</p>
                  <p style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>{s.sub}</p>
                </div>
              ))}
            </div>
            <div style={{...card,padding:"22px",marginBottom:20}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:18}}>
                <h3 style={{fontWeight:600,fontSize:14}}>Portfolio Performance</h3>
                <div style={{display:"flex",gap:6}}>
                  {["1W","1M","3M"].map(p=>(
                    <button key={p} style={{padding:"4px 10px",borderRadius:6,border:"1px solid rgba(255,255,255,0.1)",background:p==="1M"?"rgba(14,165,233,0.15)":"transparent",color:p==="1M"?"#0ea5e9":"rgba(255,255,255,0.4)",fontSize:11,cursor:"pointer"}}>{p}</button>
                  ))}
                </div>
              </div>
              <svg width="100%" height="160" viewBox="0 0 800 160" preserveAspectRatio="none">
                <defs><linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.25"/><stop offset="100%" stopColor="#0ea5e9" stopOpacity="0"/></linearGradient></defs>
                <path d="M0,130 Q100,120 150,100 T300,70 T450,50 T600,30 T800,10 L800,160 L0,160 Z" fill="url(#cg)"/>
                <path d="M0,130 Q100,120 150,100 T300,70 T450,50 T600,30 T800,10" fill="none" stroke="#0ea5e9" strokeWidth="2.5"/>
              </svg>
            </div>
            <div style={{...card,padding:"22px"}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
                <h3 style={{fontWeight:600,fontSize:14}}>Active Configuration</h3>
                <button onClick={()=>setActive("setup")} style={{fontSize:11,color:"#0ea5e9",background:"transparent",border:"none",cursor:"pointer"}}>Edit →</button>
              </div>
              <div style={{display:"flex",flexWrap:"wrap",gap:20}}>
                <div>
                  <p style={{fontSize:10,color:"rgba(255,255,255,0.35)",marginBottom:6,textTransform:"uppercase",letterSpacing:".06em"}}>Exchanges</p>
                  {selExchanges.length===0
                    ? <span style={{fontSize:12,color:"rgba(255,255,255,0.3)"}}>None connected</span>
                    : <div style={{display:"flex",gap:6}}>{selExchanges.map(e=><span key={e} style={{padding:"4px 10px",borderRadius:20,background:"rgba(14,165,233,0.15)",color:"#0ea5e9",fontSize:11,fontWeight:600,textTransform:"capitalize"}}>{e}</span>)}</div>
                  }
                </div>
                <div>
                  <p style={{fontSize:10,color:"rgba(255,255,255,0.35)",marginBottom:6,textTransform:"uppercase",letterSpacing:".06em"}}>Market</p>
                  <span style={{padding:"4px 10px",borderRadius:20,background:"rgba(16,185,129,0.15)",color:"#10b981",fontSize:11,fontWeight:600,textTransform:"capitalize"}}>{selMarket}</span>
                </div>
                <div>
                  <p style={{fontSize:10,color:"rgba(255,255,255,0.35)",marginBottom:6,textTransform:"uppercase",letterSpacing:".06em"}}>Pairs ({selPairs.length})</p>
                  <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
                    {selPairs.length===0
                      ? <span style={{fontSize:12,color:"rgba(255,255,255,0.3)"}}>None selected</span>
                      : <>{selPairs.slice(0,4).map(p=><span key={p} style={{padding:"4px 10px",borderRadius:20,background:"rgba(255,255,255,0.07)",color:"rgba(255,255,255,0.7)",fontSize:11}}>{p}</span>)}
                        {selPairs.length>4&&<span style={{padding:"4px 10px",borderRadius:20,background:"rgba(255,255,255,0.05)",color:"rgba(255,255,255,0.4)",fontSize:11}}>+{selPairs.length-4}</span>}</>
                    }
                  </div>
                </div>
              </div>
            </div>
          </>}

          {/* SIGNALS */}
          {active==="signals"&&<>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:20}}>
              <div style={{display:"flex",alignItems:"center",gap:8,padding:"8px 14px",background:"rgba(16,185,129,0.1)",border:"1px solid rgba(16,185,129,0.2)",borderRadius:10}}>
                <span style={{width:7,height:7,borderRadius:"50%",background:"#10b981"}}/>
                <span style={{fontSize:12,color:"#10b981",fontWeight:600}}>Scanning markets live</span>
              </div>
              <p style={{fontSize:12,color:"rgba(255,255,255,0.35)"}}>{limits.signals_per_day===-1?"Unlimited":`${limits.signals_per_day-47} remaining`} today</p>
            </div>
            <div style={{display:"flex",flexDirection:"column",gap:12}}>
              {SIGNALS.map((s,i)=>(
                <div key={i} style={{...card,padding:"20px 22px",border:`1px solid ${s.hot?"rgba(14,165,233,0.25)":"rgba(255,255,255,0.07)"}`}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"start",marginBottom:14}}>
                    <div style={{display:"flex",alignItems:"center",gap:10}}>
                      <span style={{fontSize:16,fontWeight:700}}>{s.symbol}</span>
                      <span style={{padding:"4px 10px",borderRadius:20,fontSize:11,fontWeight:700,background:s.dir==="long"?"rgba(16,185,129,0.2)":"rgba(239,68,68,0.2)",color:s.dir==="long"?"#10b981":"#ef4444"}}>{s.dir.toUpperCase()}</span>
                      {s.hot&&<span style={{padding:"3px 8px",borderRadius:20,fontSize:10,background:"rgba(251,191,36,0.15)",color:"#fbbf24",fontWeight:600}}>🔥 HOT</span>}
                    </div>
                    <span style={{fontSize:11,color:"rgba(255,255,255,0.3)"}}>{s.time}</span>
                  </div>
                  <div style={{display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:10,marginBottom:14}}>
                    {([["Entry",s.entry,"#f1f5f9"],["Stop Loss",s.sl,"#ef4444"],["Take Profit",s.tp,"#10b981"],["Confidence",s.conf+"%",s.conf>=80?"#10b981":s.conf>=65?"#fbbf24":"#ef4444"],["R:R",s.rr+"x","#0ea5e9"]] as [string,string,string][]).map(([l,v,c])=>(
                      <div key={l} style={{background:"rgba(255,255,255,0.04)",borderRadius:10,padding:"10px 12px"}}>
                        <p style={{fontSize:10,color:"rgba(255,255,255,0.35)",marginBottom:4,textTransform:"uppercase"}}>{l}</p>
                        <p style={{fontSize:13,fontWeight:600,fontFamily:"monospace",color:c}}>{v}</p>
                      </div>
                    ))}
                  </div>
                  <div style={{display:"flex",gap:8}}>
                    <button style={{flex:1,padding:"9px",borderRadius:10,background:"linear-gradient(135deg,#0ea5e9,#10b981)",border:"none",color:"#020c07",fontWeight:700,fontSize:13,cursor:"pointer"}}>Execute Trade</button>
                    <button style={{padding:"9px 18px",borderRadius:10,background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.1)",color:"rgba(255,255,255,0.5)",fontSize:13,cursor:"pointer"}}>Dismiss</button>
                  </div>
                </div>
              ))}
            </div>
          </>}

          {/* OPPORTUNITY HUNTER */}
          {active==="hunter"&&(hasFeature("opportunity_hunter")?<OpportunityHunter/>:(
            <div style={{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",minHeight:400,gap:16,textAlign:"center"}}>
              <div style={{fontSize:48}}>🎯</div>
              <h2 style={{fontSize:22,fontWeight:700}}>Opportunity Hunter</h2>
              <p style={{color:"rgba(255,255,255,0.5)",maxWidth:360,lineHeight:1.7}}>AI scans for hidden opportunities beyond your signal queue. Available from Starter plan.</p>
              <a href="/checkout?tier=starter" style={{padding:"12px 32px",borderRadius:12,background:"linear-gradient(135deg,#0ea5e9,#10b981)",color:"#020c07",fontWeight:700,fontSize:14,textDecoration:"none"}}>Upgrade to Starter</a>
            </div>
          ))}

          {/* SETUP */}
          {active==="setup"&&(
            <div style={{display:"flex",flexDirection:"column",gap:20}}>

              {/* Exchange */}
              <div style={{...card,padding:"22px"}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16}}>
                  <div>
                    <h3 style={{fontWeight:600,fontSize:15,marginBottom:2}}>Exchange</h3>
                    <p style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>
                      Connect up to {limits.exchanges===-1?"unlimited":limits.exchanges} exchange{limits.exchanges!==1?"s":""}
                      {selExchanges.length===0&&<span style={{color:"rgba(255,255,255,0.5)"}}> — all pairs available until you connect one</span>}
                    </p>
                  </div>
                  <span style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>{selExchanges.length}/{limits.exchanges===-1?"∞":limits.exchanges}</span>
                </div>
                <div style={{display:"flex",gap:10,flexWrap:"wrap"}}>
                  {EXCHANGES.map((ex,i)=>{
                    const canAdd = canAddExchange(selExchanges.length+1)||selExchanges.includes(ex.id);
                    const selected=selExchanges.includes(ex.id);
                    return(
                      <button key={ex.id} onClick={()=>canAdd&&toggleExchange(ex.id)} style={{display:"flex",alignItems:"center",gap:10,padding:"12px 18px",borderRadius:12,border:selected?`1px solid ${ex.color}40`:"1px solid rgba(255,255,255,0.08)",background:selected?`${ex.color}18`:"rgba(255,255,255,0.03)",cursor:canAdd?"pointer":"not-allowed",opacity:canAdd?1:0.4,transition:"all .2s",position:"relative"}}>
                        <div style={{width:28,height:28,borderRadius:"50%",background:ex.color+"30",display:"flex",alignItems:"center",justifyContent:"center",fontSize:13,fontWeight:700,color:ex.color}}>{ex.logo}</div>
                        <span style={{fontSize:13,fontWeight:600}}>{ex.name}</span>
                        {selected&&<Check size={14} style={{color:ex.color}}/>}
                        {!canAdd&&<Lock size={12} style={{color:"#fbbf24",position:"absolute",top:6,right:6}}/>}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Market */}
              <div style={{...card,padding:"22px"}}>
                <h3 style={{fontWeight:600,fontSize:15,marginBottom:4}}>Market Type</h3>
                <p style={{fontSize:11,color:"rgba(255,255,255,0.35)",marginBottom:16}}>Pairs list will update based on selected market</p>
                <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10}}>
                  {MARKETS.map(m=>{
                    const allowed=hasMarket(m.id);
                    const selected=selMarket===m.id;
                    return(
                      <button key={m.id} onClick={()=>allowed&&setSelMarket(m.id)} style={{padding:"14px 16px",borderRadius:12,textAlign:"left",border:selected?"1px solid rgba(14,165,233,0.4)":"1px solid rgba(255,255,255,0.07)",background:selected?"rgba(14,165,233,0.1)":"rgba(255,255,255,0.02)",cursor:allowed?"pointer":"not-allowed",opacity:allowed?1:0.35,transition:"all .2s",position:"relative"}}>
                        <div style={{display:"flex",justifyContent:"space-between",alignItems:"start",marginBottom:4}}>
                          <span style={{fontSize:13,fontWeight:600,color:selected?"#0ea5e9":"#f1f5f9"}}>{m.name}</span>
                          {!allowed?<Lock size={11} style={{color:"#fbbf24"}}/>:selected?<Check size={13} style={{color:"#0ea5e9"}}/>:null}
                        </div>
                        <p style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>{m.desc}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Pairs */}
              <div style={{...card,padding:"22px"}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
                  <div>
                    <h3 style={{fontWeight:600,fontSize:15,marginBottom:2}}>Trading Pairs</h3>
                    <p style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>
                      {selExchanges.length===0
                        ? "Connect an exchange to load its pairs — all available for now"
                        : pairsSource?`From: ${pairsSource}`:"Loading..."}
                      {limits.pairs!==-1&&` · Max ${limits.pairs} pairs`}
                      {` · ${selPairs.length} selected`}
                    </p>
                  </div>
                  <div style={{display:"flex",alignItems:"center",gap:8}}>
                    <div style={{display:"flex",alignItems:"center",gap:6,padding:"7px 12px",background:"rgba(255,255,255,0.04)",borderRadius:9,border:"1px solid rgba(255,255,255,0.08)"}}>
                      <Search size={12} style={{color:"rgba(255,255,255,0.35)"}}/>
                      <input value={pairSearch} onChange={e=>setPairSearch(e.target.value)} placeholder="Search..." style={{background:"transparent",border:"none",outline:"none",color:"#f1f5f9",fontSize:12,width:90}}/>
                    </div>
                    <button onClick={()=>fetchPairs(selExchanges,selMarket)} style={{padding:"7px",background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:9,color:"rgba(255,255,255,0.5)",cursor:"pointer"}}>
                      {loadingPairs?<Loader2 size={14} style={{animation:"spin 1s linear infinite"}}/>:<RefreshCw size={14}/>}
                    </button>
                  </div>
                </div>

                {pairsError&&(
                  <div style={{display:"flex",alignItems:"center",gap:8,padding:"8px 12px",background:"rgba(251,191,36,0.08)",border:"1px solid rgba(251,191,36,0.15)",borderRadius:8,marginBottom:12}}>
                    <AlertCircle size={13} style={{color:"#fbbf24",flexShrink:0}}/>
                    <span style={{fontSize:11,color:"#fbbf24"}}>{pairsError}</span>
                  </div>
                )}

                {loadingPairs?(
                  <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:10,padding:"32px",color:"rgba(255,255,255,0.4)"}}>
                    <Loader2 size={18} style={{animation:"spin 1s linear infinite"}}/>
                    <span style={{fontSize:13}}>Loading pairs from {selExchanges.join(", ")}...</span>
                  </div>
                ):(
                  <>
                    <div style={{display:"flex",flexWrap:"wrap",gap:8,maxHeight:260,overflowY:"auto",paddingRight:4}}>
                      {filteredPairs.map(p=>{
                        const selected=selPairs.includes(p);
                        // القفل فقط عند الوصول للحد مع عدم التحديد
                        const disabled=!selected&&atPairLimit;
                        return(
                          <button key={p} onClick={()=>!disabled&&togglePair(p)} style={{padding:"6px 14px",borderRadius:20,fontSize:12,fontWeight:600,border:selected?"1px solid rgba(16,185,129,0.5)":"1px solid rgba(255,255,255,0.08)",background:selected?"rgba(16,185,129,0.15)":"rgba(255,255,255,0.03)",color:selected?"#10b981":disabled?"rgba(255,255,255,0.2)":"rgba(255,255,255,0.6)",cursor:disabled?"not-allowed":"pointer",transition:"all .15s",position:"relative"}}>
                            {p}
                            {disabled&&!selected&&<Lock size={9} style={{marginLeft:4,color:"#fbbf24",verticalAlign:"middle"}}/>}
                          </button>
                        );
                      })}
                    </div>
                    {atPairLimit&&(
                      <div style={{marginTop:12,padding:"10px 14px",background:"rgba(251,191,36,0.08)",border:"1px solid rgba(251,191,36,0.2)",borderRadius:9,display:"flex",alignItems:"center",gap:8}}>
                        <Lock size={13} style={{color:"#fbbf24"}}/>
                        <p style={{fontSize:12,color:"#fbbf24"}}>Reached {limits.pairs}-pair limit. <a href="/checkout?tier=elite" style={{color:"#fbbf24",textDecoration:"underline"}}>Upgrade for unlimited pairs</a></p>
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Strategies */}
              <div style={{...card,padding:"22px"}}>
                <h3 style={{fontWeight:600,fontSize:15,marginBottom:4}}>AI Strategy</h3>
                <p style={{fontSize:11,color:"rgba(255,255,255,0.35)",marginBottom:16}}>Choose strategies for your AI to follow</p>
                <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
                  {STRATEGIES.map(s=>{
                    const allowed=hasStrategy(s.id);
                    const selected=selStrategies.includes(s.id);
                    return(
                      <button key={s.id} onClick={()=>allowed&&(selected?setSelStrategies(selStrategies.filter(x=>x!==s.id)):setSelStrategies([...selStrategies,s.id]))} style={{padding:"16px",borderRadius:12,textAlign:"left",border:selected?"1px solid rgba(99,102,241,0.4)":"1px solid rgba(255,255,255,0.07)",background:selected?"rgba(99,102,241,0.1)":"rgba(255,255,255,0.02)",cursor:allowed?"pointer":"not-allowed",opacity:allowed?1:0.4,transition:"all .2s",position:"relative"}}>
                        <div style={{display:"flex",justifyContent:"space-between",alignItems:"start",marginBottom:6}}>
                          <div style={{display:"flex",alignItems:"center",gap:8}}>
                            <span style={{fontSize:18}}>{s.icon}</span>
                            <span style={{fontSize:13,fontWeight:700}}>{s.name}</span>
                          </div>
                          {!allowed?<LockedBadge/>:selected?<Check size={14} style={{color:"#818cf8"}}/>:null}
                        </div>
                        <p style={{fontSize:11,color:"rgba(255,255,255,0.4)",marginBottom:8}}>{s.desc}</p>
                        <div style={{display:"flex",gap:10}}>
                          <span style={{fontSize:10,color:"rgba(255,255,255,0.4)"}}>Risk: <span style={{color:s.risk==="Low"?"#10b981":s.risk==="High"?"#ef4444":"#fbbf24",fontWeight:600}}>{s.risk}</span></span>
                          <span style={{fontSize:10,color:"rgba(255,255,255,0.4)"}}>Win: <span style={{color:"#0ea5e9",fontWeight:600}}>{s.win}</span></span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              <button style={{padding:"14px",borderRadius:12,background:"linear-gradient(135deg,#0ea5e9,#10b981)",border:"none",color:"#020c07",fontWeight:700,fontSize:14,cursor:"pointer"}}>
                Save Configuration & Activate
              </button>
            </div>
          )}

          {/* TRADES */}
          {active==="trades"&&(
            <div style={{...card,padding:"22px"}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:18}}>
                <h3 style={{fontWeight:600,fontSize:14}}>Trade History</h3>
                <div style={{display:"flex",gap:8}}>
                  {["All","Open","Closed"].map(f=>(
                    <button key={f} style={{padding:"5px 12px",borderRadius:7,border:"1px solid rgba(255,255,255,0.1)",background:f==="All"?"rgba(14,165,233,0.15)":"transparent",color:f==="All"?"#0ea5e9":"rgba(255,255,255,0.4)",fontSize:11,cursor:"pointer"}}>{f}</button>
                  ))}
                </div>
              </div>
              {[{sym:"BTC/USDT",dir:"long",entry:101200,exit:104850,pnl:"+$365",up:true,st:"open"},{sym:"ETH/USDT",dir:"long",entry:2480,exit:2610,pnl:"+$130",up:true,st:"closed"},{sym:"SOL/USDT",dir:"short",entry:182,exit:178,pnl:"+$40",up:true,st:"closed"},{sym:"BNB/USDT",dir:"long",entry:598,exit:591,pnl:"-$70",up:false,st:"closed"}].map((t,i)=>(
                <div key={i} style={{display:"grid",gridTemplateColumns:"1fr auto auto auto auto auto",gap:16,alignItems:"center",padding:"13px 0",borderBottom:"1px solid rgba(255,255,255,0.04)"}}>
                  <span style={{fontWeight:600}}>{t.sym}</span>
                  <span style={{padding:"3px 10px",borderRadius:20,fontSize:11,fontWeight:600,background:t.dir==="long"?"rgba(16,185,129,0.15)":"rgba(239,68,68,0.15)",color:t.dir==="long"?"#10b981":"#ef4444"}}>{t.dir.toUpperCase()}</span>
                  <span style={{fontSize:12,fontFamily:"monospace",color:"rgba(255,255,255,0.5)"}}>${t.entry.toLocaleString()}</span>
                  <span style={{fontSize:12,fontFamily:"monospace"}}>${t.exit.toLocaleString()}</span>
                  <span style={{fontSize:13,fontWeight:700,color:t.up?"#10b981":"#ef4444"}}>{t.pnl}</span>
                  <span style={{padding:"3px 10px",borderRadius:20,fontSize:11,background:t.st==="open"?"rgba(14,165,233,0.15)":"rgba(255,255,255,0.06)",color:t.st==="open"?"#0ea5e9":"rgba(255,255,255,0.4)"}}>{t.st}</span>
                </div>
              ))}
            </div>
          )}

          {/* RISK */}
          {active==="risk"&&(
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
              {[{label:"Daily Loss Limit",used:1.2,max:6,color:"#10b981"},{label:"Max Drawdown",used:3.8,max:15,color:"#fbbf24"},{label:"Position Concentration",used:28,max:30,color:"#ef4444"},{label:"Leverage Used",used:1.5,max:3,color:"#0ea5e9"}].map(r=>(
                <div key={r.label} style={{...card,padding:"22px"}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:12}}>
                    <p style={{fontWeight:600,fontSize:14}}>{r.label}</p>
                    <p style={{fontFamily:"monospace",fontSize:13,color:r.color}}>{r.used}/{r.max}{r.label.includes("Leverage")?"x":"%"}</p>
                  </div>
                  <div style={{height:8,background:"rgba(255,255,255,0.07)",borderRadius:4,overflow:"hidden"}}>
                    <div style={{height:"100%",width:`${(r.used/r.max)*100}%`,background:r.color,borderRadius:4}}/>
                  </div>
                  <p style={{marginTop:8,fontSize:11,color:"rgba(255,255,255,0.35)"}}>{((r.used/r.max)*100).toFixed(0)}% of limit used</p>
                </div>
              ))}
              <div style={{gridColumn:"1/-1",background:"rgba(16,185,129,0.07)",border:"1px solid rgba(16,185,129,0.2)",borderRadius:14,padding:"18px 22px",display:"flex",alignItems:"center",gap:12}}>
                <span style={{fontSize:24}}>✅</span>
                <div>
                  <p style={{fontWeight:600,color:"#10b981",marginBottom:2}}>All parameters within limits</p>
                  <p style={{fontSize:12,color:"rgba(255,255,255,0.4)"}}>Risk Guardian monitoring all positions. Last check: 8 seconds ago.</p>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>
      <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>
    </div>
  );
}
