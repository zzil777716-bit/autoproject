"""
Time-Series Storage & Fast Resampling Engine for SK Hynix (000660)
Manages historical 3m, 5m, 15m and 1m minute bars using SQLite, CSV, and Parquet.
"""

import os
import sqlite3
from datetime import datetime
import pandas as pd

class TimeSeriesDB:
    def __init__(self, db_path: str = "data/hynix_market_data.sqlite"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            for tf in ["1m", "3m", "5m", "15m"]:
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS bars_{tf} (
                        code TEXT,
                        timestamp TEXT,
                        open REAL,
                        high REAL,
                        low REAL,
                        close REAL,
                        volume INTEGER,
                        PRIMARY KEY (code, timestamp)
                    )
                """)
                conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{tf}_code_time ON bars_{tf}(code, timestamp)")

    def save_timeframe_bars(self, code: str, timeframe: str, df_bars: pd.DataFrame):
        if df_bars.empty:
            return
            
        tf_name = timeframe.lower().replace("min", "m").replace("t", "m")
        table_name = f"bars_{tf_name}"
        
        records = []
        for ts, row in df_bars.iterrows():
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S') if isinstance(ts, datetime) else str(ts)
            records.append((
                code,
                ts_str,
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                int(row['volume'])
            ))
            
        # 1. SQLite 저장
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(f"""
                INSERT OR REPLACE INTO {table_name} (code, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, records)
            
        # 2. CSV 및 Parquet 저장
        os.makedirs("data", exist_ok=True)
        csv_path = f"data/{code}_{tf_name}.csv"
        parquet_path = f"data/{code}_{tf_name}.parquet"
        
        df_bars.to_csv(csv_path, encoding='utf-8-sig')
        try:
            df_bars.to_parquet(parquet_path)
        except Exception:
            pass
            
        print(f">> [TimeSeriesDB] ✅ SK하이닉스({code}) {tf_name} 데이터 저장 완료: 총 {len(df_bars):,d}개 봉 -> [DB, CSV, Parquet]")

    def load_timeframe_bars(self, code: str, timeframe: str, start_date: str = "2025-08-01") -> pd.DataFrame:
        tf_name = timeframe.lower().replace("min", "m").replace("t", "m")
        table_name = f"bars_{tf_name}"
        
        with sqlite3.connect(self.db_path) as conn:
            query = f"""
                SELECT timestamp, open, high, low, close, volume
                FROM {table_name}
                WHERE code = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """
            df = pd.read_sql_query(query, conn, params=(code, start_date))
            
        if df.empty:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        return df

    def save_bars(self, code: str, df_bars: pd.DataFrame):
        self.save_timeframe_bars(code, "1m", df_bars)

    def load_recent_bars(self, code: str, limit: int = 500) -> pd.DataFrame:
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM bars_1m
                WHERE code = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(code, limit))
            
        if df.empty:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.sort_values('timestamp', inplace=True)
        df.set_index('timestamp', inplace=True)
        return df
