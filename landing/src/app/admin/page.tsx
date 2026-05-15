"use client";

import { useState } from "react";
import {
  Users, DollarSign, TrendingUp, Zap, Shield, Settings,
  BarChart3, Bell, LogOut, Menu, X, Search, Filter,
  ArrowUpRight, ArrowDownRight, CheckCircle, AlertCircle,
  XCircle, ChevronDown, Download, RefreshCw
} from "lucide-react";

// ─── Mock Data ────────────────────────────────────────────────────────────────
const STATS = [
  { label:"Total Revenue",    value:"$48,291",  change:"+12.4%", up:true,  icon:DollarSign  },
  { label:"Active Users",     value:"312",      change:"+8.1%",  up:true,  icon:Users       },
  { label:"MRR",              value:"$31,450",  change:"+6.8%",  up:true,  icon:TrendingUp  },
  { label:"Signals Today",    value:"1,842",    change:"-2.1%",  up:false, icon:Zap         },
  { label:"Churn Rate",       value:"2.3%",     change:"-0.4%",  up:true,  icon:ArrowUpRight},
  { label:"AI Cost Today",    value:"$124",     change:"+5.2%",  up:false, icon:BarChart3   },
];

const USERS = [
  { id:"#1001", name:"Ahmed Al-Rashidi", email:"ahmed@example.com", plan:"Pro",          status:"active",    joined:"May 12",  mrr:99,   trades:47  },
  { id:"#1002", name:"Sara Al-Mutairi",  email:"sara@example.com",  plan:"Elite",        status:"active",    joined:"May 10",  mrr:199,  trades:82  },
  { id:"#1003", name:"Khalid Hassan",    email:"khalid@example.com",plan:"Whale",        status:"active",    joined:"May 8",   mrr:499,  trades:134 },
  { id:"#1004", name:"Fatima Al-Azmi",   email:"fatima@example.com",plan:"Starter",      status:"active",    joined:"May 5",   mrr:59,   trades:21  },
  { id:"#1005", name:"Omar Nasser",      email:"omar@example.com",  plan:"Micro",        status:"suspended", joined:"Apr 29",  mrr:0,    trades:8   },
  { id:"#1006", name:"Nora Al-Sabah",    email:"nora@example.com",  plan:"Institutional",status:"active",    joined:"Apr 20",  mrr:1499, trades:289 },
  { id:"#1007", name:"Yusuf Ibrahim",    email:"yusuf@example.com", plan:"Pro",          status:"trial",     joined:"May 15",  mrr:0,    trades:3   },
  { id:"#1008", name:"Layla Al-Amin",    email:"layla@example.com", plan:"Elite",        status:"active",    joined:"Apr 15",  mrr:199,  trades:61  },
];

const REVENUE_DATA = [
  {month:"Nov",val:18200},{month:"Dec",val:22400},{month:"Jan",val:25100},
  {month:"Feb",val:27800},{month:"Mar",val:29400},{month:"Apr",val:31450},
];

const PLAN_DIST = [
  {plan:"Micro",    count:48,  color:"#6ee7b7"},
  {plan:"Starter",  count:67,  color:"#34d399"},
  {plan:"Pro",      count:112, color:"#10b981"},
  {plan:"Elite",    count:54,  color:"#059669"},
  {plan:"Whale",    count:21,  color:"#0ea5e9"},
  {plan:"Institutional",count:7,color:"#6366f1"},
  {plan:"Founder",  count:3,   color:"#fbbf24"},
];

const ALERTS = [
  {type:"warning", msg:"User #1005 payment failed — 3rd attempt", time:"5 min ago"},
  {type:"info",    msg:"12 new waitlist signups in the last hour",  time:"1h ago"},
  {type:"error",   msg:"API rate limit approaching on Bybit",       time:"2h ago"},
  {type:"success", msg:"Deployment v2.1.4 successful",             time:"3h ago"},
];

const NAV = [
  {id:"overview",  label:"Overview",   icon:BarChart3},
  {id:"users",     label:"Users",      icon:Users},
  {id:"revenue",   label:"Revenue",    icon:DollarSign},
  {id:"system",    label:"System",     icon:Shield},
  {id:"settings",  label:"Settings",   icon:Settings},
];

const PLAN_COLORS: Record<string,string> = {
  Trial:"rgba(255,255,255,0.15)", Micro:"rgba(110,231,183,0.2)", Starter:"rgba(52,211,153,0.2)",
  Pro:"rgba(16,185,129,0.2)", Elite:"rgba(14,165,233,0.2)", Whale:"rgba(99,102,241,0.2)",
  Institutional:"rgba(139,92,246,0.2)", Founder:"rgba(251,191,36,0.2)"
};
const PLAN_TEXT: Record<string,string> = {
  Trial:"rgba(255,255,255,0.5)", Micro:"#6ee7b7", Starter:"#34d399",
  Pro:"#10b981", Elite:"#0ea5e9", Whale:"#818cf8",
  Institutional:"#a78bfa", Founder:"#fbbf24"
};

export default function AdminPage() {
  const [active, setActive]   = useState("overview");
  const [sideOpen, setSideOpen] = useState(true);
  const [search, setSearch]   = useState("");
  const maxRev = Math.max(...REVENUE_DATA.map(d=>d.val));
  const maxPlan = Math.max(...PLAN_DIST.map(d=>d.count));

  const filteredUsers = USERS.filter(u =>
    u.name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase()) ||
    u.plan.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{background:"#050810",minHeight:"100vh",color:"#f1f5f9",fontFamily:"'Inter',system-ui,sans-serif",display:"flex"}}>

      {/* ─── SIDEBAR ──────────────────────────────────────────────── */}
      <aside style={{
        width: sideOpen ? 220 : 64,
        background:"#080d1a",
        borderRight:"1px solid rgba(255,255,255,0.06)",
        display:"flex",flexDirection:"column",
        transition:"width .25s ease",
        flexShrink:0, position:"relative", zIndex:20
      }}>
        <div style={{padding:"20px 16px",borderBottom:"1px solid rgba(255,255,255,0.06)",display:"flex",alignItems:"center",gap:12}}>
          <svg width="32" height="32" viewBox="0 0 100 100" style={{flexShrink:0}}>
            <defs>
              <linearGradient id="al" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#0ea5e9"/>
                <stop offset="100%" stopColor="#10b981"/>
              </linearGradient>
            </defs>
            <polygon points="50,6 96,90 4,90" fill="rgba(14,165,233,0.1)" stroke="url(#al)" strokeWidth="3.5" strokeLinejoin="round"/>
            <circle cx="50" cy="52" r="10" fill="none" stroke="url(#al)" strokeWidth="2"/>
            <circle cx="50" cy="52" r="3.5" fill="url(#al)"/>
            <line x1="50" y1="30" x2="50" y2="42" stroke="url(#al)" strokeWidth="1.8" strokeLinecap="round"/>
            <line x1="42" y1="60" x2="26" y2="76" stroke="url(#al)" strokeWidth="1.8" strokeLinecap="round"/>
            <line x1="58" y1="60" x2="74" y2="76" stroke="url(#al)" strokeWidth="1.8" strokeLinecap="round"/>
            <circle cx="50" cy="27" r="3" fill="#10b981"/>
            <circle cx="24" cy="78" r="3" fill="#0ea5e9"/>
            <circle cx="76" cy="78" r="3" fill="#0ea5e9"/>
          </svg>
          {sideOpen && (
            <div>
              <div style={{fontWeight:700,fontSize:15,background:"linear-gradient(135deg,#0ea5e9,#10b981)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>TradoAI</div>
              <div style={{fontSize:10,color:"rgba(255,255,255,0.35)",marginTop:1}}>Admin Panel</div>
            </div>
          )}
        </div>

        <button onClick={()=>setSideOpen(!sideOpen)} style={{position:"absolute",top:22,right:-12,width:24,height:24,background:"#0d1526",border:"1px solid rgba(255,255,255,0.1)",borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",cursor:"pointer",color:"rgba(255,255,255,0.5)"}}>
          {sideOpen?<X size={12}/>:<Menu size={12}/>}
        </button>

        <nav style={{flex:1,padding:"12px 0"}}>
          {NAV.map(n=>(
            <button key={n.id} onClick={()=>setActive(n.id)} style={{
              width:"100%",display:"flex",alignItems:"center",gap:12,
              padding:"11px 16px",border:"none",
              background:active===n.id?"rgba(14,165,233,0.1)":"transparent",
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

        <div style={{padding:"16px",borderTop:"1px solid rgba(255,255,255,0.06)"}}>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:12,padding:"8px 0"}}>
            <div style={{width:28,height:28,borderRadius:"50%",background:"linear-gradient(135deg,#0ea5e9,#10b981)",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0,fontSize:11,fontWeight:700,color:"#020c07"}}>A</div>
            {sideOpen && <div><p style={{fontSize:12,fontWeight:600}}>Admin</p><p style={{fontSize:10,color:"rgba(255,255,255,0.35)"}}>jaraa7.js@gmail.com</p></div>}
          </div>
          <button style={{width:"100%",display:"flex",alignItems:"center",gap:12,background:"transparent",border:"none",color:"rgba(255,255,255,0.35)",cursor:"pointer",padding:"6px 0"}}>
            <LogOut size={15} style={{flexShrink:0}}/>
            {sideOpen && <span style={{fontSize:12}}>Sign out</span>}
          </button>
        </div>
      </aside>

      {/* ─── MAIN ─────────────────────────────────────────────────── */}
      <main style={{flex:1,overflow:"auto"}}>

        {/* Header */}
        <div style={{padding:"20px 32px",borderBottom:"1px solid rgba(255,255,255,0.06)",display:"flex",alignItems:"center",justifyContent:"space-between",background:"rgba(8,13,26,0.9)",backdropFilter:"blur(20px)",position:"sticky",top:0,zIndex:10}}>
          <div>
            <h1 style={{fontSize:18,fontWeight:700}}>
              {NAV.find(n=>n.id===active)?.label}
            </h1>
            <p style={{fontSize:11,color:"rgba(255,255,255,0.35)",marginTop:2}}>
              {new Date().toLocaleDateString("en-US",{weekday:"long",year:"numeric",month:"long",day:"numeric"})}
            </p>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:12}}>
            <button style={{display:"flex",alignItems:"center",gap:6,padding:"8px 14px",background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.1)",borderRadius:10,color:"rgba(255,255,255,0.6)",fontSize:12,cursor:"pointer"}}>
              <Download size={14}/> Export
            </button>
            <button style={{display:"flex",alignItems:"center",gap:6,padding:"8px 14px",background:"rgba(14,165,233,0.1)",border:"1px solid rgba(14,165,233,0.2)",borderRadius:10,color:"#0ea5e9",fontSize:12,cursor:"pointer"}}>
              <RefreshCw size={14}/> Refresh
            </button>
            <div style={{position:"relative"}}>
              <button style={{padding:"8px",background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:8,color:"rgba(255,255,255,0.6)",cursor:"pointer"}}>
                <Bell size={16}/>
              </button>
              <span style={{position:"absolute",top:4,right:4,width:7,height:7,background:"#ef4444",borderRadius:"50%",border:"1px solid #050810"}}/>
            </div>
          </div>
        </div>

        <div style={{padding:"28px 32px"}}>

          {/* ── OVERVIEW ── */}
          {active==="overview" && <>

            {/* Stats grid */}
            <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:16,marginBottom:28}}>
              {STATS.map(s=>(
                <div key={s.label} style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:14,padding:"20px 24px",display:"flex",justifyContent:"space-between",alignItems:"start"}}>
                  <div>
                    <p style={{fontSize:11,color:"rgba(255,255,255,0.4)",marginBottom:8,textTransform:"uppercase",letterSpacing:".06em"}}>{s.label}</p>
                    <p style={{fontSize:24,fontWeight:700,fontFamily:"monospace",marginBottom:6}}>{s.value}</p>
                    <div style={{display:"flex",alignItems:"center",gap:4,fontSize:11,color:s.up?"#10b981":"#ef4444"}}>
                      {s.up?<ArrowUpRight size={13}/>:<ArrowDownRight size={13}/>}
                      {s.change} vs last month
                    </div>
                  </div>
                  <div style={{width:40,height:40,borderRadius:10,background:"rgba(14,165,233,0.1)",display:"flex",alignItems:"center",justifyContent:"center",color:"#0ea5e9"}}>
                    <s.icon size={18}/>
                  </div>
                </div>
              ))}
            </div>

            <div style={{display:"grid",gridTemplateColumns:"2fr 1fr",gap:20,marginBottom:20}}>

              {/* Revenue chart */}
              <div style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16,padding:"24px"}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:24}}>
                  <h3 style={{fontWeight:600,fontSize:14}}>Monthly Revenue (MRR)</h3>
                  <span style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>Last 6 months</span>
                </div>
                <div style={{display:"flex",alignItems:"end",gap:12,height:140}}>
                  {REVENUE_DATA.map(d=>(
                    <div key={d.month} style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",gap:6}}>
                      <span style={{fontSize:10,color:"rgba(255,255,255,0.4)",fontFamily:"monospace"}}>${(d.val/1000).toFixed(1)}k</span>
                      <div style={{width:"100%",background:"linear-gradient(180deg,#0ea5e9,#10b981)",borderRadius:"6px 6px 0 0",height:`${(d.val/maxRev)*110}px`,transition:"height .5s",opacity:.85}}/>
                      <span style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>{d.month}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Plan distribution */}
              <div style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16,padding:"24px"}}>
                <h3 style={{fontWeight:600,fontSize:14,marginBottom:20}}>Plan Distribution</h3>
                <div style={{display:"flex",flexDirection:"column",gap:10}}>
                  {PLAN_DIST.map(p=>(
                    <div key={p.plan} style={{display:"flex",alignItems:"center",gap:10}}>
                      <span style={{fontSize:11,color:"rgba(255,255,255,0.5)",width:80,flexShrink:0}}>{p.plan}</span>
                      <div style={{flex:1,height:6,background:"rgba(255,255,255,0.06)",borderRadius:3,overflow:"hidden"}}>
                        <div style={{height:"100%",width:`${(p.count/maxPlan)*100}%`,background:p.color,borderRadius:3}}/>
                      </div>
                      <span style={{fontSize:11,fontFamily:"monospace",color:"rgba(255,255,255,0.5)",width:24,textAlign:"right"}}>{p.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Alerts */}
            <div style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16,padding:"24px"}}>
              <h3 style={{fontWeight:600,fontSize:14,marginBottom:16}}>System Alerts</h3>
              <div style={{display:"flex",flexDirection:"column",gap:10}}>
                {ALERTS.map((a,i)=>(
                  <div key={i} style={{display:"flex",alignItems:"center",gap:12,padding:"12px 16px",background:"rgba(255,255,255,0.03)",borderRadius:10,border:`1px solid ${a.type==="error"?"rgba(239,68,68,0.2)":a.type==="warning"?"rgba(251,191,36,0.2)":a.type==="success"?"rgba(16,185,129,0.2)":"rgba(14,165,233,0.2)"}`}}>
                    {a.type==="error"&&<XCircle size={16} style={{color:"#ef4444",flexShrink:0}}/>}
                    {a.type==="warning"&&<AlertCircle size={16} style={{color:"#fbbf24",flexShrink:0}}/>}
                    {a.type==="success"&&<CheckCircle size={16} style={{color:"#10b981",flexShrink:0}}/>}
                    {a.type==="info"&&<Bell size={16} style={{color:"#0ea5e9",flexShrink:0}}/>}
                    <span style={{flex:1,fontSize:13}}>{a.msg}</span>
                    <span style={{fontSize:11,color:"rgba(255,255,255,0.3)",flexShrink:0}}>{a.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </>}

          {/* ── USERS ── */}
          {active==="users" && <>
            <div style={{display:"flex",gap:12,marginBottom:20}}>
              <div style={{flex:1,display:"flex",alignItems:"center",gap:10,background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:10,padding:"10px 16px"}}>
                <Search size={15} style={{color:"rgba(255,255,255,0.35)",flexShrink:0}}/>
                <input
                  value={search} onChange={e=>setSearch(e.target.value)}
                  placeholder="Search users..."
                  style={{background:"transparent",border:"none",outline:"none",color:"#f1f5f9",fontSize:13,width:"100%"}}
                />
              </div>
              <button style={{display:"flex",alignItems:"center",gap:8,padding:"10px 16px",background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:10,color:"rgba(255,255,255,0.5)",fontSize:13,cursor:"pointer"}}>
                <Filter size={14}/> Filter
              </button>
            </div>

            <div style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16,overflow:"hidden"}}>
              <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
                <thead>
                  <tr style={{background:"rgba(255,255,255,0.03)",borderBottom:"1px solid rgba(255,255,255,0.06)"}}>
                    {["ID","Name","Plan","Status","MRR","Trades","Joined","Actions"].map(h=>(
                      <th key={h} style={{padding:"12px 16px",textAlign:"left",color:"rgba(255,255,255,0.35)",fontWeight:500,fontSize:11,textTransform:"uppercase",letterSpacing:".06em"}}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((u,i)=>(
                    <tr key={i} style={{borderBottom:"1px solid rgba(255,255,255,0.04)",transition:"background .15s"}} onMouseEnter={e=>(e.currentTarget.style.background="rgba(255,255,255,0.02)")} onMouseLeave={e=>(e.currentTarget.style.background="transparent")}>
                      <td style={{padding:"14px 16px",fontFamily:"monospace",fontSize:11,color:"rgba(255,255,255,0.35)"}}>{u.id}</td>
                      <td style={{padding:"14px 16px"}}>
                        <div style={{fontWeight:600,marginBottom:2}}>{u.name}</div>
                        <div style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>{u.email}</div>
                      </td>
                      <td style={{padding:"14px 16px"}}>
                        <span style={{padding:"4px 10px",borderRadius:20,fontSize:11,fontWeight:600,background:PLAN_COLORS[u.plan]||"rgba(255,255,255,0.1)",color:PLAN_TEXT[u.plan]||"white"}}>{u.plan}</span>
                      </td>
                      <td style={{padding:"14px 16px"}}>
                        <span style={{padding:"4px 10px",borderRadius:20,fontSize:11,fontWeight:600,background:u.status==="active"?"rgba(16,185,129,0.15)":u.status==="trial"?"rgba(14,165,233,0.15)":"rgba(239,68,68,0.15)",color:u.status==="active"?"#10b981":u.status==="trial"?"#0ea5e9":"#ef4444"}}>{u.status}</span>
                      </td>
                      <td style={{padding:"14px 16px",fontFamily:"monospace",fontWeight:600,color:u.mrr>0?"#10b981":"rgba(255,255,255,0.3)"}}>{u.mrr>0?`$${u.mrr}`:"—"}</td>
                      <td style={{padding:"14px 16px",fontFamily:"monospace",color:"rgba(255,255,255,0.6)"}}>{u.trades}</td>
                      <td style={{padding:"14px 16px",color:"rgba(255,255,255,0.35)",fontSize:12}}>{u.joined}</td>
                      <td style={{padding:"14px 16px"}}>
                        <div style={{display:"flex",gap:6}}>
                          <button style={{padding:"5px 10px",borderRadius:6,background:"rgba(14,165,233,0.1)",border:"1px solid rgba(14,165,233,0.2)",color:"#0ea5e9",fontSize:11,cursor:"pointer"}}>View</button>
                          <button style={{padding:"5px 10px",borderRadius:6,background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.1)",color:"rgba(255,255,255,0.5)",fontSize:11,cursor:"pointer"}}>Edit</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{padding:"12px 16px",borderTop:"1px solid rgba(255,255,255,0.05)",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                <span style={{fontSize:12,color:"rgba(255,255,255,0.35)"}}>Showing {filteredUsers.length} of {USERS.length} users</span>
                <div style={{display:"flex",gap:8}}>
                  {["←","1","2","3","→"].map(p=>(
                    <button key={p} style={{width:28,height:28,borderRadius:6,background:p==="1"?"rgba(14,165,233,0.15)":"rgba(255,255,255,0.05)",border:p==="1"?"1px solid rgba(14,165,233,0.3)":"1px solid rgba(255,255,255,0.08)",color:p==="1"?"#0ea5e9":"rgba(255,255,255,0.4)",fontSize:12,cursor:"pointer"}}>{p}</button>
                  ))}
                </div>
              </div>
            </div>
          </>}

          {/* ── REVENUE ── */}
          {active==="revenue" && (
            <div style={{display:"flex",flexDirection:"column",gap:20}}>
              <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:16}}>
                {[{l:"MRR",v:"$31,450",c:"+6.8%"},{l:"ARR",v:"$377,400",c:"+6.8%"},{l:"ARPU",v:"$100.8",c:"+2.1%"}].map(s=>(
                  <div key={s.l} style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:14,padding:"24px"}}>
                    <p style={{fontSize:11,color:"rgba(255,255,255,0.4)",textTransform:"uppercase",letterSpacing:".08em",marginBottom:8}}>{s.l}</p>
                    <p style={{fontSize:28,fontWeight:700,fontFamily:"monospace",marginBottom:4}}>{s.v}</p>
                    <p style={{fontSize:12,color:"#10b981"}}>{s.c} vs last month</p>
                  </div>
                ))}
              </div>
              <div style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:16,padding:"24px"}}>
                <h3 style={{fontWeight:600,fontSize:14,marginBottom:20}}>Revenue by Plan</h3>
                <div style={{display:"flex",flexDirection:"column",gap:12}}>
                  {[
                    {plan:"Institutional",count:7, mrr:10493,pct:33},
                    {plan:"Whale",        count:21,mrr:10479,pct:33},
                    {plan:"Founder",      count:3, mrr:8997, pct:29},
                    {plan:"Elite",        count:54,mrr:10746,pct:34},
                    {plan:"Pro",          count:112,mrr:11088,pct:35},
                    {plan:"Starter",      count:67,mrr:3953, pct:13},
                    {plan:"Micro",        count:48,mrr:1392, pct:4},
                  ].map(r=>(
                    <div key={r.plan} style={{display:"grid",gridTemplateColumns:"120px 80px 1fr 80px",alignItems:"center",gap:12}}>
                      <span style={{fontSize:13,fontWeight:500}}>{r.plan}</span>
                      <span style={{fontSize:12,color:"rgba(255,255,255,0.4)",fontFamily:"monospace"}}>{r.count} users</span>
                      <div style={{height:8,background:"rgba(255,255,255,0.06)",borderRadius:4,overflow:"hidden"}}>
                        <div style={{height:"100%",width:`${r.pct}%`,background:"linear-gradient(90deg,#0ea5e9,#10b981)",borderRadius:4}}/>
                      </div>
                      <span style={{fontSize:13,fontFamily:"monospace",color:"#10b981",textAlign:"right"}}>${r.mrr.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ── SYSTEM ── */}
          {active==="system" && (
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
              {[
                {label:"Fly.io API",        status:"operational", uptime:"99.98%",  resp:"142ms"},
                {label:"Supabase DB",       status:"operational", uptime:"99.99%",  resp:"18ms"},
                {label:"Redis Cache",       status:"operational", uptime:"100%",    resp:"3ms"},
                {label:"Anthropic AI",      status:"operational", uptime:"99.95%",  resp:"2,840ms"},
                {label:"Telegram Bot",      status:"operational", uptime:"99.97%",  resp:"210ms"},
                {label:"Bybit Testnet",     status:"degraded",    uptime:"97.2%",   resp:"890ms"},
              ].map(s=>(
                <div key={s.label} style={{background:"#0d1526",border:`1px solid ${s.status==="operational"?"rgba(16,185,129,0.2)":"rgba(251,191,36,0.25)"}`,borderRadius:14,padding:"20px 24px",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <div style={{display:"flex",alignItems:"center",gap:12}}>
                    <div style={{width:10,height:10,borderRadius:"50%",background:s.status==="operational"?"#10b981":"#fbbf24",boxShadow:`0 0 8px ${s.status==="operational"?"#10b981":"#fbbf24"}`}}/>
                    <div>
                      <p style={{fontWeight:600,fontSize:14,marginBottom:2}}>{s.label}</p>
                      <p style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>Response: {s.resp}</p>
                    </div>
                  </div>
                  <div style={{textAlign:"right"}}>
                    <p style={{fontSize:12,color:s.status==="operational"?"#10b981":"#fbbf24",fontWeight:600,textTransform:"capitalize"}}>{s.status}</p>
                    <p style={{fontSize:11,color:"rgba(255,255,255,0.35)"}}>Uptime: {s.uptime}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── SETTINGS ── */}
          {active==="settings" && (
            <div style={{maxWidth:560,display:"flex",flexDirection:"column",gap:14}}>
              {[
                {label:"Platform Name",       val:"TradoAI"},
                {label:"Support Email",        val:"hello@tradoai.net"},
                {label:"Max Trial Days",       val:"7 days"},
                {label:"Default Max Leverage", val:"3x"},
                {label:"AI Model",             val:"claude-sonnet-4-5"},
                {label:"Cache TTL (prices)",   val:"30 seconds"},
                {label:"Maintenance Mode",     val:"Off"},
                {label:"New Signups",          val:"Enabled"},
              ].map(s=>(
                <div key={s.label} style={{background:"#0d1526",border:"1px solid rgba(255,255,255,0.07)",borderRadius:12,padding:"18px 22px",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <p style={{fontWeight:500,fontSize:14}}>{s.label}</p>
                  <span style={{padding:"6px 14px",background:"rgba(14,165,233,0.1)",border:"1px solid rgba(14,165,233,0.2)",borderRadius:8,color:"#0ea5e9",fontFamily:"monospace",fontSize:12,fontWeight:600}}>{s.val}</span>
                </div>
              ))}
              <button style={{padding:"14px",borderRadius:12,background:"linear-gradient(135deg,#0ea5e9,#10b981)",border:"none",color:"#020c07",fontWeight:700,fontSize:14,cursor:"pointer",marginTop:6}}>
                Save Changes
              </button>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
