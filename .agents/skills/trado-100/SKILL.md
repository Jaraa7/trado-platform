---
name: trado-100
description: TRADO-100 — the 100-manager evolutionary trading system on TRADO. Load this before ANY work on managers, genomes, families, death/inheritance rules, the event engine, Risk Guardian, the six Supabase tables, scheduled tasks (evolve / post-mortem / guardian), or promotion stages. Holds the owner's decisions (Nov 2026), the hard rules that never change, table names, and what is explicitly out of scope.
---

# TRADO-100 — نظام المدراء المتطوّر

Design doc (editable, source of truth for intent): https://claude.ai/artifact/2oKznfTFETfc3XSdw8sq2R
Project summary: `claude/trado-100-managers-system.md` in the claude.ai Project "TRADO Platform".

## Owner decisions (6 Nov 2026) — do not re-ask
| Item | Decision |
|---|---|
| Status | Freeze lifted; building now |
| Managers | 100 from day one, 10 families × 10 variants |
| Market | Bybit **Perp (linear)**, leverage ≤ 3x; stage-D real managers 1x |
| Universe | Top 50 Bybit Perp symbols by 24h volume, refreshed monthly |
| Real money | Paper for ≥ 2 months first. Wave-2 cap **1,000 USD total**, owner GO per manager |
| Alerts | Google Calendar «تنبيهات TRADO» (death, promotion-needs-GO, kill switch) |
| Weekly review | Friday morning (Kuwait) |
| Code path | Claude sessions with repo attached + Supabase MCP → PRs; deploy to Fly from the Mac (`flyctl`) |
| Spend caps | AI 100 USD/mo (warn 80), Fly.io 25 USD/mo |
| Language | Talk to the owner in Kuwaiti Arabic; code/comments may be English |

## Hard rules (never evolve, never override)
- **Risk Guardian is law**: every order passes it; it alone has veto. Pure Python math, no LLM on the hot path.
- Risk per trade ≤ 2% of manager equity; R:R ≥ 1.5; daily loss 6% ⇒ 24h freeze; leverage ≤ 3x.
- **Global kill switch**: real treasury drawdown 20% from peak ⇒ all real execution stops, everyone back to paper until the owner unlocks.
- Exchange keys: trade-only, no withdrawal, IP-restricted to Fly.
- No new entries inside the macro blackout window (`data_sources/macro_calendar.py` → `MacroCalendar.blackout()`), ±30 min around high-impact USD events.
- Paper fills = live mid price + 0.1% slippage + real Bybit taker fee.
- No family may hold > 30 of 100 seats; every family keeps ≥ 3 seats even while losing (diversity guard).
- A paper manager showing > 40%/month goes under "watch" (re-backtest on a second period) — assume overfitting, not genius.

## Death rules (automatic, immediate, no second chance for the same manager)
| Rule | Threshold |
|---|---|
| Total drawdown | 15% below equity peak |
| Daily loss | 6% once ⇒ 24h freeze; twice in 7 days ⇒ death |
| Idle | 0 trades in 14 days |
| Stuck | 90 days in stage A without promotion |
| Rule breach | any attempt to exceed Risk Guardian size/leverage |
| Correlation | 3 same-family managers lose the same trade same day ⇒ weakest dies |

## Lifecycle
born → alive → dead → inherit. Birth = mutation (±10–20% on 1–2 genes) or crossover of two top survivors, then Freqtrade backtest on last 90 days — losers are never born. Death writes a post-mortem to `deaths`; the freed seat is refilled within 1 hour with a child that inherits the family's `lessons`.

## Stages
| Stage | Entry condition | Capital | Mode |
|---|---|---|---|
| A | born | 1,000 paper | paper |
| B | +20% within ≤ 60d, DD ≤ 10%, ≥ 30 trades | 2,000 paper | paper |
| C | +50% cumulative, DD ≤ 12%, 90d alive | 5,000 paper | paper |
| D | top-5 two months running **+ owner GO** | 100–250 USD real | real, 1x |
| E | +30% real in 90d, DD ≤ 10% | per treasury | real |

## Families (10)
trend · breakout · mean_reversion · scalp · grid · funding_basis · regime_switch · sentiment · accumulate · llm_judge
Only `llm_judge` (10 managers) calls an LLM (Gemini Flash-Lite) and only on ≥ 1h timeframes. Everything else is numpy.

## Supabase tables (project `mmuupwishkejogasopez`)
`t100_managers` · `t100_trades` · `t100_deaths` · `t100_lessons` · `t100_regime_stats` · `t100_treasury` (prefixed because `public.trades` already exists for SaaS users; RLS on, no policies = service role only)
Migration: `db/migrations/004_trado100.sql`. Lessons become active only after two consecutive weekly post-mortems agree; harmful lessons auto-retire after one month of worse performance.

## Runtime (Fly app `trado-bot`, region sin)
- `feed` process: one Bybit v5 WebSocket (`publicTrade`, `kline.1`, `orderbook.50`) → Redis (`px:{sym}`, candles, Pub/Sub `events:{sym}`), heartbeat every 10s; stale > 30s ⇒ engine goes "blind" (no new entries).
- `engine` process: subscribes `events:*`, wakes only the managers subscribed to that symbol/event; stop-loss / take-profit checked on every price event.
- Scheduled: `evolve` nightly 00:10 UTC · `post-mortem` Sunday 09:00 · `guardian` hourly (heartbeats, spend caps, kill switch, `flyctl machine restart` if worker silent 15 min).
- Existing modules to reuse, not rewrite: `strategies/engine.py` (4 strategy classes + `Indicators`), `nervous/` (scheduler, decisions, performance), `data_sources/` (14 free sources), `agents/trading/risk_guardian`, `agents/trading/regime_detector`, `freqtrade/`.

## Out of scope (do not build)
Payment gateway, subscription tiers, customer chatbots, marketing agents, HFT/co-location, paid data feeds. This is the owner's private system, not a product.

## Working style the owner requires
Every proposed step must be executable and concrete. No "consider doing X". Open a PR per week-step; the owner reviews Fridays.
