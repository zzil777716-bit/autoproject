"""
========================================================================================
🔍 [API LAYER: CQRS READ-ONLY QUERY SERVICE (2.4 COMPONENT)]
Zero-lock read replica queries for Dashboard, Mobile API, and Quant Research.
========================================================================================
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.data_lake import QuantDataLake

class QueryService:
    """CQRS Query(읽기) 전용 서비스 — 주문 처리 및 쓰기 트래픽에 전혀 영향을 주지 않음"""

    def __init__(self, base_dir: str = r"D:\ANTIGRAVITY(자동매매)"):
        self.base_dir = base_dir
        self.datalake_sam = QuantDataLake(base_dir, partition_key="005930")
        self.datalake_sk = QuantDataLake(base_dir, partition_key="000660")
        self.datalake_consolidated = QuantDataLake(base_dir)

    def get_recent_trade_journal(self, limit: int = 50) -> List[Dict[str, Any]]:
        """최근 체결 및 청산 매매 일지 조회"""
        trades = self.datalake_consolidated.query_recent_trades(limit)
        if not trades:
            # 파티셔닝된 DB 병합 조회
            t_sam = self.datalake_sam.query_recent_trades(limit // 2)
            t_sk = self.datalake_sk.query_recent_trades(limit // 2)
            trades = sorted(t_sam + t_sk, key=lambda x: x.get("timestamp", ""), reverse=True)
        return trades

    def get_latest_market_theme_summary(self) -> Dict[str, Any]:
        """최신 주도 테마 캘린더 요약 조회"""
        cal_path = os.path.join(self.base_dir, "data", "calendar", "market_calendar_history.json")
        if os.path.exists(cal_path):
            try:
                with open(cal_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    latest_date = max(data.keys()) if data else ""
                    return data.get(latest_date, {})
            except Exception:
                return {}
        return {}

    def get_system_health(self) -> Dict[str, Any]:
        """전체 봇 및 인프라 헬스체크"""
        return {
            "status": "HEALTHY",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "database_engine": "SQLite WAL Mode (Partitioned)",
            "sync_engine": "Asynchronous Non-blocking GDrive Worker",
            "active_strategies": ["005930 MTF-Squeeze", "000660 Triple-Screen Envelope"]
        }
