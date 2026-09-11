"""
Strategy 2: [변동성 수축 및 수급 반등형 (MTF-Squeeze & Divergence Reversal)]
Finite State Machine Engine for Samsung Electronics (005930)
Includes Red-Team Hardcore Guardrails & 1-Share Execution Mode.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np

from config.settings import config
from core.indicators import (
    calculate_ema,
    calculate_vwap,
    calculate_rsi,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_rvol
)

@dataclass
class StrategySignal:
    should_enter: bool = False
    strategy_name: str = "STRATEGY_2_SQUEEZE"
    reason: str = ""
    suggested_price: float = 0.0
    stop_loss_price: float = 0.0
    target_price: float = 0.0
    state_15m: str = "NEUTRAL"
    state_5m: str = "NEUTRAL"
    state_3m: str = "NEUTRAL"
    metrics: Dict[str, Any] = field(default_factory=dict)

class MTFStrategyEngine:
    def __init__(self):
        self.orb_high: float = 0.0
        self.orb_low: float = float('inf')
        self.orb_initialized: bool = False
        self.prev_intensity_3m: float = 100.0

    def evaluate(
        self,
        df_15m: pd.DataFrame,
        df_5m: pd.DataFrame,
        df_3m: pd.DataFrame,
        current_price: float,
        realtime_intensity: float,
        current_time: datetime
    ) -> StrategySignal:
        """
        전략 2 (변동성 수축 및 상승 다이버전스 반등) 15M -> 5M -> 3M 연쇄 판정.
        """
        signal = StrategySignal(metrics={})
        now_time = current_time.time()
        
        # -------------------------------------------------------------
        # [가드레일 4] 09:00 ~ 09:15 시초가 갭 페이크 방어 (Blackout)
        # -------------------------------------------------------------
        if now_time < config.TIME_BLACKOUT_END:
            signal.state_15m = "BLACKOUT_ORB_BUILDING (09:15 이전 대기)"
            signal.reason = "시초 15분간 노이즈/갭 필터링 대기"
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
            signal.reason = "지표 계산을 위한 최소 분봉 데이터 누적 대기"
            return signal

        # -------------------------------------------------------------
        # 1. [15분봉 변동성 수축 필터 (Macro Squeeze Gate)]
        # -------------------------------------------------------------
        bb_upper_15m, bb_mid_15m, bb_lower_15m, bb_bw_15m = calculate_bollinger_bands(df_15m['close'], config.BB_PERIOD_15M, config.BB_STD_15M)
        atr_15m = calculate_atr(df_15m, 14)
        ema_120_15m = calculate_ema(df_15m['close'], config.EMA_SUPPORT_15M)
        
        last_bw_15m = bb_bw_15m.iloc[-1]
        last_atr_15m = atr_15m.iloc[-1]
        last_close_15m = df_15m['close'].iloc[-1]
        last_ema_120 = ema_120_15m.iloc[-1]
        
        # [가드레일 2] 최소 변동성 게이트 (15M ATR < 0.60% 시 진입 차단)
        atr_pct = (last_atr_15m / last_close_15m) * 100.0
        if atr_pct < config.MIN_15M_ATR_PCT:
            signal.state_15m = f"NO_TRADE (15M ATR {atr_pct:.2f}% < {config.MIN_15M_ATR_PCT}% 수수료 위험)"
            signal.reason = "15분봉 변동성이 너무 작아 수수료 잠식 위험으로 진입 차단"
            return signal

        # 볼린저 밴드 스퀴즈 (BandWidth <= 1.8%)
        is_15m_squeeze = last_bw_15m <= config.BB_BW_SQUEEZE_MAX_15M
        
        # 거시 지지 기반 확인 (120 EMA 상단 +0.5% 이내 또는 상회)
        is_15m_supported = last_close_15m >= (last_ema_120 * 0.995)

        if not (is_15m_squeeze and is_15m_supported):
            signal.state_15m = f"WAITING_SQUEEZE (BW:{last_bw_15m:.4f} <= {config.BB_BW_SQUEEZE_MAX_15M}, 120EMA 지지)"
            signal.reason = f"15분봉 변동성 수축(BW: {last_bw_15m:.3f}) 미충족 또는 지지선 이탈"
            return signal
            
        signal.state_15m = "SQUEEZE_DETECTED 🟢"

        # -------------------------------------------------------------
        # 2. [5분봉 상승 다이버전스 & 반전 검증 (Meso Divergence Reversal)]
        # -------------------------------------------------------------
        rsi_5m = calculate_rsi(df_5m['close'], config.RSI_PERIOD_5M)
        bb_up_5m, bb_mid_5m, bb_low_5m, _ = calculate_bollinger_bands(df_5m['close'], 20)
        
        # 다이버전스 탐색 (최근 12개 5분봉 내 저점 비교)
        lookback = config.DIVERGENCE_LOOKBACK_5M
        sub_price = df_5m['low'].iloc[-lookback:]
        sub_rsi = rsi_5m.iloc[-lookback:]
        
        # 최근 3봉 내 최저점과 그 이전 최저점 비교
        recent_low_idx = sub_price.iloc[-4:].idxmin()
        prev_low_idx = sub_price.iloc[:-4].idxmin()
        
        price_low_recent = sub_price.loc[recent_low_idx]
        price_low_prev = sub_price.loc[prev_low_idx]
        rsi_recent = sub_rsi.loc[recent_low_idx]
        rsi_prev = sub_rsi.loc[prev_low_idx]
        
        # 상승 다이버전스: 가격 저점은 하락/동등하나 RSI 저점은 상승
        is_bullish_div = (price_low_recent <= price_low_prev * 1.002) and (rsi_recent > rsi_prev + 1.0)
        
        # 또는 5분봉 볼린저 하단 터치 후 양봉 재진입 (Rejection)
        last_candle_5m = df_5m.iloc[-1]
        is_bb_rejection = (last_candle_5m['close'] > last_candle_5m['open']) and (last_candle_5m['low'] <= bb_low_5m.iloc[-1])
        
        is_5m_reversal = is_bullish_div or is_bb_rejection

        if not is_5m_reversal:
            signal.state_5m = f"WAITING_DIVERGENCE (RSI: {rsi_5m.iloc[-1]:.1f}, 5M 하단 지지 탐색)"
            signal.reason = "5분봉 상승 다이버전스 또는 밴드 하단 거부 캔들 미완성"
            return signal
            
        signal.state_5m = "REVERSAL_CONFIRMED 🟢"

        # -------------------------------------------------------------
        # 3. [3분봉 체결강도 V자 반등 & 틱 반전 트리거 (Micro Order Flow)]
        # -------------------------------------------------------------
        intensity_delta = realtime_intensity - self.prev_intensity_3m
        self.prev_intensity_3m = realtime_intensity
        
        last_high_3m = df_3m['high'].iloc[-2] if len(df_3m) >= 2 else current_price
        
        # 체결강도 110% 이상 + 직전 3분봉 고가 돌파
        is_3m_flow_triggered = (
            (realtime_intensity >= config.INTENSITY_MIN_3M) and
            (current_price >= last_high_3m)
        )
        
        stop_price = round(price_low_recent - 200, 0) # 직전 저점 -2틱(-200원)
        target_1 = round(current_price * (1.0 + config.TAKE_PROFIT_1_PCT / 100.0), 0)
        target_2 = round(current_price * (1.0 + config.TAKE_PROFIT_2_PCT / 100.0), 0)

        signal.metrics = {
            'price': current_price,
            '15m_bw': float(last_bw_15m),
            '15m_atr_pct': float(atr_pct),
            '5m_rsi': float(rsi_5m.iloc[-1]),
            'intensity': float(realtime_intensity),
            'swing_low': float(price_low_recent),
            'stop_loss': float(stop_price),
            'target_1': float(target_1)
        }

        if is_3m_flow_triggered:
            signal.state_3m = "TRIGGERED 🚀"
            signal.should_enter = True
            signal.suggested_price = current_price
            signal.stop_loss_price = stop_price
            signal.target_price = target_1
            signal.reason = (
                f"전략 2 조건 충족! [15M 스퀴즈 BW:{last_bw_15m:.3f}] -> [5M 상승 다이버전스/RSI {rsi_5m.iloc[-1]:.1f}] -> "
                f"[3M 틱반전 & 체결강도 {realtime_intensity:.1f}%]"
            )
        else:
            signal.state_3m = f"TRIGGER_WAIT (체결강도: {realtime_intensity:.1f}%, 직전고가: {last_high_3m:,.0f}원)"
            signal.reason = "3분봉 체결강도 및 직전고가 돌파 틱 대기"

        return signal
