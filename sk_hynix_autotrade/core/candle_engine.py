"""
Candle Resampling & Realtime Aggregation Engine for SK Hynix (000660)
Synthesizes 1M, 3M, 5M, 15M candles from incoming tick streams.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

class CandleEngine:
    def __init__(self, code: str = "000660"):
        self.code = code
        self.raw_1m_bars: List[Dict] = []
        self.current_1m_bar: Optional[Dict] = None
        self.current_minute: Optional[datetime] = None

    def preload_historical_bars(self, df_bars: pd.DataFrame):
        """과거 분봉 데이터를 엔진에 초기 적재"""
        if df_bars.empty:
            return
            
        records = []
        for ts, row in df_bars.iterrows():
            records.append({
                'timestamp': ts if isinstance(ts, datetime) else pd.to_datetime(ts),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            })
        self.raw_1m_bars = records
        if records:
            last = records[-1]
            self.current_minute = last['timestamp'].replace(second=0, microsecond=0)

    def on_tick(self, timestamp: datetime, price: float, volume: int) -> bool:
        """새로운 틱 데이터 수신 시 1분봉 합성. 1분봉 마감 시 True 반환."""
        bar_minute = timestamp.replace(second=0, microsecond=0)
        new_bar_closed = False
        
        if self.current_minute is None:
            self.current_minute = bar_minute
            self.current_1m_bar = {
                'timestamp': bar_minute,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume
            }
        elif bar_minute > self.current_minute:
            if self.current_1m_bar:
                self.raw_1m_bars.append(self.current_1m_bar)
                if len(self.raw_1m_bars) > 1000:
                    self.raw_1m_bars.pop(0)
                new_bar_closed = True
                
            self.current_minute = bar_minute
            self.current_1m_bar = {
                'timestamp': bar_minute,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume
            }
        else:
            if self.current_1m_bar:
                self.current_1m_bar['high'] = max(self.current_1m_bar['high'], price)
                self.current_1m_bar['low'] = min(self.current_1m_bar['low'], price)
                self.current_1m_bar['close'] = price
                self.current_1m_bar['volume'] += volume
                
        return new_bar_closed

    def get_df_1m(self) -> pd.DataFrame:
        bars = list(self.raw_1m_bars)
        if self.current_1m_bar:
            bars.append(self.current_1m_bar)
        if not bars:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            
        df = pd.DataFrame(bars)
        df.drop_duplicates(subset=['timestamp'], inplace=True)
        df.set_index('timestamp', inplace=True)
        return df

    def resample(self, rule: str) -> pd.DataFrame:
        df_1m = self.get_df_1m()
        if df_1m.empty:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            
        resampled = df_1m.resample(rule, label='right', closed='right').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        return resampled

    def get_3m_df(self) -> pd.DataFrame:
        return self.resample('3T')

    def get_5m_df(self) -> pd.DataFrame:
        return self.resample('5T')

    def get_15m_df(self) -> pd.DataFrame:
        return self.resample('15T')
