"use client";
import { canAutoExecute as tierCanAutoExecute } from "@/lib/tiers";
import { useState, useEffect } from "react";
import { Lock, Zap, TrendingUp, AlertCircle, CheckCircle, Clock, DollarSign, Settings2 } from "lucide-react";

// ─── Tier config ──────────────────────────────────────────────────
const TIER = "elite"; // في الإنتاج يأتي من JWT
const canAutoExecute = tierCanAutoExecute(TIER as any);

// ─── Types ────────────────────────────────────────────────────────
type OppStatus = "live" | "fading" | "expired" | "taken";

interface Opportunity {
  id: string;
  symbol: string;
  type: string;
  detail: string;
  conf: number;
  potential: string;
  entry: string;
  sl: string;
  tp: string;
  rr: string;
  totalSeconds: number;   // مدة الفرصة الكاملة
  remainingSeconds: number;
  status: OppStatus;
  autoTaken?: boolean;
}

// ─── Mock Opportunities ───────────────────────────────────────────
const INITIAL_OPPS: Opportunity[] = [
  { id:"o1", symbol:"INJ/USDT",  type:"Volume Spike",        detail:"3.2x avg volume — breaking resistance at $34.2", conf:91, potential:"+18%", entry:"$34.20", sl:"$32.80", tp:"$40.50", rr:"4.5", totalSeconds:1800, remainingSeconds:1247, status:"live"    },
  { id:"o2", symbol:"WLD/USDT",  type:"Pattern Forming",     detail:"Bull flag on 4H — measured target $4.80",        conf:84, potential:"+22%", entry:"$3.92",  sl:"$3.71",  tp:"$4.80",  rr:"4.1", totalSeconds:3600, remainingSeconds:2180, status:"live"    },
  { id:"o3", symbol:"TIA/USDT",  type:"Whale Accumulation",  detail:"$4.2M bought in 2h — supply wall thinning",      conf:88, potential:"+15%", entry:"$8.14",  sl:"$7.80",  tp:"$9.36",  rr:"3.6", totalSeconds:900,  remainingSeconds:142,  status:"fading"  },
  { id:"o4", symbol:"PYTH/USDT", type:"News Catalyst",       detail:"Major partnership — momentum expected",           conf:76, potential:"+31%", entry:"$0.482", sl:"$0.455", tp:"$0.632", rr:"5.5", totalSeconds:1200, remainingSeconds:0,    status:"expired" },
  { id:"o5", symbol:"JTO/USDT",  type:"Support Bounce",      detail:"Strong demand zone — 3 consecutive rejections",  conf:82, potential:"+12%", entry:"$3.21",  sl:"$3.05",  tp:"$3.60",  rr:"2.4", totalSeconds:2400, remainingSeconds:1890, status:"live"    },
];

// ─── Helpers ──────────────────────────────────────────────────────
function formatTime(seconds: number): string {
  if (seconds <= 0) return "00:00";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
}

function getStatusStyle(status: OppStatus) {
  if (status === "live")    return { bg:"rgba(16,185,129,0.12)",  border:"rgba(16,185,129,0.3)",  dot:"#10b981", label:"Live",    labelColor:"#10b981" };
  if (status === "fading")  return { bg:"rgba(251,191,36,0.10)",  border:"rgba(251,191,36,0.3)",  dot:"#fbbf24", label:"Fading",  labelColor:"#fbbf24" };
  if (status === "expired") return { bg:"rgba(239,68,68,0.08)",   border:"rgba(239,68,68,0.2)",   dot:"#ef4444", label:"Expired", labelColor:"#ef4444" };
  return                           { bg:"rgba(14,165,233,0.08)",  border:"rgba(14,165,233,0.2)",  dot:"#0ea5e9", label:"Taken",   labelColor:"#0ea5e9" };
}

function getConfColor(conf: number) {
  if (conf >= 85) return "#10b981";
  if (conf >= 70) return "#fbbf24";
  return "#ef4444";
}

// ─── Opportunity Card ─────────────────────────────────────────────
function OppCard({ opp, budget, onTake, onAnalyze }: {
  opp: Opportunity;
  budget: number;
  onTake: (id:string) => void;
  onAnalyze: (id:string) => void;
}) {
  const [remaining, setRemaining] = useState(opp.remainingSeconds);
  const st = getStatusStyle(opp.status);
  const pct = opp.totalSeconds > 0 ? (remaining / opp.totalSeconds) * 100 : 0;

  useEffect(() => {
    if (opp.status === "expired" || opp.status === "taken") return;
    const t = setInterval(() => {
      setRemaining(r => Math.max(0, r - 1));
    }, 1000);
    return () => clearInterval(t);
  }, [opp.status]);

  const isDead = opp.status === "expired" || opp.status === "taken";
  const progressColor = pct > 50 ? "#10b981" : pct > 20 ? "#fbbf24" : "#ef4444";

  return (
    <div style={{
      background: isDead ? "rgba(255,255,255,0.02)" : st.bg,
      border: `1px solid ${st.border}`,
      borderRadius: 16,
      padding: "20px 24px",
      opacity: isDead ? 0.6 : 1,
      transition: "all .3s",
    }}>
      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"start", marginBottom:14 }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <span style={{ fontSize:17, fontWeight:700 }}>{opp.symbol}</span>
          <span style={{ padding:"3px 10px", borderRadius:20, fontSize:11, fontWeight:600, background:"rgba(255,255,255,0.07)", color:"rgba(255,255,255,0.6)" }}>{opp.type}</span>
          {opp.autoTaken && (
            <span style={{ padding:"3px 8px", borderRadius:20, fontSize:10, background:"rgba(14,165,233,0.15)", color:"#0ea5e9", fontWeight:600, display:"flex", alignItems:"center", gap:3 }}>
              <Zap size={9}/> Auto-executed
            </span>
          )}
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          {/* Status badge */}
          <div style={{ display:"flex", alignItems:"center", gap:5, padding:"4px 10px", borderRadius:20, background:"rgba(0,0,0,0.2)", border:`1px solid ${st.border}` }}>
            <span style={{ width:6, height:6, borderRadius:"50%", background:st.dot, boxShadow: !isDead ? `0 0 6px ${st.dot}` : "none" }}/>
            <span style={{ fontSize:11, fontWeight:700, color:st.labelColor }}>{st.label}</span>
          </div>
          {/* Potential */}
          <div style={{ textAlign:"right" }}>
            <p style={{ fontSize:14, fontWeight:700, color:"#10b981" }}>{opp.potential}</p>
            <p style={{ fontSize:10, color:"rgba(255,255,255,0.3)" }}>potential</p>
          </div>
        </div>
      </div>

      {/* Detail */}
      <p style={{ fontSize:13, color:"rgba(255,255,255,0.55)", marginBottom:14 }}>{opp.detail}</p>

      {/* Countdown + progress */}
      {!isDead && (
        <div style={{ marginBottom:14 }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:6 }}>
            <div style={{ display:"flex", alignItems:"center", gap:6 }}>
              <Clock size={12} style={{ color:"rgba(255,255,255,0.4)" }}/>
              <span style={{ fontSize:11, color:"rgba(255,255,255,0.4)" }}>Expires in</span>
            </div>
            <span style={{ fontSize:13, fontWeight:700, fontFamily:"monospace", color: pct > 50 ? "#10b981" : pct > 20 ? "#fbbf24" : "#ef4444" }}>
              {formatTime(remaining)}
            </span>
          </div>
          <div style={{ height:5, background:"rgba(255,255,255,0.07)", borderRadius:3, overflow:"hidden" }}>
            <div style={{ height:"100%", width:`${pct}%`, background:progressColor, borderRadius:3, transition:"width 1s linear" }}/>
          </div>
        </div>
      )}

      {/* Metrics */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:8, marginBottom:16 }}>
        {([["Entry",opp.entry,"#f1f5f9"],["Stop Loss",opp.sl,"#ef4444"],["Take Profit",opp.tp,"#10b981"],["Confidence",opp.conf+"%",getConfColor(opp.conf)],["R:R",opp.rr+"x","#0ea5e9"]] as [string,string,string][]).map(([l,v,c])=>(
          <div key={l} style={{ background:"rgba(255,255,255,0.04)", borderRadius:9, padding:"9px 10px" }}>
            <p style={{ fontSize:9, color:"rgba(255,255,255,0.35)", marginBottom:3, textTransform:"uppercase", letterSpacing:".05em" }}>{l}</p>
            <p style={{ fontSize:12, fontWeight:700, fontFamily:"monospace", color:c }}>{v}</p>
          </div>
        ))}
      </div>

      {/* Conf bar */}
      <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:14 }}>
        <span style={{ fontSize:10, color:"rgba(255,255,255,0.35)", flexShrink:0 }}>AI Confidence</span>
        <div style={{ flex:1, height:5, background:"rgba(255,255,255,0.07)", borderRadius:3, overflow:"hidden" }}>
          <div style={{ height:"100%", width:`${opp.conf}%`, background:getConfColor(opp.conf), borderRadius:3 }}/>
        </div>
        <span style={{ fontSize:11, fontWeight:700, color:getConfColor(opp.conf), flexShrink:0 }}>{opp.conf}%</span>
      </div>

      {/* Auto budget info */}
      {canAutoExecute && !isDead && budget > 0 && (
        <div style={{ display:"flex", alignItems:"center", gap:6, padding:"8px 12px", background:"rgba(14,165,233,0.08)", border:"1px solid rgba(14,165,233,0.15)", borderRadius:8, marginBottom:12 }}>
          <Zap size={12} style={{ color:"#0ea5e9", flexShrink:0 }}/>
          <span style={{ fontSize:11, color:"rgba(255,255,255,0.5)" }}>Auto-execute budget: </span>
          <span style={{ fontSize:11, fontWeight:700, color:"#0ea5e9" }}>${budget} allocated</span>
        </div>
      )}

      {/* Actions */}
      {!isDead && (
        <div style={{ display:"flex", gap:8 }}>
          <button onClick={()=>onTake(opp.id)} style={{ flex:1, padding:"9px", borderRadius:10, background:"linear-gradient(135deg,#fbbf24,#f59e0b)", border:"none", color:"#1c0a00", fontWeight:700, fontSize:13, cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", gap:6 }}>
            <TrendingUp size={14}/> Execute Now
          </button>
          <button onClick={()=>onAnalyze(opp.id)} style={{ padding:"9px 18px", borderRadius:10, background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", color:"rgba(255,255,255,0.6)", fontSize:13, cursor:"pointer" }}>
            Full Analysis
          </button>
        </div>
      )}
      {opp.status === "taken" && (
        <div style={{ display:"flex", alignItems:"center", gap:8, padding:"9px 14px", background:"rgba(14,165,233,0.08)", border:"1px solid rgba(14,165,233,0.2)", borderRadius:10 }}>
          <CheckCircle size={15} style={{ color:"#0ea5e9" }}/><span style={{ fontSize:13, color:"#0ea5e9", fontWeight:600 }}>Trade executed successfully</span>
        </div>
      )}
      {opp.status === "expired" && (
        <div style={{ display:"flex", alignItems:"center", gap:8, padding:"9px 14px", background:"rgba(239,68,68,0.06)", border:"1px solid rgba(239,68,68,0.15)", borderRadius:10 }}>
          <AlertCircle size={15} style={{ color:"#ef4444" }}/><span style={{ fontSize:13, color:"rgba(255,255,255,0.4)" }}>Opportunity expired — entry window closed</span>
        </div>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────
export default function OpportunityHunter() {
  const [opps, setOpps] = useState<Opportunity[]>(INITIAL_OPPS);
  const [budget, setBudget] = useState(500);
  const [inputBudget, setInputBudget] = useState("500");
  const [autoEnabled, setAutoEnabled] = useState(false);
  const [showBudgetPanel, setShowBudgetPanel] = useState(false);
  const [budgetError, setBudgetError] = useState("");

  // تحديث حالة الفرص (fading عند < 20%)
  useEffect(() => {
    const interval = setInterval(() => {
      setOpps(prev => prev.map(o => {
        if (o.status === "expired" || o.status === "taken") return o;
        const pct = (o.remainingSeconds / o.totalSeconds) * 100;
        const newStatus: OppStatus = pct <= 0 ? "expired" : pct <= 20 ? "fading" : "live";
        return { ...o, remainingSeconds: Math.max(0, o.remainingSeconds - 1), status: newStatus };
      }));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleTake = (id: string) => {
    setOpps(prev => prev.map(o => o.id === id ? { ...o, status:"taken" as OppStatus } : o));
  };

  const handleAnalyze = (id: string) => {
    // في الإنتاج: يفتح modal تحليل مفصل من AI
    alert("Full AI analysis — coming soon");
  };

  const handleSaveBudget = () => {
    const val = parseFloat(inputBudget);
    if (isNaN(val) || val < 50) { setBudgetError("Minimum budget is $50"); return; }
    if (val > 100000) { setBudgetError("Maximum budget is $100,000"); return; }
    setBudget(val);
    setBudgetError("");
    setShowBudgetPanel(false);
  };

  const live    = opps.filter(o=>o.status==="live").length;
  const fading  = opps.filter(o=>o.status==="fading").length;
  const expired = opps.filter(o=>o.status==="expired").length;

  return (
    <div>
      {/* Header stats */}
      <div style={{ display:"grid", gridTemplateColumns: canAutoExecute ? "1fr 1fr 1fr 1fr" : "1fr 1fr 1fr", gap:12, marginBottom:20 }}>
        <div style={{ background:"rgba(16,185,129,0.1)", border:"1px solid rgba(16,185,129,0.25)", borderRadius:12, padding:"14px 18px", display:"flex", alignItems:"center", gap:10 }}>
          <span style={{ width:8, height:8, borderRadius:"50%", background:"#10b981", boxShadow:"0 0 8px #10b981", flexShrink:0 }}/>
          <div><p style={{ fontSize:11, color:"rgba(255,255,255,0.4)", marginBottom:2 }}>Live</p><p style={{ fontSize:20, fontWeight:700, color:"#10b981", fontFamily:"monospace" }}>{live}</p></div>
        </div>
        <div style={{ background:"rgba(251,191,36,0.1)", border:"1px solid rgba(251,191,36,0.25)", borderRadius:12, padding:"14px 18px", display:"flex", alignItems:"center", gap:10 }}>
          <span style={{ width:8, height:8, borderRadius:"50%", background:"#fbbf24", flexShrink:0 }}/>
          <div><p style={{ fontSize:11, color:"rgba(255,255,255,0.4)", marginBottom:2 }}>Fading</p><p style={{ fontSize:20, fontWeight:700, color:"#fbbf24", fontFamily:"monospace" }}>{fading}</p></div>
        </div>
        <div style={{ background:"rgba(239,68,68,0.08)", border:"1px solid rgba(239,68,68,0.2)", borderRadius:12, padding:"14px 18px", display:"flex", alignItems:"center", gap:10 }}>
          <span style={{ width:8, height:8, borderRadius:"50%", background:"#ef4444", flexShrink:0 }}/>
          <div><p style={{ fontSize:11, color:"rgba(255,255,255,0.4)", marginBottom:2 }}>Expired</p><p style={{ fontSize:20, fontWeight:700, color:"rgba(255,255,255,0.4)", fontFamily:"monospace" }}>{expired}</p></div>
        </div>

        {/* Auto-Execute Budget — فقط للباقات $199+ */}
        {canAutoExecute && (
          <div
            onClick={()=>setShowBudgetPanel(!showBudgetPanel)}
            style={{ background: autoEnabled?"rgba(14,165,233,0.12)":"rgba(255,255,255,0.04)", border:`1px solid ${autoEnabled?"rgba(14,165,233,0.3)":"rgba(255,255,255,0.1)"}`, borderRadius:12, padding:"14px 18px", cursor:"pointer", transition:"all .2s" }}
          >
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:4 }}>
              <p style={{ fontSize:11, color:"rgba(255,255,255,0.4)" }}>Auto-Execute Budget</p>
              <div
                onClick={e=>{e.stopPropagation();setAutoEnabled(!autoEnabled)}}
                style={{ width:36, height:20, borderRadius:10, background:autoEnabled?"#0ea5e9":"rgba(255,255,255,0.15)", position:"relative", cursor:"pointer", transition:"background .2s" }}
              >
                <div style={{ width:16, height:16, borderRadius:"50%", background:"white", position:"absolute", top:2, left:autoEnabled?18:2, transition:"left .2s" }}/>
              </div>
            </div>
            <p style={{ fontSize:18, fontWeight:700, fontFamily:"monospace", color:autoEnabled?"#0ea5e9":"rgba(255,255,255,0.5)" }}>${budget.toLocaleString()}</p>
            <p style={{ fontSize:10, color:"rgba(255,255,255,0.3)", marginTop:2 }}>{autoEnabled?"Active — AI will auto-trade":"Tap to configure"}</p>
          </div>
        )}
      </div>

      {/* Budget Panel */}
      {canAutoExecute && showBudgetPanel && (
        <div style={{ background:"#0d1526", border:"1px solid rgba(14,165,233,0.2)", borderRadius:16, padding:"22px", marginBottom:20 }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
            <div>
              <h3 style={{ fontWeight:600, fontSize:15, marginBottom:4, display:"flex", alignItems:"center", gap:8 }}>
                <Settings2 size={16} style={{ color:"#0ea5e9" }}/> Auto-Execute Configuration
              </h3>
              <p style={{ fontSize:12, color:"rgba(255,255,255,0.4)" }}>AI will automatically enter trades on your behalf within this budget</p>
            </div>
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:14, marginBottom:16 }}>
            <div>
              <label style={{ fontSize:11, color:"rgba(255,255,255,0.4)", display:"block", marginBottom:6 }}>Total Budget (USDT)</label>
              <div style={{ display:"flex", alignItems:"center", gap:8, background:"rgba(255,255,255,0.05)", border:`1px solid ${budgetError?"rgba(239,68,68,0.4)":"rgba(255,255,255,0.1)"}`, borderRadius:10, padding:"0 12px" }}>
                <DollarSign size={14} style={{ color:"rgba(255,255,255,0.35)", flexShrink:0 }}/>
                <input
                  value={inputBudget}
                  onChange={e=>{ setInputBudget(e.target.value); setBudgetError(""); }}
                  type="number" min="50" max="100000"
                  style={{ background:"transparent", border:"none", outline:"none", color:"#f1f5f9", fontSize:14, fontFamily:"monospace", fontWeight:600, padding:"11px 0", width:"100%" }}
                />
              </div>
              {budgetError && <p style={{ fontSize:11, color:"#ef4444", marginTop:4 }}>{budgetError}</p>}
            </div>
            <div>
              <label style={{ fontSize:11, color:"rgba(255,255,255,0.4)", display:"block", marginBottom:6 }}>Min Confidence to Auto-Trade</label>
              <div style={{ display:"flex", alignItems:"center", gap:8, background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"11px 14px" }}>
                <span style={{ fontSize:14, fontFamily:"monospace", fontWeight:600, color:"#10b981" }}>80%</span>
                <span style={{ fontSize:11, color:"rgba(255,255,255,0.35)" }}>and above</span>
              </div>
            </div>
            <div>
              <label style={{ fontSize:11, color:"rgba(255,255,255,0.4)", display:"block", marginBottom:6 }}>Max per Trade</label>
              <div style={{ display:"flex", alignItems:"center", gap:8, background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"11px 14px" }}>
                <span style={{ fontSize:14, fontFamily:"monospace", fontWeight:600 }}>20%</span>
                <span style={{ fontSize:11, color:"rgba(255,255,255,0.35)" }}>of budget</span>
              </div>
            </div>
          </div>
          <div style={{ background:"rgba(14,165,233,0.06)", border:"1px solid rgba(14,165,233,0.15)", borderRadius:10, padding:"12px 16px", marginBottom:16, display:"flex", gap:10 }}>
            <AlertCircle size={14} style={{ color:"#0ea5e9", flexShrink:0, marginTop:1 }}/>
            <p style={{ fontSize:12, color:"rgba(255,255,255,0.5)", lineHeight:1.6 }}>
              AI will only auto-execute on opportunities with confidence ≥80% and R:R ≥2.0. Each trade uses max 20% of your budget. You can pause auto-execute at any time.
            </p>
          </div>
          <div style={{ display:"flex", gap:10 }}>
            <button onClick={handleSaveBudget} style={{ flex:1, padding:"11px", borderRadius:10, background:"linear-gradient(135deg,#0ea5e9,#10b981)", border:"none", color:"#020c07", fontWeight:700, fontSize:13, cursor:"pointer" }}>
              Save & Activate
            </button>
            <button onClick={()=>setShowBudgetPanel(false)} style={{ padding:"11px 20px", borderRadius:10, background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", color:"rgba(255,255,255,0.5)", fontSize:13, cursor:"pointer" }}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Locked for lower tiers */}
      {!canAutoExecute && (
        <div style={{ background:"rgba(251,191,36,0.06)", border:"1px solid rgba(251,191,36,0.2)", borderRadius:12, padding:"14px 18px", marginBottom:20, display:"flex", alignItems:"center", gap:10 }}>
          <Lock size={14} style={{ color:"#fbbf24", flexShrink:0 }}/>
          <p style={{ fontSize:12, color:"rgba(255,255,255,0.5)" }}>
            Auto-Execute is available from <strong style={{ color:"#fbbf24" }}>Elite ($199/mo)</strong> and above.{" "}
            <a href="/checkout?tier=elite" style={{ color:"#fbbf24", textDecoration:"underline" }}>Upgrade now</a>
          </p>
        </div>
      )}

      {/* Opportunities */}
      <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
        {opps.map(o => (
          <OppCard key={o.id} opp={o} budget={autoEnabled ? budget : 0} onTake={handleTake} onAnalyze={handleAnalyze}/>
        ))}
      </div>
    </div>
  );
}
