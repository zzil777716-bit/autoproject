"""
========================================================================================
🏛️ [SDK: STRATEGY INTERFACES & DUAL-STRATEGY SUITE]
Pure Python strategy implementations matching backtest and live production environments.
1. Strategy A: 15M 3-Lines (20선, VWAP20, 전환선13) 2-Bars Sustained Close
2. Strategy B: 15M MA 20-60-120 Alignment & Golden Disparity (101.5% ~ 103.2%)
3. DualStrategyEngine: Evaluates both engines simultaneously with individual/dual tagging
========================================================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

@dataclass
class StrategySignal:
    should_enter: bool
    side: str = "BUY"
    entry_price: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    strategy_tag: str = "DEFAULT"
    reason: str = ""

class BaseStrategy(ABC):
    def __init__(self, code: str, stock_name: str):
        self.code = code
        self.stock_name = stock_name
        self.strategy_name = self.__class__.__name__

    @abstractmethod
    def evaluate(self, data_feed: Dict[str, pd.DataFrame], current_time_str: str) -> StrategySignal:
        pass

# ========================================================================================
# 1. [전략 A] 15분봉 3선(20선, VWAP20, 일목 전환선13) 2봉 연속 종가 유지 전략
# ========================================================================================
class Samsung3LinesSustainedStrategy(BaseStrategy):
    """[삼성전자 전략 A] 15M 3선 2봉 연속 종가 유지 확인 전략"""
    def __init__(self, code: str = "005930", stock_name: str = "삼성전자"):
        super().__init__(code, stock_name)

    def evaluate(self, data_feed: Dict[str, pd.DataFrame], current_time_str: str) -> StrategySignal:
        df_15m = data_feed.get("15m")
        if df_15m is None or len(df_15m) < 20:
            return StrategySignal(should_enter=False)

        close = df_15m['close']
        ma20 = close.rolling(20).mean()
        cum_vol = df_15m['volume'].rolling(20).sum()
        cum_val = (close * df_15m['volume']).rolling(20).sum()
        vwap20 = cum_val / (cum_vol + 1e-9)
        h13 = df_15m['high'].rolling(13).max()
        l13 = df_15m['low'].rolling(13).min()
        tenkan13 = (h13 + l13) / 2.0

        all_3lines = (close > ma20) & (close > vwap20) & (close > tenkan13)
        sustained_2bars = all_3lines & all_3lines.shift(1).fillna(False)

        is_now_sustained = sustained_2bars.iloc[-1]
        was_previously_sustained = sustained_2bars.iloc[-2] if len(sustained_2bars) >= 2 else False
        cur_price = close.iloc[-1]

        if is_now_sustained and not was_previously_sustained:
            reason = (
                f"[전략 A: 3선안착] 15M 3선 종가 유지 확인 (현재가: {cur_price:,.0f} > "
                f"20선: {ma20.iloc[-1]:,.0f}, VWAP20: {vwap20.iloc[-1]:,.0f}, 전환선: {tenkan13.iloc[-1]:,.0f})"
            )
            return StrategySignal(
                should_enter=True,
                side="BUY",
                entry_price=cur_price,
                stop_loss_price=cur_price * 0.991,
                take_profit_price=cur_price * 1.015,
                strategy_tag="STRATEGY_A_3LINES",
                reason=reason
            )

        return StrategySignal(should_enter=False)

class SKHynix3LinesMomentumStrategy(BaseStrategy):
    """[SK하이닉스 전략 A] 15M 3선 유지 + 3M 5EMA 돌파 및 RVOL 점화 전략"""
    def __init__(self, code: str = "000660", stock_name: str = "SK하이닉스"):
        super().__init__(code, stock_name)

    def evaluate(self, data_feed: Dict[str, pd.DataFrame], current_time_str: str) -> StrategySignal:
        df_15m = data_feed.get("15m")
        df_3m = data_feed.get("3m")

        if df_15m is None or len(df_15m) < 20 or df_3m is None or len(df_3m) < 6:
            return StrategySignal(should_enter=False)

        close15 = df_15m['close']
        ma20 = close15.rolling(20).mean()
        cum_vol15 = df_15m['volume'].rolling(20).sum()
        cum_val15 = (close15 * df_15m['volume']).rolling(20).sum()
        vwap20 = cum_val15 / (cum_vol15 + 1e-9)
        h13 = df_15m['high'].rolling(13).max()
        l13 = df_15m['low'].rolling(13).min()
        tenkan13 = (h13 + l13) / 2.0

        all_3lines = (close15 > ma20) & (close15 > vwap20) & (close15 > tenkan13)
        sustained_2bars = all_3lines & all_3lines.shift(1).fillna(False)

        if not sustained_2bars.iloc[-1]:
            return StrategySignal(should_enter=False)

        close3 = df_3m['close']
        ema5 = close3.ewm(span=5, adjust=False).mean()
        vol3 = df_3m['volume']
        vol_ma5 = vol3.rolling(5).mean()
        rvol = vol3 / (vol_ma5 + 1e-9)

        ema_cross = (close3.iloc[-1] > ema5.iloc[-1]) and (close3.iloc[-2] <= ema5.iloc[-2])
        rvol_surge = rvol.iloc[-1] >= 1.35
        cur_price = close3.iloc[-1]

        if ema_cross and rvol_surge:
            reason = (
                f"[전략 A: 3선점화] 15M 3선 유지 + 3M 5EMA 돌파 및 RVOL {rvol.iloc[-1]:.1f}배 점화 (현재가: {cur_price:,.0f}원)"
            )
            return StrategySignal(
                should_enter=True,
                side="BUY",
                entry_price=cur_price,
                stop_loss_price=cur_price * 0.991,
                take_profit_price=cur_price * 1.015,
                strategy_tag="STRATEGY_A_3LINES",
                reason=reason
            )

        return StrategySignal(should_enter=False)

# ========================================================================================
# 2. [전략 B] 15분봉 20-60-120 정배열 & 황금 이격도 (101.5% ~ 103.2%) 전략
# ========================================================================================
class SamsungAlignmentDisparityStrategy(BaseStrategy):
    """[삼성전자 전략 B] 15M 20-60-120 정배열 + 황금 이격도(101.5%~103.0%) + 5M 반등"""
    def __init__(self, code: str = "005930", stock_name: str = "삼성전자"):
        super().__init__(code, stock_name)

    def evaluate(self, data_feed: Dict[str, pd.DataFrame], current_time_str: str) -> StrategySignal:
        df_15m = data_feed.get("15m")
        df_5m = data_feed.get("5m")
        if df_15m is None or len(df_15m) < 120 or df_5m is None or len(df_5m) < 20:
            return StrategySignal(should_enter=False)

        close15 = df_15m['close']
        ma20 = close15.rolling(20).mean().iloc[-1]
        ma60 = close15.rolling(60).mean().iloc[-1]
        ma120 = close15.rolling(120).mean().iloc[-1]
        cur_price = close15.iloc[-1]

        is_aligned = (ma20 > ma60) and (ma60 > ma120)
        disp_price_ma20 = (cur_price / (ma20 + 1e-9)) * 100.0
        is_golden_disp = (101.5 <= disp_price_ma20 <= 103.0)

        # 5분봉 20EMA/VWAP 지지 양봉 반등 확인
        c5 = df_5m['close']
        ema20_5 = c5.ewm(span=20, adjust=False).mean().iloc[-1]
        rebound_5m = (df_5m['low'].iloc[-1] <= ema20_5 * 1.003) and (c5.iloc[-1] > df_5m['open'].iloc[-1])

        if is_aligned and is_golden_disp and rebound_5m:
            reason = (
                f"[전략 B: 정배열이격] 15M 20>60>120 정배열 + 황금 이격도 {disp_price_ma20:.1f}% + 5M 지지반등 (현재가: {cur_price:,.0f}원)"
            )
            return StrategySignal(
                should_enter=True,
                side="BUY",
                entry_price=cur_price,
                stop_loss_price=cur_price * 0.991,
                take_profit_price=cur_price * 1.015,
                strategy_tag="STRATEGY_B_DISPARITY",
                reason=reason
            )

        return StrategySignal(should_enter=False)

class SKHynixAlignmentDisparityStrategy(BaseStrategy):
    """[SK하이닉스 전략 B] 15M 20-60-120 정배열 + 황금 이격도(101.5%~104.0%) + 3M 점화"""
    def __init__(self, code: str = "000660", stock_name: str = "SK하이닉스"):
        super().__init__(code, stock_name)

    def evaluate(self, data_feed: Dict[str, pd.DataFrame], current_time_str: str) -> StrategySignal:
        df_15m = data_feed.get("15m")
        df_3m = data_feed.get("3m")
        if df_15m is None or len(df_15m) < 120 or df_3m is None or len(df_3m) < 6:
            return StrategySignal(should_enter=False)

        close15 = df_15m['close']
        ma20 = close15.rolling(20).mean().iloc[-1]
        ma60 = close15.rolling(60).mean().iloc[-1]
        ma120 = close15.rolling(120).mean().iloc[-1]
        cur_price = close15.iloc[-1]

        is_aligned = (ma20 > ma60) and (ma60 > ma120)
        disp_price_ma20 = (cur_price / (ma20 + 1e-9)) * 100.0
        is_golden_disp = (101.5 <= disp_price_ma20 <= 104.0)

        # 3분봉 5EMA 돌파 및 거래량 1.35배 점화
        c3 = df_3m['close']
        ema5_3 = c3.ewm(span=5, adjust=False).mean()
        rvol = df_3m['volume'].iloc[-1] / (df_3m['volume'].rolling(5).mean().iloc[-1] + 1e-9)
        ema_cross = (c3.iloc[-1] > ema5_3.iloc[-1]) and (c3.iloc[-2] <= ema5_3.iloc[-2])
        rvol_surge = rvol >= 1.35

        if is_aligned and is_golden_disp and ema_cross and rvol_surge:
            reason = (
                f"[전략 B: 정배열이격] 15M 20>60>120 정배열 + 황금 이격도 {disp_price_ma20:.1f}% + 3M RVOL {rvol:.1f}배 점화 (현재가: {cur_price:,.0f}원)"
            )
            return StrategySignal(
                should_enter=True,
                side="BUY",
                entry_price=cur_price,
                stop_loss_price=cur_price * 0.991,
                take_profit_price=cur_price * 1.015,
                strategy_tag="STRATEGY_B_DISPARITY",
                reason=reason
            )

        return StrategySignal(should_enter=False)

# ========================================================================================
# 3. [통합 듀얼 엔진] 전략 A와 전략 B를 동시 감시 및 발주하는 합성 엔진
# ========================================================================================
class DualStrategyEngine(BaseStrategy):
    def __init__(self, code: str, stock_name: str):
        super().__init__(code, stock_name)
        if code == "005930":
            self.strategy_a = Samsung3LinesSustainedStrategy(code, stock_name)
            self.strategy_b = SamsungAlignmentDisparityStrategy(code, stock_name)
        else:
            self.strategy_a = SKHynix3LinesMomentumStrategy(code, stock_name)
            self.strategy_b = SKHynixAlignmentDisparityStrategy(code, stock_name)

    def evaluate(self, data_feed: Dict[str, pd.DataFrame], current_time_str: str) -> StrategySignal:
        sig_a = self.strategy_a.evaluate(data_feed, current_time_str)
        sig_b = self.strategy_b.evaluate(data_feed, current_time_str)

        # 1. 두 전략 동시 충족 (초강력 합의 신호)
        if sig_a.should_enter and sig_b.should_enter:
            return StrategySignal(
                should_enter=True,
                side="BUY",
                entry_price=sig_a.entry_price,
                stop_loss_price=sig_a.stop_loss_price,
                take_profit_price=sig_a.take_profit_price,
                strategy_tag="DUAL_CONFLUENCE_A+B",
                reason=f"🔥 [초강력 합의: A+B 동시발생] {sig_a.reason} & {sig_b.reason}"
            )

        # 2. 전략 A 단독 발생
        if sig_a.should_enter:
            return sig_a

        # 3. 전략 B 단독 발생
        if sig_b.should_enter:
            return sig_b

        return StrategySignal(should_enter=False)
