"""
========================================================================================
🗄️ [STORAGE: QUANT RESEARCH DATA LAKE & PARTITIONED SQLITE WITH WAL]
Multi-process safe SQLite with WAL (Write-Ahead Logging), 5s busy timeout, and strategy partitioning.
========================================================================================
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

class QuantDataLake:
    """
    멀티 프로세스 안전 SQLite 데이터 레이크:
    1. PRAGMA journal_mode=WAL (동시 읽기/쓰기 락 경합 방지)
    2. PRAGMA busy_timeout=5000 (동시 접근 시 5초 대기 후 재시도)
    3. 종목/전략별 파일 파티셔닝 지원 (trade_journal_{code}.sqlite)
    """
    def __init__(self, base_dir: str = r"D:\ANTIGRAVITY(자동매매)", partition_key: Optional[str] = None):
        self.base_dir = base_dir
        self.research_dir = os.path.join(base_dir, "data", "research")
        os.makedirs(self.research_dir, exist_ok=True)
        
        self.partition_key = partition_key
        if partition_key:
            self.db_name = f"trade_journal_{partition_key}.sqlite"
        else:
            self.db_name = "trade_journal.sqlite"

        self.db_path = os.path.join(self.research_dir, self.db_name)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. 매매 저널 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    strategy_name TEXT,
                    code TEXT,
                    stock_name TEXT,
                    side TEXT,
                    price REAL,
                    qty INTEGER,
                    pnl_won REAL,
                    pnl_pct REAL,
                    mfe_pct REAL,
                    mae_pct REAL,
                    hold_time_seconds INTEGER,
                    reason TEXT
                )
            """)
            # 2. 5초 스냅샷 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_snapshots_5s (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    code TEXT,
                    price REAL,
                    volume INTEGER,
                    intensity REAL,
                    bid_depth_ratio REAL
                )
            """)
            conn.commit()

    def record_trade(
        self,
        strategy_name: str,
        code: str,
        stock_name: str,
        side: str,
        price: float,
        qty: int,
        pnl_won: float,
        pnl_pct: float,
        mfe_pct: float,
        mae_pct: float,
        hold_time_seconds: int,
        reason: str
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trade_journal (
                    timestamp, strategy_name, code, stock_name, side, price, qty,
                    pnl_won, pnl_pct, mfe_pct, mae_pct, hold_time_seconds, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                strategy_name, code, stock_name, side, price, qty,
                pnl_won, pnl_pct, mfe_pct, mae_pct, hold_time_seconds, reason
            ))
            conn.commit()

    def record_snapshot(self, code: str, price: float, volume: int, intensity: float, bid_depth_ratio: float = 1.0):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO market_snapshots_5s (timestamp, code, price, volume, intensity, bid_depth_ratio)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), code, price, volume, intensity, bid_depth_ratio))
            conn.commit()

    def query_recent_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """읽기 전용 쿼리 (WAL 모드로 쓰기 작업 방해 없음)"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trade_journal ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
