"""
[부자회사원 7개월 검증 삼중 스크린 엔벨로프/EMA 주도주 눌림목 매매 전략]
SK Hynix (000660) High-Beta Momentum Multi-Timeframe Strategy Engine
Based on YouTube Reference: https://youtu.be/8j-C8Ec_OLk
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np

from config.settings import config
from core.indicators import (
    calculate_ema,
    calculate_envelope,
    calculate_macd,
    calculate_vwap,
    calculate_rsi,
    calculate_atr,
    calculate_rvol
)

@dataclass
class StrategySignal:
    should_enter: bool = False
    strategy_name: str = "BUJA_ENVELOPE_PULLBACK"
    reason: str = ""
    suggested_price: float = 0.0
    stop_loss_price: float = 0.0
    target_price: float = 0.0
    state_15m: str = "NEUTRAL"
    state_5m: str = "NEUTRAL"
    state_3m: str = "NEUTRAL"
    metrics: Dict[str, Any] = field(default_factory=dict)

class SKHynixPullbackStrategyEngine:
    def __init__(self):
        self.orb_high: float = 0.0
        self.orb_low: float = float('inf')
        self.orb_initialized: bool = False

    def evaluate(
        self,
        df_15m: pd.DataFrame,
        df_5m: pd.DataFrame,
        df_3m: pd.DataFrame,
        current_price: float,
        realtime_intensity: float,
        current_time: datetime
    ) -> StrategySignal:
        signal = StrategySignal(metrics={})
        now_time = current_time.time()
        
        # -------------------------------------------------------------
        # [가드레일 4] 09:00 ~ 09:15 시초가 갭 페이크 방어 (Blackout)
        # -------------------------------------------------------------
        if now_time < config.TIME_BLACKOUT_END:
            signal.state_15m = "BLACKOUT_ORB_BUILDING (09:15 이전 대기)"
            signal.reason = "시초 15분간 주도주 갭/노이즈 안정화 대기"
            return signal
            
        if not self.orb_initialized and len(df_15m) > 0:
            self.orb_high = df_15m.iloc[0]['high']
            self.orb_low = df_15m.iloc[0]['low']
            self.orb_initialized = True
            
        # -------------------------------------------------------------
        # [가드레일 4] 15:15 장마감 임박 신규 진입 차단
        # -------------------------------------------------------------
        if now_time >= config.TIME_ENTRY_DEADLINE:
            signal.state_15m = "MARKET_CLOSE_TIMEOUT (15:15 이후 신규매수 금지)"
            signal.reason = "장마감 임박으로 신규 진입 차단"
            return signal

        if len(df_15m) < 20 or len(df_5m) < 20 or len(df_3m) < 20:
            signal.reason = "최소 분봉 캔들 데이터 누적 대기"
            return signal

        # -------------------------------------------------------------
        # [Screen 1] 15분봉 조류(Tide) - 대형 추세 및 MACD 모멘텀 필터
        # -------------------------------------------------------------
        ema_20_15m = calculate_ema(df_15m['close'], config.EMA_FAST_15M)
        ema_60_15m = calculate_ema(df_15m['close'], config.EMA_MID_15M)
        ema_120_15m = calculate_ema(df_15m['close'], config.EMA_SLOW_15M)
        macd_15m, sig_15m, hist_15m = calculate_macd(df_15m['close'], 12, 26, 9)
        atr_15m = calculate_atr(df_15m, 14)
        
        last_close_15m = df_15m['close'].iloc[-1]
        last_atr = atr_15m.iloc[-1]
        atr_pct = (last_atr / last_close_15m) * 100.0
        
        # [가드레일 2] SK하이닉스 최소 변동성 게이트 (15M ATR >= 0.70%)
        if atr_pct < config.MIN_15M_ATR_PCT:
            signal.state_15m = f"LOW_VOLATILITY (ATR {atr_pct:.2f}% < {config.MIN_15M_ATR_PCT}%)"
            signal.reason = "15분봉 변동성 부족으로 수수료 잠식 방어"
            return signal

        # 15M 추세 정배열: EMA 20 > EMA 60 > EMA 120 (또는 EMA 60 > EMA 120 정배열 & 종가 > EMA 20)
        is_15m_trend_bullish = (
            (ema_60_15m.iloc[-1] > ema_120_15m.iloc[-1]) and
            (last_close_15m >= ema_20_15m.iloc[-1] * 0.997) and
            (hist_15m.iloc[-1] >= -0.001 or macd_15m.iloc[-1] >= sig_15m.iloc[-1])
        )
        
        if not is_15m_trend_bullish:
            signal.state_15m = "WAITING_15M_BULLISH_TREND (이평 정배열 & MACD 상향)"
            signal.reason = "15분봉 거시 추세 정배열 미충족"
            return signal
            
        signal.state_15m = "15M_TIDE_BULLISH 🟢"

        # -------------------------------------------------------------
        # [Screen 2] 5분봉 파도(Wave) - 부자회사원 엔벨로프(20, 1.8%) / VWAP 눌림목 포착
        # -------------------------------------------------------------
        env_up_5m, env_mid_5m, env_low_5m = calculate_envelope(df_5m['close'], config.ENVELOPE_PERIOD_5M, config.ENVELOPE_PERCENT_5M)
        vwap_5m = calculate_vwap(df_5m)
        rsi_5m = calculate_rsi(df_5m['close'], config.RSI_PERIOD_5M)
        
        last_candle_5m = df_5m.iloc[-1]
        last_env_low = env_low_5m.iloc[-1]
        last_vwap = vwap_5m.iloc[-1]
        last_rsi = rsi_5m.iloc[-1]
        
        # 엔벨로프 하단선 근접/터치 (하단선 대비 +0.3% 이내) 또는 VWAP 평단 지지
        is_envelope_touch = last_candle_5m['low'] <= (last_env_low * 1.003)
        is_vwap_support = last_candle_5m['low'] <= (last_vwap * 1.002) and (last_candle_5m['close'] >= last_vwap * 0.998)
        is_pullback_zone = is_envelope_touch or is_vwap_support
        
        # RSI 쿨다운(35~48) 후 반등 또는 42선 상향 돌파
        is_rsi_rebound = (last_rsi >= config.RSI_PULLBACK_MIN_5M) and (last_rsi <= 55.0)
        
        # 5분봉 밑꼬리 달린 지지 양봉 확인
        candle_body = abs(last_candle_5m['close'] - last_candle_5m['open'])
        lower_shadow = min(last_candle_5m['open'], last_candle_5m['close']) - last_candle_5m['low']
        is_pinbar_support = lower_shadow >= (candle_body * 0.5) or (last_candle_5m['close'] >= last_candle_5m['open'])

        if not (is_pullback_zone and is_rsi_rebound and is_pinbar_support):
            signal.state_5m = f"WAITING_5M_PULLBACK (EnvLow:{last_env_low:,.0f}, RSI:{last_rsi:.1f})"
            signal.reason = "5분봉 엔벨로프 하단 지지선/VWAP 눌림목 미도달 또는 지지 캔들 미형성"
            return signal
            
        signal.state_5m = "5M_WAVE_PULLBACK_SUPPORT 🟢"

        # -------------------------------------------------------------
        # [Screen 3] 3분봉 잔물결(Ripple) - 5 EMA 돌파 + RVOL 200%↑ + 체결강도 110%↑
        # -------------------------------------------------------------
        ema_5_3m = calculate_ema(df_3m['close'], config.EMA_TRIGGER_3M)
        rvol_3m = calculate_rvol(df_3m['volume'], 20)
        
        last_close_3m = df_3m['close'].iloc[-1]
        last_ema_5 = ema_5_3m.iloc[-1]
        last_rvol = rvol_3m.iloc[-1]
        
        is_3m_breakout = (current_price >= last_ema_5)
        is_rvol_spike = (last_rvol >= config.RVOL_THRESHOLD_3M)
        is_intensity_strong = (realtime_intensity >= config.INTENSITY_MIN_3M)

        swing_low = df_5m['low'].iloc[-4:].min()
        stop_price = round(swing_low - 500, 0) # 직전 저점 -2틱(-500원)
        target_1 = round(env_mid_5m.iloc[-1], 0) if env_mid_5m.iloc[-1] > current_price else round(current_price * (1.0 + config.TAKE_PROFIT_1_PCT / 100.0), 0)
        target_2 = round(env_up_5m.iloc[-1], 0) if env_up_5m.iloc[-1] > current_price else round(current_price * (1.0 + config.TAKE_PROFIT_2_PCT / 100.0), 0)

        signal.metrics = {
            'price': current_price,
            '15m_atr_pct': float(atr_pct),
            '5m_env_low': float(last_env_low),
            '5m_env_mid': float(env_mid_5m.iloc[-1]),
            '5m_env_up': float(env_up_5m.iloc[-1]),
            '5m_rsi': float(last_rsi),
            '3m_rvol': float(last_rvol),
            'intensity': float(realtime_intensity),
            'stop_loss': float(stop_price),
            'target_1': float(target_1),
            'target_2': float(target_2)
        }

        if is_3m_breakout and (is_rvol_spike or is_intensity_strong):
            signal.state_3m = "TRIGGERED 🚀"
            signal.should_enter = True
            signal.suggested_price = current_price
            signal.stop_loss_price = stop_price
            signal.target_price = target_1
            signal.reason = (
                f"[부자회사원 눌림목 확정] [15M 조류 정배열] -> [5M 엔벨로프({config.ENVELOPE_PERCENT_5M}%) 지지/RSI {last_rsi:.1f}] -> "
                f"[3M 5EMA 돌파/RVOL {last_rvol:.1f}배/체결강도 {realtime_intensity:.1f}%]"
            )
        else:
            signal.state_3m = f"TRIGGER_WAIT (RVOL: {last_rvol:.1f}x, 체결강도: {realtime_intensity:.1f}%)"
            signal.reason = "3분봉 5 EMA 돌파 및 수급(RVOL/체결강도) 트리거 대기"

        return signal
