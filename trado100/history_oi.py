"""Download Bybit open-interest history (1h) next to the kline history.

    python3 -u -m trado100.history_oi --out data/hist --months 24

Writes <out>/<SYMBOL>_oi.npy = [[ts_ms, open_interest]] oldest first. Public endpoint, no keys.
"""
from __future__ import annotations
import argparse, asyncio, glob, os, time
import numpy as np
from .feed import Feed


async def oi_all(feed: Feed, symbol: str, months: int) -> np.ndarray:
    since = int((time.time() - months * 30 * 86400) * 1000)
    end, rows = int(time.time() * 1000), []
    while end > since:
        res = await feed._get("/v5/market/open-interest", category="linear", symbol=symbol,
                              intervalTime="1h", limit=200, endTime=end)
        if not res or not res["list"]:
            break
        page = [[float(r["timestamp"]), float(r["openInterest"])] for r in res["list"]]
        rows += page
        nxt = int(min(p[0] for p in page)) - 1
        if nxt >= end or len(page) < 2:
            break
        end = nxt
    if not rows:
        return np.empty((0, 2))
    a = np.array(rows)
    a = a[np.argsort(a[:, 0])]
    _, idx = np.unique(a[:, 0], return_index=True)
    return a[idx]


async def main(out: str, months: int):
    feed = Feed()
    for f in sorted(glob.glob(os.path.join(out, "*USDT.npy"))):
        s = os.path.basename(f)[:-4]
        a = await oi_all(feed, s, months)
        np.save(os.path.join(out, f"{s}_oi.npy"), a)
        span = f"{(a[-1][0] - a[0][0]) / 86400000:.0f}d" if len(a) else "none"
        print(f"{s}: {len(a)} OI rows ({span})", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/hist"); ap.add_argument("--months", type=int, default=24)
    a = ap.parse_args()
    asyncio.run(main(a.out, a.months))
