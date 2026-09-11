"""
========================================================================================
📥 [COLLECTOR: HISTORICAL TIMESERIES COLLECTOR]
Historical multi-timeframe candle data collector for Samsung Electronics and SK Hynix.
========================================================================================
"""

import os
import pandas as pd
from typing import Optional

class HistoricalDataCollector:
    def __init__(self, base_dir: str = r"C:\Antigravity"):
        self.base_dir = base_dir
        self.timeseries_dir = os.path.join(base_dir, "data", "timeseries")
        os.makedirs(self.timeseries_dir, exist_ok=True)

    def load_historical_bars(self, code: str, interval_min: int) -> pd.DataFrame:
        """기존 수집된 1개년 분봉 데이터프레임 로드"""
        filename = f"{code}_{interval_min}m.csv"
        file_path = os.path.join(self.timeseries_dir, filename)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, parse_dates=['time'])
            df.set_index('time', inplace=True)
            return df
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume', 'intensity'])
