"""
Technical indicators calculation engine for Multi-Timeframe Strategy.
Supports fast rolling & vectorized calculations using Pandas and NumPy.
"""

import numpy as np
import pandas as pd

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """지수이동평균 (EMA)"""
    return series.ewm(span=period, adjust=False).mean()

def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """단순이동평균 (SMA)"""
    return series.rolling(window=period).mean()

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """당일 거래량가중평균 (Volume Weighted Average Price)"""
    typical_price = (df['high'] + df['low'] + df['close']) / 3.0
    cum_pv = (typical_price * df['volume']).cumsum()
    cum_vol = df['volume'].cumsum()
    return cum_pv / cum_vol.replace(0, np.nan)

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """상대강도지수 (RSI)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def calculate_bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0):
    """볼린저 밴드 (Upper, Middle, Lower, Bandwidth)"""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    bandwidth = (upper - lower) / middle.replace(0, np.nan)
    return upper, middle, lower, bandwidth

def calculate_envelope(series: pd.Series, period: int = 20, percent: float = 2.0):
    """엔벨로프 (Envelope: Upper, Middle, Lower)"""
    mid = series.rolling(window=period).mean()
    upper = mid * (1.0 + percent / 100.0)
    lower = mid * (1.0 - percent / 100.0)
    return upper, mid, lower

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD, Signal, Histogram"""
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd = ema_fast - ema_slow
    sig = calculate_ema(macd, signal)
    hist = macd - sig
    return macd, sig, hist


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """평균진폭 (Average True Range)"""
    high = df['high']
    low = df['low']
    close_prev = df['close'].shift(1)
    
    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """평균방향성지수 (ADX)"""
    high = df['high']
    low = df['low']
    
    up_move = high.diff()
    down_move = -low.diff()
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    atr = calculate_atr(df, period)
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(period).mean() / atr.replace(0, np.nan))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(period).mean() / atr.replace(0, np.nan))
    
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    adx = dx.rolling(period).mean()
    return adx.fillna(0)

def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
    """슈퍼트렌드 지표 (SuperTrend, Direction)"""
    atr = calculate_atr(df, period)
    hl2 = (df['high'] + df['low']) / 2.0
    
    upper_basic = hl2 + (multiplier * atr)
    lower_basic = hl2 - (multiplier * atr)
    
    upper_band = pd.Series(index=df.index, dtype=float)
    lower_band = pd.Series(index=df.index, dtype=float)
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)  # 1: Bullish, -1: Bearish
    
    for i in range(len(df)):
        if i == 0:
            upper_band.iloc[i] = upper_basic.iloc[i]
            lower_band.iloc[i] = lower_basic.iloc[i]
            supertrend.iloc[i] = upper_band.iloc[i]
            direction.iloc[i] = -1
            continue
            
        # Upper Band
        if upper_basic.iloc[i] < upper_band.iloc[i-1] or df['close'].iloc[i-1] > upper_band.iloc[i-1]:
            upper_band.iloc[i] = upper_basic.iloc[i]
        else:
            upper_band.iloc[i] = upper_band.iloc[i-1]
            
        # Lower Band
        if lower_basic.iloc[i] > lower_band.iloc[i-1] or df['close'].iloc[i-1] < lower_band.iloc[i-1]:
            lower_band.iloc[i] = lower_basic.iloc[i]
        else:
            lower_band.iloc[i] = lower_band.iloc[i-1]
            
        # SuperTrend & Direction
        if direction.iloc[i-1] == -1 and df['close'].iloc[i] > upper_band.iloc[i]:
            direction.iloc[i] = 1
            supertrend.iloc[i] = lower_band.iloc[i]
        elif direction.iloc[i-1] == 1 and df['close'].iloc[i] < lower_band.iloc[i]:
            direction.iloc[i] = -1
            supertrend.iloc[i] = upper_band.iloc[i]
        else:
            direction.iloc[i] = direction.iloc[i-1]
            supertrend.iloc[i] = lower_band.iloc[i] if direction.iloc[i] == 1 else upper_band.iloc[i]
            
    return supertrend, direction

def calculate_rvol(series_vol: pd.Series, lookback_period: int = 20) -> float:
    """시간대별 상대 거래량 (Relative Volume)"""
    if len(series_vol) < lookback_period + 1:
        return 1.0
    avg_vol = series_vol.iloc[-lookback_period-1:-1].mean()
    if avg_vol == 0:
        return 1.0
    return float(series_vol.iloc[-1] / avg_vol)
