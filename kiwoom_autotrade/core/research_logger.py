"""
Institutional Quant Research & Trade Journal Engine
Automatically collects:
1. Real-time Market & Indicator Snapshots (data lake for ML/Backtesting)
2. Detailed Trade Journal (Entry/Exit reason, MFE/MAE excursion analysis, PnL)
3. Signal Near-Miss / Filter Logs (for parameter sensitivity tuning)
4. Daily Quant Research Reports
5. Automatic Google Drive Sync (G:\내 드라이브\Antigravity)
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

from core.gdrive_sync import GDriveSync

class ResearchLogger:
    def __init__(self, code: str, stock_name: str, base_dir: str = "."):
        self.code = code
        self.stock_name = stock_name
        self.base_dir = base_dir
        self.research_dir = os.path.join(base_dir, "data", "research")
        os.makedirs(self.research_dir, exist_ok=True)
        
        self.db_path = os.path.join(self.research_dir, f"research_datalake_{code}.sqlite")
        self.trade_journal_db = os.path.join(self.research_dir, "trade_journal.sqlite")
        self.gdrive_sync = GDriveSync()
        self._init_databases()

    def _init_databases(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    code TEXT,
                    price REAL,
                    diff_rate REAL,
                    intensity REAL,
                    volume INTEGER,
                    state_15m TEXT,
                    state_5m TEXT,
                    state_3m TEXT,
                    indicators_json TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snap_time ON market_snapshots(timestamp)")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS signal_near_miss (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    code TEXT,
                    price REAL,
                    strategy_name TEXT,
                    dropped_stage TEXT,
                    reason TEXT,
                    metrics_json TEXT
                )
            """)

        with sqlite3.connect(self.trade_journal_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_journal (
                    trade_id TEXT PRIMARY KEY,
                    code TEXT,
                    stock_name TEXT,
                    strategy_name TEXT,
                    qty INTEGER,
                    entry_time TEXT,
                    entry_price REAL,
                    entry_reason TEXT,
                    entry_indicators_json TEXT,
                    exit_time TEXT,
                    exit_price REAL,
                    exit_reason TEXT,
                    holding_seconds REAL,
                    pnl_won REAL,
                    pnl_pct REAL,
                    mfe_pct REAL,
                    mae_pct REAL
                )
            """)

    def log_market_snapshot(
        self,
        now: datetime,
        price: float,
        diff_rate: float,
        intensity: float,
        volume: int,
        state_15m: str,
        state_5m: str,
        state_3m: str,
        indicators: Dict[str, Any]
    ):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO market_snapshots 
                    (timestamp, code, price, diff_rate, intensity, volume, state_15m, state_5m, state_3m, indicators_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    now.strftime('%Y-%m-%d %H:%M:%S'),
                    self.code,
                    price,
                    diff_rate,
                    intensity,
                    volume,
                    state_15m,
                    state_5m,
                    state_3m,
                    json.dumps(indicators, ensure_ascii=False)
                ))
        except Exception:
            pass

    def log_near_miss(self, now: datetime, price: float, strategy_name: str, stage: str, reason: str, metrics: Dict[str, Any]):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO signal_near_miss 
                    (timestamp, code, price, strategy_name, dropped_stage, reason, metrics_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    now.strftime('%Y-%m-%d %H:%M:%S'),
                    self.code,
                    price,
                    strategy_name,
                    stage,
                    reason,
                    json.dumps(metrics, ensure_ascii=False)
                ))
        except Exception:
            pass

    def log_trade_entry(
        self,
        trade_id: str,
        strategy_name: str,
        qty: int,
        entry_time: datetime,
        entry_price: float,
        reason: str,
        indicators: Dict[str, Any]
    ):
        try:
            with sqlite3.connect(self.trade_journal_db) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO trade_journal
                    (trade_id, code, stock_name, strategy_name, qty, entry_time, entry_price, entry_reason, entry_indicators_json,
                     exit_time, exit_price, exit_reason, holding_seconds, pnl_won, pnl_pct, mfe_pct, mae_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, 0, 0, 0, 0, 0)
                """, (
                    trade_id,
                    self.code,
                    self.stock_name,
                    strategy_name,
                    qty,
                    entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                    entry_price,
                    reason,
                    json.dumps(indicators, ensure_ascii=False)
                ))
            print(f">> [TradeJournal] 📝 매매 일지 등록 [진입]: ID({trade_id}) {self.stock_name} {entry_price:,.0f}원 ({qty}주)")
        except Exception as e:
            print(f">> [TradeJournal] 진입 기록 오류: {e}")

    def log_trade_exit(
        self,
        trade_id: str,
        exit_time: datetime,
        exit_price: float,
        exit_reason: str,
        holding_seconds: float,
        pnl_won: float,
        pnl_pct: float,
        mfe_pct: float,
        mae_pct: float
    ):
        try:
            with sqlite3.connect(self.trade_journal_db) as conn:
                conn.execute("""
                    UPDATE trade_journal
                    SET exit_time = ?, exit_price = ?, exit_reason = ?, holding_seconds = ?,
                        pnl_won = ?, pnl_pct = ?, mfe_pct = ?, mae_pct = ?
                    WHERE trade_id = ?
                """, (
                    exit_time.strftime('%Y-%m-%d %H:%M:%S'),
                    exit_price,
                    exit_reason,
                    holding_seconds,
                    pnl_won,
                    pnl_pct,
                    mfe_pct,
                    mae_pct,
                    trade_id
                ))
            print(f">> [TradeJournal] 📝 매매 일지 완료 [청산]: ID({trade_id}) 손익: {pnl_won:+,}원 ({pnl_pct:+.2f}%) | MFE:+{mfe_pct:.2f}% / MAE:{mae_pct:.2f}%")
            
            # Markdown 일일 매매 일지 파일 추가 및 구글 드라이브 클라우드 동기화
            self._append_markdown_journal(trade_id, exit_time, exit_price, exit_reason, pnl_won, pnl_pct, mfe_pct, mae_pct)
            self.gdrive_sync.sync_file(self.trade_journal_db, "research")
            self.gdrive_sync.sync_file(self.db_path, "research")
        except Exception as e:
            print(f">> [TradeJournal] 청산 기록 오류: {e}")

    def _append_markdown_journal(
        self,
        trade_id: str,
        exit_time: datetime,
        exit_price: float,
        exit_reason: str,
        pnl_won: float,
        pnl_pct: float,
        mfe_pct: float,
        mae_pct: float
    ):
        date_str = exit_time.strftime('%Y-%m-%d')
        md_file = os.path.join(self.research_dir, f"trade_log_{date_str}.md")
        
        is_new = not os.path.exists(md_file)
        with open(md_file, "a", encoding="utf-8") as f:
            if is_new:
                f.write(f"# 📊 [{date_str}] 자동매매 실전 매매 일지 & 정밀 분석 리포트\n\n")
                f.write("| 매매ID | 종목 | 청산시각 | 손익금 | 수익률 | 청산사유 | MFE(최대수익) | MAE(최대손실) |\n")
                f.write("| :--- | :--- | :--- | :---: | :---: | :--- | :---: | :---: |\n")
            f.write(f"| `{trade_id}` | **{self.stock_name}** | {exit_time.strftime('%H:%M:%S')} | **{pnl_won:+,}원** | `{pnl_pct:+.2f}%` | {exit_reason} | `+{mfe_pct:.2f}%` | `{mae_pct:.2f}%` |\n")
            
        # 구글 드라이브 동기화
        self.gdrive_sync.sync_file(md_file, "research")
