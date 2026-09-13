"""
========================================================================================
📊 [STORAGE: TIMESERIES INDICATOR ENGINE & CANDLE AGGREGATOR]
Real-time 1M/3M/5M/15M Bar aggregation and vector math for ATR, BB, EMA, RSI, Envelope, MACD.
========================================================================================
"""

import math
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

class TimeseriesIndicatorEngine:
    """실시간 분봉 집계 및 기술적 지표 산출 엔진 (Pre-warm 지원)"""
    def __init__(self, code: str, stock_name: str, base_dir: str = r"D:\ANTIGRAVITY(자동매매)"):
        self.code = str(code).zfill(6)
        self.stock_name = stock_name
        self.base_dir = base_dir
        self.bars_1m: List[Dict] = []
        self.current_bar_1m: Optional[Dict] = None

        # 시작 즉시 로컬 3분봉 데이터로 캔들 엔진 예열 (Cold Start 방지)
        self.prewarm_from_csv()

    def prewarm_from_csv(self):
        """로컬 저장소의 3분봉 데이터를 읽어 메모리 캔들 엔진을 즉시 예열 (Cold Start 방어)"""
        import os
        import glob
        pattern = os.path.join(self.base_dir, "data", "종목데이터", "*", "3분봉", f"{self.code}_*_3M.csv")
        files = glob.glob(pattern)
        if not files:
            pattern = os.path.join(self.base_dir, "data", "종목데이터", "*", f"{self.code}_*.csv")
            files = glob.glob(pattern)

        if files:
            try:
                df = pd.read_csv(files[0], index_col=0)
                df.index = pd.to_datetime(df.index)
                df.sort_index(inplace=True)

                recent_df = df.tail(1500)
                prewarmed_bars = []
                for dt, row in recent_df.iterrows():
                    prewarmed_bars.append({
                        'time': dt,
                        'open': float(row.get('Open', row.get('open', 0))),
                        'high': float(row.get('High', row.get('high', 0))),
                        'low': float(row.get('Low', row.get('low', 0))),
                        'close': float(row.get('Close', row.get('close', 0))),
                        'volume': int(row.get('Volume', row.get('volume', 0))),
                        'intensity': 100.0
                    })
                self.bars_1m = prewarmed_bars
                print(f">> [TimeseriesEngine] 🔥 [{self.stock_name} {self.code}] 과거 {len(prewarmed_bars):,}개 캔들 메모리 예열(Pre-warm) 완료! (최종: {df.index[-1]})")
            except Exception as e:
                print(f">> [TimeseriesEngine] ⚠️ 예열 로드 중 오류: {e}")

    def add_tick(self, price: float, volume: int, intensity: float, timestr: str):
        now = datetime.now()
        minute_dt = now.replace(second=0, microsecond=0)

        if self.current_bar_1m is None or self.current_bar_1m['time'] != minute_dt:
            if self.current_bar_1m is not None:
                self.bars_1m.append(self.current_bar_1m)
                if len(self.bars_1m) > 1000:
                    self.bars_1m.pop(0)

            self.current_bar_1m = {
                'time': minute_dt,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume,
                'intensity': intensity
            }
        else:
            b = self.current_bar_1m
            b['high'] = max(b['high'], price)
            b['low'] = min(b['low'], price)
            b['close'] = price
            b['volume'] += volume
            b['intensity'] = intensity

    def get_df_1m(self) -> pd.DataFrame:
        data = list(self.bars_1m)
        if self.current_bar_1m:
            data.append(self.current_bar_1m)
        if not data:
            return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume', 'intensity'])
        df = pd.DataFrame(data)
        df.set_index('time', inplace=True)
        return df

    def resample_bars(self, interval_str: str) -> pd.DataFrame:
        df_1m = self.get_df_1m()
        if df_1m.empty:
            return pd.DataFrame()
        
        agg_rules = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'intensity': 'mean'
        }
        resampled = df_1m.resample(interval_str).agg(agg_rules).dropna()
        return resampled

    def get_3m_df(self) -> pd.DataFrame:
        return self.resample_bars('3min')

    def get_5m_df(self) -> pd.DataFrame:
        return self.resample_bars('5min')

    def get_15m_df(self) -> pd.DataFrame:
        return self.resample_bars('15min')

    @staticmethod
    def calc_ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    @staticmethod
    def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def calc_bollinger(series: pd.Series, period: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
        mid = series.rolling(period).mean()
        std = series.rolling(period).std()
        upper = mid + (std * num_std)
        lower = mid - (std * num_std)
        bandwidth = (upper - lower) / (mid + 1e-9)
        return {"upper": upper, "mid": mid, "lower": lower, "bandwidth": bandwidth}

    @staticmethod
    def calc_envelope(series: pd.Series, period: int = 20, rate_pct: float = 1.8) -> Dict[str, pd.Series]:
        mid = series.rolling(period).mean()
        upper = mid * (1.0 + rate_pct / 100.0)
        lower = mid * (1.0 - rate_pct / 100.0)
        return {"upper": upper, "mid": mid, "lower": lower}

    @staticmethod
    def calc_tenkan_sen(df: pd.DataFrame, period: int = 13) -> pd.Series:
        """일목균형표 전환선 (과거 period 봉의 최고가 + 최저가) / 2"""
        high_p = df['high'].rolling(window=period).max()
        low_p = df['low'].rolling(window=period).min()
        return (high_p + low_p) / 2.0

    @staticmethod
    def calc_rolling_vwap(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """20개 캔들 롤링 거래량가중평균가 (Rolling VWAP)"""
        cum_vol = df['volume'].rolling(window=period).sum()
        cum_val = (df['close'] * df['volume']).rolling(window=period).sum()
        return cum_val / (cum_vol + 1e-9)

    @staticmethod
    def calc_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        fast_ema = series.ewm(span=fast, adjust=False).mean()
        slow_ema = series.ewm(span=slow, adjust=False).mean()
        macd = fast_ema - slow_ema
        sig = macd.ewm(span=signal, adjust=False).mean()
        hist = macd - sig
        return {"macd": macd, "signal": sig, "hist": hist}

    @staticmethod
    def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df['high']
        low = df['low']
        close_prev = df['close'].shift(1)
        tr1 = high - low
        tr2 = (high - close_prev).abs()
        tr3 = (low - close_prev).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(period).mean()
