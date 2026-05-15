"use client";

import { useState } from "react";
import {
  TrendingUp, TrendingDown, Shield, Bell, Settings,
  LogOut, BarChart3, Zap, ChevronUp, ChevronDown,
  ArrowUpRight, ArrowDownRight, Clock, CheckCircle,
  AlertCircle, Menu, X
} from "lucide-react";

// ─── Mock Data ────────────────────────────────────────────────────────────────
const STATS = [
  { label: "Total P&L",      value: "+$4,821",  sub: "+12.4% this month", up: true  },
  { label: "Win Rate",       value: "71.3%",    sub: "last 30 days",      up: true  },
  { label: "Open Trades",    value: "3",        sub: "across 2 exchanges",up: null  },
  { label: "AI Signals",     value: "47",       sub: "used this month",   up: null  },
];

const TRADES = [
  { symbol:"BTC/USDT", dir:"long",  entry:101200, current:104850, pnl:"+$365", pnl_pct:"+3.6%", up:true,  status:"open",   time:"2h ago"   },
  { symbol:"ETH/USDT", dir:"long",  entry:2480,   current:2610,  pnl:"+$130", pnl_pct:"+5.2%", up:true,  status:"open",   time:"5h ago"   },
  { symbol:"SOL/USDT", dir:"short", entry:182,     current:178,   pnl:"+$40",  pnl_pct:"+2.2%", up:true,  status:"open",   time:"1d ago"   },
  { symbol:"BNB/USDT", dir:"long",  entry:598,     current:591,   pnl:"-$70",  pnl_pct:"-1.2%", up:false, status:"closed", time:"2d ago"   },
  { symbol:"XRP/USDT", dir:"long",  entry:0.62,    current:0.71,  pnl:"+$90",  pnl_pct:"+14.5%",up:true,  status:"closed", time:"3d ago"   },
];

const SIGNALS = [
  { symbol:"BTC/USDT", dir:"long",  entry:"$103,200", sl:"$100,800", tp:"$108,000", conf:87, rr:"2.4", time:"2 min ago",  status:"active"  },
  { symbol:"ETH/USDT", dir:"long",  entry:"$2,580",   sl:"$2,490",   tp:"$2,720",   conf:79, rr:"1.6", time:"18 min ago", status:"active"  },
  { symbol:"SOL/USDT", dir:"short", entry:"$182",     sl:"$188",     tp:"$170",     conf:72, rr:"2.0", time:"1h ago",     status:"active"  },
  { symbol:"AVAX/USDT",dir:"long",  entry:"$38.4",    sl:"$36.8",    tp:"$42.0",    conf:65, rr:"2.2", time:"3h ago",     status:"expired" },
];

const NAV = [
  { id:"overview",  label:"Overview",  icon:BarChart3  },
  { id:"signals",   label:"Signals",   icon:Zap        },
  { id:"trades",    label:"Trades",    icon:TrendingUp },
  { id:"risk",      label:"Risk",      icon:Shield     },
  { id:"settings",  label:"Settings",  icon:Settings   },
];

export default function DashboardPage() {
  const [active, setActive] = useState("overview");
  const [sideOpen, setSideOpen] = useState(false);

  return (
    <div style={{background:"#050810",minHeight:"100vh",color:"#f1f5f9",fontFamily:"'Inter',system-ui,sans-serif",display:"flex"}}>

      {/* ─── SIDEBAR ──────────────────────────────────────────────── */}
      <aside style={{
        width: sideOpen ? 220 : 64,
        background:"#080d1a",
        borderRight:"1px solid rgba(255,255,255,0.06)",
        display:"flex",flexDirection:"column",
        transition:"width .2s ease",
        flexShrink:0,
        position:"relative",zIndex:20
      }}>
        {/* Logo */}
        <div style={{padding:"20px 16px",borderBottom:"1px solid rgba(255,255,255,0.06)",display:"flex",alignItems:"center",gap:12}}>
          <svg width="32" height="32" viewBox="0 0 100 100" style={{flexShrink:0}}>
            <defs>
              <linearGradient id="sl" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#0ea5e9"/>
                <stop offset="100%" stopColor="#10b981"/>
              </linearGradient>
            </defs>
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
          {sideOpen && <span style={{fontWeight:700,fontSize:16,background:"linear-gradient(135deg,#0ea5e9,#10b981)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent",whiteSpace:"nowrap"}}>TradoAI</span>}
        </div>

        {/* Toggle */}
        <button onClick={()=>setSideOpen(!sideOpen)} style={{position:"absolute",top:22,right:-12,width:24,height:24,background:"#0d1526",border:"1px solid rgba(255,255,255,0.1)",borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",cursor:"pointer",color:"rgba(255,255,255,0.5)"}}>
          {sideOpen ? <X size={12}/> : <Menu size={12}/>}
        </button>

        {/* Nav */}
        <nav style={{flex:1,padding:"12px 0"}}>
          {NAV.map(n=>(
            <button key={n.id} onClick={()=>setActive(n.id)} style={{
              width:"100%",display:"flex",alignItems:"center",gap:12,
              padding:"11px 16px",border:"none",background:active===n.id?"rgba(14,165,233,0.1)":"transparent",
              color:active===n.id?"#0ea5e9":"rgba(255,255,255,0.45)",
              borderLeft:active===n.id?"2px solid #0ea5e9":"2px solid transparent",
              cursor:"pointer",transition:"all .2s",fontSize:13,fontWeight:active===n.id?600:400,
              whiteSpace:"nowrap",overflow:"hidden"
            }}>
              <n.icon size={18} style={{flexShrink:0}}/>
              {sideOpen && n.label}
            </button>
          ))}
        </nav>

        {/* User */}
        <div style={{padding:"16px",borderTop:"1px solid rgba(255,255,255,0.06)"}}>
          <button style={{width:"100%",display:"flex",alignItems:"center",gap:12,background:"transparent",border:"none",color:"rgba(255,255,255,0.4)",cursor:"pointer",padding:"8px 0"}}>
            <LogOut size={16} style={{flexShrink:0}}/>
            {sideOpen && <span style={{fontSize:12}}>Sign out</span>}
          </button>
        </div>
      </aside>

      {/* ─── MAIN ─────────────────────────────────────────────────── */}
      <main style={{flex:1,overflow:"auto"}}>

        {/* Header */}
        <div style={{padding:"24px 32px",borderBottom:"1px solid rgba(255,255,255,0.06)",display:"flex",alignItems:"center",justifyContent:"space-between",background:"rgba(8,13,26,0.8)",backdropFilter:"blur(20px)",position:"sticky",top:0,zIndex:10}}>
          <div>
            <h1 style={{fontSize:20,fontWeight:700,marginBottom:2}}>
              {active==="overview"&&"Overview"}
              {active==="signals"&&"AI Signals"}
              {active==="trades"&&"My Trades"}
              {active==="risk"&&"Risk Monitor"}
              {active==="settings"&&"Settings"}
            </h1>
            <p style={{fontSize:12,color:"rgba(255,255,255,0.4)"}}>Welcome back, Jaraa7</p>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:12}}>
            <div style={{display:"flex",alignItems:"center",gap:6,padding:"6px 12px",background:"rgba(16,185,129,0.1)",border:"1px solid rgba(16,185,129,0.2)",borderRadius:8}}>
              <span style={{width:6,height:6,borderRadius:"50%",background:"#10b981",animation:"pulse 2s infinite"}}/>
              <span style={{fontSize:11,color:"#10b981",fontWeight:600}}>Pro Plan</span>
            </div>
            <button style={{padding:"8px",background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:8,color:"rgba(255,255,255,0.6)",cursor:"pointer",position:"relative"}}>
              <Bell size={16}/>
              <span style={{position:"absolute",top:4,right:4,width:6,height:6,background:"#ef4444",borderRadius:"50%"}}/>
            </button>
          </div>
        </div>

        <div style={{padding:"32px"}}>

          {/* ── OVERVIEW ── */}
          {active==="overview" && <>

            {/* Stats */}
            <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:16,marginBottom:32}}>
              {STATS.map(s=>(
                <div key={s.label} style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16,padding:"20px 24px"}}>
                  <p style={{fontSize:11,color:"rgba(255,255,255,0.4)",marginBottom:8,textTransform:"uppercase",letterSpacing:".05em"}}>{s.label}</p>
                  <p style={{fontSize:26,fontWeight:700,fontFamily:"'JetBrains Mono',monospace",marginBottom:4,color:s.up===true?"#10b981":s.up===false?"#ef4444":"#f1f5f9"}}>{s.value}</p>
                  <p style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>{s.sub}</p>
                </div>
              ))}
            </div>

            {/* Chart placeholder */}
            <div style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16,padding:"24px",marginBottom:24}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:20}}>
                <h3 style={{fontWeight:600,fontSize:15}}>Portfolio Performance</h3>
                <div style={{display:"flex",gap:8}}>
                  {["1W","1M","3M","1Y"].map(p=>(
                    <button key={p} style={{padding:"4px 12px",borderRadius:6,border:"1px solid rgba(255,255,255,0.1)",background:p==="1M"?"rgba(14,165,233,0.15)":"transparent",color:p==="1M"?"#0ea5e9":"rgba(255,255,255,0.4)",fontSize:11,cursor:"pointer"}}>
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              <svg width="100%" height="180" viewBox="0 0 800 180" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.3"/>
                    <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0"/>
                  </linearGradient>
                </defs>
                <path d="M0,140 Q100,130 150,110 T300,80 T450,60 T600,40 T800,20 L800,180 L0,180 Z" fill="url(#cg)"/>
                <path d="M0,140 Q100,130 150,110 T300,80 T450,60 T600,40 T800,20" fill="none" stroke="#0ea5e9" strokeWidth="2.5"/>
                <circle cx="800" cy="20" r="5" fill="#0ea5e9"/>
              </svg>
            </div>

            {/* Recent Trades */}
            <div style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16,padding:"24px"}}>
              <h3 style={{fontWeight:600,fontSize:15,marginBottom:20}}>Recent Trades</h3>
              <div style={{overflowX:"auto"}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
                  <thead>
                    <tr style={{borderBottom:"1px solid rgba(255,255,255,0.06)"}}>
                      {["Pair","Direction","Entry","Current","P&L","Status","Time"].map(h=>(
                        <th key={h} style={{padding:"8px 12px",textAlign:"left",color:"rgba(255,255,255,0.35)",fontWeight:500,fontSize:11,textTransform:"uppercase",letterSpacing:".05em"}}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {TRADES.slice(0,5).map((t,i)=>(
                      <tr key={i} style={{borderBottom:"1px solid rgba(255,255,255,0.04)"}}>
                        <td style={{padding:"12px",fontWeight:600}}>{t.symbol}</td>
                        <td style={{padding:"12px"}}>
                          <span style={{padding:"3px 10px",borderRadius:20,fontSize:11,fontWeight:600,background:t.dir==="long"?"rgba(16,185,129,0.15)":"rgba(239,68,68,0.15)",color:t.dir==="long"?"#10b981":"#ef4444"}}>
                            {t.dir.toUpperCase()}
                          </span>
                        </td>
                        <td style={{padding:"12px",fontFamily:"monospace",color:"rgba(255,255,255,0.6)"}}>${t.entry.toLocaleString()}</td>
                        <td style={{padding:"12px",fontFamily:"monospace"}}>${t.current.toLocaleString()}</td>
                        <td style={{padding:"12px",fontWeight:600,color:t.up?"#10b981":"#ef4444"}}>
                          <div style={{display:"flex",alignItems:"center",gap:4}}>
                            {t.up?<ArrowUpRight size={14}/>:<ArrowDownRight size={14}/>}
                            {t.pnl} ({t.pnl_pct})
                          </div>
                        </td>
                        <td style={{padding:"12px"}}>
                          <span style={{padding:"3px 10px",borderRadius:20,fontSize:11,background:t.status==="open"?"rgba(14,165,233,0.15)":"rgba(255,255,255,0.08)",color:t.status==="open"?"#0ea5e9":"rgba(255,255,255,0.4)"}}>
                            {t.status}
                          </span>
                        </td>
                        <td style={{padding:"12px",color:"rgba(255,255,255,0.35)",fontSize:12}}><Clock size={12} style={{display:"inline",marginRight:4}}/>{t.time}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>}

          {/* ── SIGNALS ── */}
          {active==="signals" && <>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:24}}>
              <div style={{display:"flex",alignItems:"center",gap:8,padding:"8px 16px",background:"rgba(16,185,129,0.1)",border:"1px solid rgba(16,185,129,0.2)",borderRadius:10}}>
                <span style={{width:8,height:8,borderRadius:"50%",background:"#10b981",animation:"pulse 2s infinite"}}/>
                <span style={{fontSize:12,color:"#10b981",fontWeight:600}}>Live — scanning markets</span>
              </div>
              <p style={{fontSize:12,color:"rgba(255,255,255,0.35)"}}>43 signals remaining today</p>
            </div>
            <div style={{display:"flex",flexDirection:"column",gap:12}}>
              {SIGNALS.map((s,i)=>(
                <div key={i} style={{background:"#0d1526",border:`1px solid ${s.status==="active"?"rgba(14,165,233,0.2)":"rgba(255,255,255,0.06)"}`,borderRadius:16,padding:"20px 24px",opacity:s.status==="expired"?.5:1}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"start",marginBottom:16}}>
                    <div style={{display:"flex",alignItems:"center",gap:12}}>
                      <span style={{fontSize:17,fontWeight:700}}>{s.symbol}</span>
                      <span style={{padding:"4px 12px",borderRadius:20,fontSize:12,fontWeight:600,background:s.dir==="long"?"rgba(16,185,129,0.15)":"rgba(239,68,68,0.15)",color:s.dir==="long"?"#10b981":"#ef4444"}}>{s.dir.toUpperCase()}</span>
                      {s.status==="expired"&&<span style={{padding:"4px 12px",borderRadius:20,fontSize:11,background:"rgba(255,255,255,0.06)",color:"rgba(255,255,255,0.3)"}}>Expired</span>}
                    </div>
                    <span style={{fontSize:11,color:"rgba(255,255,255,0.3)"}}>{s.time}</span>
                  </div>
                  <div style={{display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:12}}>
                    {[["Entry",s.entry,"#f1f5f9"],["Stop Loss",s.sl,"#ef4444"],["Take Profit",s.tp,"#10b981"],["Confidence",s.conf+"%",s.conf>=80?"#10b981":s.conf>=65?"#fbbf24":"#ef4444"],["Risk/Reward",s.rr+"x","#0ea5e9"]].map(([l,v,c])=>(
                      <div key={l as string} style={{background:"rgba(255,255,255,0.04)",borderRadius:10,padding:"12px"}}>
                        <p style={{fontSize:10,color:"rgba(255,255,255,0.35)",marginBottom:4,textTransform:"uppercase",letterSpacing:".05em"}}>{l as string}</p>
                        <p style={{fontSize:14,fontWeight:600,fontFamily:"monospace",color:c as string}}>{v as string}</p>
                      </div>
                    ))}
                  </div>
                  {s.status==="active"&&(
                    <div style={{marginTop:16,display:"flex",gap:10}}>
                      <button style={{flex:1,padding:"10px",borderRadius:10,background:"linear-gradient(135deg,#0ea5e9,#10b981)",border:"none",color:"#020c07",fontWeight:700,fontSize:13,cursor:"pointer"}}>
                        Execute Trade
                      </button>
                      <button style={{padding:"10px 20px",borderRadius:10,background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.1)",color:"rgba(255,255,255,0.6)",fontSize:13,cursor:"pointer"}}>
                        Dismiss
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>}

          {/* ── TRADES ── */}
          {active==="trades" && (
            <div style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16,padding:"24px"}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:20}}>
                <h3 style={{fontWeight:600,fontSize:15}}>All Trades</h3>
                <div style={{display:"flex",gap:8}}>
                  {["All","Open","Closed"].map(f=>(
                    <button key={f} style={{padding:"6px 14px",borderRadius:8,border:"1px solid rgba(255,255,255,0.1)",background:f==="All"?"rgba(14,165,233,0.15)":"transparent",color:f==="All"?"#0ea5e9":"rgba(255,255,255,0.4)",fontSize:12,cursor:"pointer"}}>{f}</button>
                  ))}
                </div>
              </div>
              <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
                <thead>
                  <tr style={{borderBottom:"1px solid rgba(255,255,255,0.06)"}}>
                    {["Pair","Dir","Entry","Exit","P&L","Status","Time"].map(h=>(
                      <th key={h} style={{padding:"8px 12px",textAlign:"left",color:"rgba(255,255,255,0.35)",fontWeight:500,fontSize:11,textTransform:"uppercase"}}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {TRADES.map((t,i)=>(
                    <tr key={i} style={{borderBottom:"1px solid rgba(255,255,255,0.04)"}}>
                      <td style={{padding:"12px",fontWeight:600}}>{t.symbol}</td>
                      <td style={{padding:"12px"}}>
                        <span style={{padding:"3px 10px",borderRadius:20,fontSize:11,fontWeight:600,background:t.dir==="long"?"rgba(16,185,129,0.15)":"rgba(239,68,68,0.15)",color:t.dir==="long"?"#10b981":"#ef4444"}}>{t.dir.toUpperCase()}</span>
                      </td>
                      <td style={{padding:"12px",fontFamily:"monospace",fontSize:12}}>${t.entry.toLocaleString()}</td>
                      <td style={{padding:"12px",fontFamily:"monospace",fontSize:12,color:"rgba(255,255,255,0.5)"}}>{t.status==="open"?"—":"$"+t.current.toLocaleString()}</td>
                      <td style={{padding:"12px",fontWeight:600,color:t.up?"#10b981":"#ef4444"}}>{t.pnl} ({t.pnl_pct})</td>
                      <td style={{padding:"12px"}}>
                        <span style={{padding:"3px 10px",borderRadius:20,fontSize:11,background:t.status==="open"?"rgba(14,165,233,0.15)":"rgba(255,255,255,0.06)",color:t.status==="open"?"#0ea5e9":"rgba(255,255,255,0.35)"}}>{t.status}</span>
                      </td>
                      <td style={{padding:"12px",color:"rgba(255,255,255,0.35)",fontSize:12}}>{t.time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* ── RISK ── */}
          {active==="risk" && (
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
              {[
                {label:"Daily Loss Limit",used:1.2,max:6,color:"#10b981"},
                {label:"Max Drawdown",used:3.8,max:15,color:"#fbbf24"},
                {label:"Position Concentration",used:28,max:30,color:"#ef4444"},
                {label:"Leverage Used",used:1.5,max:3,color:"#0ea5e9"},
              ].map(r=>(
                <div key={r.label} style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16,padding:"24px"}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:12}}>
                    <p style={{fontWeight:600,fontSize:14}}>{r.label}</p>
                    <p style={{fontFamily:"monospace",fontSize:14,color:r.color}}>{r.used}/{r.max}{r.label.includes("Leverage")?"x":"%"}</p>
                  </div>
                  <div style={{height:8,background:"rgba(255,255,255,0.08)",borderRadius:4,overflow:"hidden"}}>
                    <div style={{height:"100%",width:`${(r.used/r.max)*100}%`,background:r.color,borderRadius:4,transition:"width .5s"}}/>
                  </div>
                  <p style={{marginTop:8,fontSize:11,color:"rgba(255,255,255,0.35)"}}>
                    {((r.used/r.max)*100).toFixed(0)}% of limit used
                  </p>
                </div>
              ))}
              <div style={{gridColumn:"1/-1",background:"rgba(16,185,129,0.08)",border:"1px solid rgba(16,185,129,0.2)",borderRadius:16,padding:"20px 24px",display:"flex",alignItems:"center",gap:12}}>
                <CheckCircle size={20} style={{color:"#10b981",flexShrink:0}}/>
                <div>
                  <p style={{fontWeight:600,color:"#10b981",marginBottom:2}}>All risk parameters within limits</p>
                  <p style={{fontSize:12,color:"rgba(255,255,255,0.45)"}}>Risk Guardian is monitoring all positions in real-time. Last check: 12 seconds ago.</p>
                </div>
              </div>
            </div>
          )}

          {/* ── SETTINGS ── */}
          {active==="settings" && (
            <div style={{maxWidth:600,display:"flex",flexDirection:"column",gap:16}}>
              {[
                {label:"Risk per Trade",desc:"Maximum loss allowed per single trade",val:"2%"},
                {label:"Daily Loss Limit",desc:"Stop trading when daily loss hits this",val:"6%"},
                {label:"Max Leverage",desc:"Maximum leverage across all positions",val:"3x"},
                {label:"Telegram Alerts",desc:"Receive signals and notifications",val:"Enabled"},
                {label:"Auto Execute",desc:"Automatically execute approved signals",val:"Disabled"},
              ].map(s=>(
                <div key={s.label} style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:14,padding:"20px 24px",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <div>
                    <p style={{fontWeight:600,fontSize:14,marginBottom:2}}>{s.label}</p>
                    <p style={{fontSize:12,color:"rgba(255,255,255,0.4)"}}>{s.desc}</p>
                  </div>
                  <div style={{padding:"6px 16px",background:"rgba(14,165,233,0.1)",border:"1px solid rgba(14,165,233,0.2)",borderRadius:8,color:"#0ea5e9",fontFamily:"monospace",fontSize:13,fontWeight:600}}>
                    {s.val}
                  </div>
                </div>
              ))}
              <button style={{padding:"14px",borderRadius:12,background:"linear-gradient(135deg,#0ea5e9,#10b981)",border:"none",color:"#020c07",fontWeight:700,fontSize:14,cursor:"pointer",marginTop:8}}>
                Save Changes
              </button>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
