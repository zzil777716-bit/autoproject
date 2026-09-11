"""
Technical Indicators Engine for SK Hynix (000660)
Implements Alexander Elder's Triple-Screen Indicators & Buja Company Employee Envelope/EMA Pullback.
"""

from typing import Tuple
import pandas as pd
import numpy as np

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """지수이동평균 (EMA)"""
    return series.ewm(span=period, adjust=False).mean()

def calculate_bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0):
    """볼린저 밴드 (Upper, Middle, Lower, Bandwidth)"""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    bandwidth = (upper - lower) / middle.replace(0, np.nan)
    return upper, middle, lower, bandwidth

def calculate_envelope(series: pd.Series, period: int = 20, percent: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    엔벨로프(Envelope) 지표:
    - 중심선(Middle): SMA(period)
    - 상단선(Upper) : Middle * (1 + percent / 100)
    - 하단선(Lower) : Middle * (1 - percent / 100)
    """
    mid = series.rolling(window=period).mean()
    upper = mid * (1.0 + percent / 100.0)
    lower = mid * (1.0 - percent / 100.0)
    return upper, mid, lower


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD, Signal, Histogram"""
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd = ema_fast - ema_slow
    sig = calculate_ema(macd, signal)
    hist = macd - sig
    return macd, sig, hist

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """당일 기준 누적 거래량가중평균가 (VWAP)"""
    tp = (df['high'] + df['low'] + df['close']) / 3.0
    tp_vol = tp * df['volume']
    
    if isinstance(df.index, pd.DatetimeIndex):
        dates = df.index.date
        cum_tp_vol = tp_vol.groupby(dates).cumsum()
        cum_vol = df['volume'].groupby(dates).cumsum()
    else:
        cum_tp_vol = tp_vol.cumsum()
        cum_vol = df['volume'].cumsum()
        
    vwap = cum_tp_vol / cum_vol.replace(0, np.nan)
    return vwap.ffill()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """상대강도지수 (RSI)"""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (ATR)"""
    high = df['high']
    low = df['low']
    close_prev = df['close'].shift(1)
    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean().bfill()

def calculate_rvol(volume_series: pd.Series, lookback: int = 20) -> pd.Series:
    """상대거래량 (RVOL)"""
    avg_vol = volume_series.rolling(window=lookback).mean()
    rvol = volume_series / avg_vol.replace(0, np.nan)
    return rvol.fillna(1.0)
