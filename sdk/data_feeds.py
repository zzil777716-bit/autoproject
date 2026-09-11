"""
========================================================================================
📡 [STRATEGY SDK: DATA FEED ABSTRACTION]
Abstract DataFeed ensuring 100% code parity between Backtesting and Live Trading.
========================================================================================
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class DataFeed(ABC):
    """데이터 피드 표준 추상 클래스"""

    @abstractmethod
    def get_ohlcv(self, code: str, interval_min: int, limit: int = 100) -> pd.DataFrame:
        """지정 주기의 OHLCV 데이터프레임 반환"""
        pass

    @abstractmethod
    def get_realtime_price(self, code: str) -> float:
        """최신 현재가 반환"""
        pass

    @abstractmethod
    def get_realtime_intensity(self, code: str) -> float:
        """최신 체결강도 반환"""
        pass

class LiveDataFeed(DataFeed):
    """실시간 웹소켓/Active-X 수신 피드"""
    def __init__(self, candle_engine, current_price_getter, intensity_getter):
        self.candle_engine = candle_engine
        self._get_price = current_price_getter
        self._get_intensity = intensity_getter

    def get_ohlcv(self, code: str, interval_min: int, limit: int = 100) -> pd.DataFrame:
        if interval_min == 15:
            df = self.candle_engine.get_15m_df()
        elif interval_min == 5:
            df = self.candle_engine.get_5m_df()
        elif interval_min == 3:
            df = self.candle_engine.get_3m_df()
        else:
            df = self.candle_engine.get_df_1m()
        return df.tail(limit)

    def get_realtime_price(self, code: str) -> float:
        return self._get_price()

    def get_realtime_intensity(self, code: str) -> float:
        return self._get_intensity()

class BacktestDataFeed(DataFeed):
    """시계열DB/CSV 과거 데이터 재생 피드"""
    def __init__(self, df_15m: pd.DataFrame, df_5m: pd.DataFrame, df_3m: pd.DataFrame):
        self.df_15m = df_15m
        self.df_5m = df_5m
        self.df_3m = df_3m
        self.current_price = 0.0
        self.current_intensity = 100.0

    def get_ohlcv(self, code: str, interval_min: int, limit: int = 100) -> pd.DataFrame:
        if interval_min == 15: return self.df_15m.tail(limit)
        if interval_min == 5: return self.df_5m.tail(limit)
        if interval_min == 3: return self.df_3m.tail(limit)
        return pd.DataFrame()

    def get_realtime_price(self, code: str) -> float:
        return self.current_price

    def get_realtime_intensity(self, code: str) -> float:
        return self.current_intensity

class MultiTimeframeFeed:
    """멀티 타임프레임 (15M, 5M, 3M) 실시간 및 과거 시계열 관리 피드"""
    def __init__(self, code: str, base_dir: str = r"C:\Antigravity"):
        self.code = code
        self.base_dir = base_dir
        self.dfs: Dict[str, pd.DataFrame] = {
            "15m": pd.DataFrame(),
            "5m": pd.DataFrame(),
            "3m": pd.DataFrame()
        }

    def load_initial_history(self):
        """1개년 과거 분봉 시계열 로드"""
        from collectors.historical_collector import HistoricalDataCollector
        collector = HistoricalDataCollector(base_dir=self.base_dir)
        for tf in [15, 5, 3]:
            df = collector.load_historical_bars(self.code, tf)
            if not df.empty:
                self.dfs[f"{tf}m"] = df

    def update_tick(self, price: float, volume: int, current_time_str: str):
        """실시간 틱 반영"""
        pass

    def get_timeframe_dfs(self) -> Dict[str, pd.DataFrame]:
        return self.dfs
