"""Download ~2y of Bybit public history for offline evolution.

    python -m trado100.history --months 24 --out data/hist

Writes <out>/<SYMBOL>.npy (15m klines: ts,o,h,l,c,v), <out>/<SYMBOL>_funding.npy ([ts, rate])
and <out>/fng.npy ([ts, -1..1]). Public endpoints only, no keys. Must run where Bybit is reachable.
"""
from __future__ import annotations
import argparse, asyncio, os, time
import numpy as np
from .feed import Feed

DEFAULT_SYMS = "BTC ETH SOL XRP DOGE ADA AVAX LINK BNB SUI".split()


async def funding_all(feed: Feed, symbol: str, months: int) -> np.ndarray:
    since = int((time.time() - months * 30 * 86400) * 1000)
    end, rows = int(time.time() * 1000), []
    while end > since:
        res = await feed._get("/v5/market/funding/history", category="linear", symbol=symbol,
                              limit=200, endTime=end)
        if not res or not res["list"]:
            break
        page = [[float(r["fundingRateTimestamp"]), float(r["fundingRate"])] for r in res["list"]]
        rows += page
        end = int(min(p[0] for p in page)) - 1
        if len(page) < 2:
            break
    if not rows:
        return np.empty((0, 2))
    a = np.array(rows)[::-1]
    _, idx = np.unique(a[:, 0], return_index=True)
    return a[idx]


async def main(months: int, out: str, syms):
    os.makedirs(out, exist_ok=True)
    feed = Feed()
    for base in syms:
        s = base + "USDT"
        k = await feed.klines(s, months * 30 * 96)
        f = await funding_all(feed, s, months)
        np.save(os.path.join(out, f"{s}.npy"), k)
        np.save(os.path.join(out, f"{s}_funding.npy"), f)
        span = f"{(k[-1][0] - k[0][0]) / 86400000:.0f}d" if len(k) else "none"
        print(f"{s}: {len(k)} bars ({span}), {len(f)} funding rows", flush=True)
    sh = await feed.sentiment_history(months * 30 + 30)
    np.save(os.path.join(out, "fng.npy"), sh)
    print(f"fng: {len(sh)} days")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=24)
    ap.add_argument("--out", default="data/hist")
    ap.add_argument("--symbols", default=",".join(DEFAULT_SYMS))
    a = ap.parse_args()
    asyncio.run(main(a.months, a.out, a.symbols.split(",")))
