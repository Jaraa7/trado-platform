"""
TradoTrendV1 — أول استراتيجية مرشّحة (3 معاملات فقط عمدًا).
اتجاه: EMA20 فوق EMA50 وADX>25 وتراجع إلى EMA20. خروج: 2R أو كسر EMA50.
تُختبر فقط في نظام trending (يأتي من nervous.market كفلتر لاحقًا).
"""
from freqtrade.strategy import IStrategy
import talib.abstract as ta
from pandas import DataFrame


class TradoTrendV1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = True
    minimal_roi = {"0": 10}          # الخروج بالقواعد لا بالـ ROI
    stoploss = -0.02                 # 1R = 2% تقريبًا على 1h
    trailing_stop = False
    startup_candle_count = 60

    adx_min = 25                     # معامل 1
    ema_fast = 20                    # معامل 2
    ema_slow = 50                    # معامل 3

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        df["ema_f"] = ta.EMA(df, timeperiod=self.ema_fast)
        df["ema_s"] = ta.EMA(df, timeperiod=self.ema_slow)
        df["adx"] = ta.ADX(df, timeperiod=14)
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        up = (df["ema_f"] > df["ema_s"]) & (df["adx"] > self.adx_min)
        dn = (df["ema_f"] < df["ema_s"]) & (df["adx"] > self.adx_min)
        df.loc[up & (df["low"] <= df["ema_f"]) & (df["close"] > df["ema_f"]), "enter_long"] = 1
        df.loc[dn & (df["high"] >= df["ema_f"]) & (df["close"] < df["ema_f"]), "enter_short"] = 1
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[df["close"] < df["ema_s"], "exit_long"] = 1
        df.loc[df["close"] > df["ema_s"], "exit_short"] = 1
        return df

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_profit >= 0.04:    # 2R
            return "take_profit_2R"
        return None
