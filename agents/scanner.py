"""
Scanner Agent - TRADO Platform
Model: Gemini 2.5 Flash-Lite
3,900+ pairs monitored every second
"""
import asyncio
import ccxt.async_support as ccxt
from core.data_validator import DataValidator

class ScannerAgent:
      MIN_VOLUME_24H = 1_000_000
      PRICE_CHANGE_THRESHOLD = 2.0

    def __init__(self, config: dict):
              self.config = config
              self.validator = DataValidator()
              self.exchanges = {
                  'binance': ccxt.binance({
                      'apiKey': config['BINANCE_API_KEY'],
                      'secret': config['BINANCE_API_SECRET'],
                      'enableRateLimit': True
                  }),
                  'bybit': ccxt.bybit({
                      'apiKey': config['BYBIT_API_KEY'],
                      'secret': config['BYBIT_API_SECRET'],
                      'enableRateLimit': True
                  }),
                  'okx': ccxt.okx({
                      'apiKey': config['OKX_API_KEY'],
                      'secret': config['OKX_API_SECRET'],
                      'enableRateLimit': True
                  })
              }
              self.blacklist = set()

    async def layer_zero_receive(self) -> list:
              """Layer 0: Receive all tickers via API"""
              all_tickers = []
              for name, exchange in self.exchanges.items():
                            try:
                                              tickers = await exchange.fetch_tickers()
                                              for symbol, data in tickers.items():
                                                                    if data.get('quoteVolume', 0) > self.MIN_VOLUME_24H:
                                                                                              all_tickers.append({
                                                                                                                            'exchange': name,
                                                                                                                            'symbol': symbol,
                                                                                                                            'price': data.get('last', 0),
                                                                                                                            'change': data.get('percentage', 0),
                                                                                                                            'volume': data.get('quoteVolume', 0)
                                                                                                })
                            except Exception as e:
                                              print(f'[Scanner] {name} error: {e}')
                                      return all_tickers

    def layer_one_filter(self, tickers: list) -> list:
              """Layer 1: Fast mathematical filter"""
              return [
                  t for t in tickers
                  if t['symbol'] not in self.blacklist
                  and abs(t.get('change', 0)) > self.PRICE_CHANGE_THRESHOLD
              ][:80]

    async def layer_two_technical(self, candidates: list) -> list:
              """Layer 2: RSI + EMA technical analysis"""
              qualified = []
              for ticker in candidates[:20]:
                            try:
                                              exchange = self.exchanges[ticker['exchange']]
                                              ohlcv = await exchange.fetch_ohlcv(ticker['symbol'], '5m', limit=50)
                                              if not ohlcv or len(ohlcv) < 20:
                                                                    continue
                                                                closes = [c[4] for c in ohlcv]
                                              rsi = self._calc_rsi(closes)
                                              ema20 = sum(closes[-20:]) / 20
                                              trend_up = closes[-1] > ema20
                                              if 25 < rsi < 75 and trend_up:
                                                                    ticker['rsi'] = round(rsi, 2)
                                                                    ticker['ema20'] = round(ema20, 6)
                                                                    qualified.append(ticker)
                            except Exception:
                                              continue
                                      return qualified

    def _calc_rsi(self, closes: list, period: int = 14) -> float:
              if len(closes) < period + 1:
                            return 50.0
                        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [max(d, 0) for d in deltas[-period:]]
        losses = [abs(min(d, 0)) for d in deltas[-period:]]
        avg_gain = sum(gains) / period or 1e-9
        avg_loss = sum(losses) / period or 1e-9
        return 100 - (100 / (1 + avg_gain / avg_loss))

    async def scan(self) -> list:
              """Full scan cycle through all 4 layers"""
        tickers = await self.layer_zero_receive()
        candidates = self.layer_one_filter(tickers)
        qualified = await self.layer_two_technical(candidates)
        # Layer 3 (Claude decision) happens in Analyst Agent
        return qualified[:15]

    async def close(self):
              for exchange in self.exchanges.values():
                            await exchange.close()
