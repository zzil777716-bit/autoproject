"""
Real-time tick aggregator & dynamic rolling candle generator.
Converts streaming tick data into 1m, 3m, 5m, and 15m OHLCV bars.
"""

from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

class CandleEngine:
    def __init__(self, code: str = "005930"):
        self.code = code
        self.current_1m_bar: Optional[Dict] = None
        self.bars_1m: List[Dict] = []
        self.max_bars_history: int = 500
        
    def on_tick(self, timestamp: datetime, price: float, volume: int) -> bool:
        """
        새로운 틱 데이터를 수신하여 1분봉으로 집계.
        새로운 1분봉이 완성되면 True 반환.
        """
        minute_bucket = timestamp.replace(second=0, microsecond=0)
        is_new_bar_closed = False
        
        if self.current_1m_bar is None:
            self.current_1m_bar = {
                'timestamp': minute_bucket,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume
            }
        elif self.current_1m_bar['timestamp'] == minute_bucket:
            # 동일한 1분 내 틱 업데이트
            self.current_1m_bar['high'] = max(self.current_1m_bar['high'], price)
            self.current_1m_bar['low'] = min(self.current_1m_bar['low'], price)
            self.current_1m_bar['close'] = price
            self.current_1m_bar['volume'] += volume
        else:
            # 이전 1분봉 마감 및 저장
            self.bars_1m.append(self.current_1m_bar.copy())
            if len(self.bars_1m) > self.max_bars_history:
                self.bars_1m.pop(0)
            is_new_bar_closed = True
            
            # 새로운 1분봉 시작
            self.current_1m_bar = {
                'timestamp': minute_bucket,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume
            }
            
        return is_new_bar_closed

    def get_df_1m(self) -> pd.DataFrame:
        """현재 진행 중인 봉까지 포함된 1분봉 DataFrame 반환"""
        all_bars = list(self.bars_1m)
        if self.current_1m_bar:
            all_bars.append(self.current_1m_bar)
        if not all_bars:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
        df = pd.DataFrame(all_bars)
        df.set_index('timestamp', inplace=True)
        return df

    def get_resampled_df(self, timeframe: str) -> pd.DataFrame:
        """
        1분봉 데이터를 기반으로 타임프레임별(3T, 5T, 15T) OHLCV 리샘플링.
        timeframe 예시: '3min' / '3T', '5min' / '5T', '15min' / '15T'
        """
        df_1m = self.get_df_1m()
        if df_1m.empty:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            
        resampled = df_1m.resample(timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        return resampled

    def get_15m_df(self) -> pd.DataFrame:
        return self.get_resampled_df('15min')

    def get_5m_df(self) -> pd.DataFrame:
        return self.get_resampled_df('5min')

    def get_3m_df(self) -> pd.DataFrame:
        return self.get_resampled_df('3min')

    def preload_historical_bars(self, df_history: pd.DataFrame):
        """초기 기동 시 과거 분봉 데이터 프리로드"""
        if df_history.empty:
            return
        records = df_history.reset_index().to_dict('records')
        self.bars_1m = records[-self.max_bars_history:]
