"""
========================================================================================
📬 [EVENTS & MESSAGE BUS LAYER: TRANSACTIONAL OUTBOX PATTERN]
Decouples high-frequency tick events (In-Memory) from critical financial events
(OrderCommand, TradeFilled, RiskAlert) with durable SQLite Transactional Outbox persistence.
========================================================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Callable, Any, Optional
import json
import os
import sqlite3
import threading

@dataclass
class Event:
    event_type: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MarketTickEvent(Event):
    event_type: str = "MARKET_TICK"
    code: str = ""
    price: float = 0.0
    volume: int = 0
    intensity: float = 100.0
    timestr: str = ""

@dataclass
class OrderCommandEvent(Event):
    event_type: str = "ORDER_COMMAND"
    code: str = ""
    side: str = "BUY"  # BUY / SELL
    qty: int = 1
    price: float = 0.0
    strategy_name: str = ""
    reason: str = ""

@dataclass
class TradeFilledEvent(Event):
    event_type: str = "TRADE_FILLED"
    order_no: str = ""
    code: str = ""
    side: str = ""
    qty: int = 1
    price: float = 0.0
    pnl_won: float = 0.0
    pnl_pct: float = 0.0
    mfe_pct: float = 0.0
    mae_pct: float = 0.0
    hold_time_seconds: int = 0
    reason: str = ""

@dataclass
class RiskAlertEvent(Event):
    event_type: str = "RISK_ALERT"
    rule_id: str = ""
    message: str = ""
    action: str = ""

class EventBus(ABC):
    """메시지 브로커 / 이벤트 버스 추상 인터페이스"""

    @abstractmethod
    def publish(self, topic: str, event: Event):
        pass

    @abstractmethod
    def publish_critical(self, topic: str, event: Event) -> int:
        pass

    @abstractmethod
    def subscribe(self, topic: str, handler: Callable[[Event], None]):
        pass

class OutboxEventBus(EventBus):
    """
    Transactional Outbox 기반 이벤트 버스:
    1. MarketTickEvent: 제로 레이턴시 인메모리 발행 (유실 무방, 속도 최우선)
    2. OrderCommand / TradeFilled / RiskAlert: SQLite outbox에 먼저 'PENDING'으로 기록 후 발행 (장애 복구 보장)
    3. 프로세스 재기동 시 replay_unprocessed_events()로 누락 이벤트 자동 복원
    """
    def __init__(self, db_dir: str = r"C:\Antigravity\data\research"):
        self.db_dir = db_dir
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "event_outbox.sqlite")
        
        self._handlers: Dict[str, List[Callable[[Event], None]]] = {}
        self._lock = threading.Lock()
        self._init_outbox_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_outbox_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    event_type TEXT,
                    payload_json TEXT,
                    status TEXT DEFAULT 'PENDING',
                    created_at TEXT,
                    processed_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS global_system_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()

    def subscribe(self, topic: str, handler: Callable[[Event], None]):
        with self._lock:
            if topic not in self._handlers:
                self._handlers[topic] = []
            self._handlers[topic].append(handler)

    def publish(self, topic: str, event: Event):
        """[일반 시세 틱용] 인메모리 직통 고속 발행"""
        self._dispatch_in_memory(topic, event)

    def publish_critical(self, topic: str, event: Event) -> int:
        """
        [금전 관련 중요 이벤트용: 주문/체결/킬스위치]
        Transactional Outbox 패턴: 발행 "직전"에 SQLite에 PENDING 상태로 먼저 기록
        """
        event_dict = asdict(event) if hasattr(event, "__dataclass_fields__") else event.__dict__
        payload_json = json.dumps(event_dict, ensure_ascii=False)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        outbox_id = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO event_outbox (topic, event_type, payload_json, status, created_at)
                VALUES (?, ?, ?, 'PENDING', ?)
            """, (topic, event.event_type, payload_json, now_str))
            outbox_id = cursor.lastrowid
            
            # 리스크 킬스위치 발생 시 글로벌 상태 테이블에 즉시 기록 (JIT 풀 체크용)
            if event.event_type == "RISK_ALERT" and getattr(event, "action", "") == "HALT_ALL_STRATEGIES":
                cursor.execute("""
                    INSERT OR REPLACE INTO global_system_state (key, value, updated_at)
                    VALUES ('IS_HALTED', 'TRUE', ?)
                """, (now_str,))
            conn.commit()

        # 인메모리 발행
        self._dispatch_in_memory(topic, event)

        # 처리 완료 상태 갱신
        self.mark_outbox_processed(outbox_id)
        return outbox_id

    def mark_outbox_processed(self, outbox_id: int):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE event_outbox SET status='PROCESSED', processed_at=? WHERE id=?
            """, (now_str, outbox_id))
            conn.commit()

    def _dispatch_in_memory(self, topic: str, event: Event):
        handlers = []
        with self._lock:
            if topic in self._handlers:
                handlers = list(self._handlers[topic])
            if "*" in self._handlers:
                handlers.extend(self._handlers["*"])

        for h in handlers:
            try:
                h(event)
            except Exception as e:
                print(f">> [OutboxEventBus] 이벤트 핸들러 처리 오류 ({topic}): {e}")

    def replay_unprocessed_events(self) -> int:
        """프로세스 재시작 시 미처리(PENDING) 이벤트 자동 재생 및 복구"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM event_outbox WHERE status='PENDING' ORDER BY id ASC")
            pending_rows = cursor.fetchall()

        replayed_count = len(pending_rows)
        if replayed_count > 0:
            print(f">> [OutboxEventBus] 🔄 미처리 이벤트 {replayed_count}건 감지 -> 복구 재생(Replay) 시작...")
            for row in pending_rows:
                topic = row["topic"]
                event_type = row["event_type"]
                payload = json.loads(row["payload_json"])

                # 이벤트 역직렬화
                if event_type == "ORDER_COMMAND":
                    event = OrderCommandEvent(**payload)
                elif event_type == "TRADE_FILLED":
                    event = TradeFilledEvent(**payload)
                elif event_type == "RISK_ALERT":
                    event = RiskAlertEvent(**payload)
                else:
                    event = Event(**payload)

                self._dispatch_in_memory(topic, event)
                self.mark_outbox_processed(row["id"])
            print(f">> [OutboxEventBus] ✅ {replayed_count}건의 미처리 이벤트 복구 완료!")
        return replayed_count

    def check_global_halt_state(self) -> bool:
        """[JIT 풀 체크용] SQLite 상태 테이블에서 직접 킬스위치 상태 조회"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM global_system_state WHERE key='IS_HALTED'")
                row = cursor.fetchone()
                if row and row[0] == "TRUE":
                    return True
        except Exception:
            pass
        return False

    def reset_global_halt_state(self):
        """킬스위치 상태 초기화 (테스트 및 장 시작 리셋용)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM global_system_state WHERE key='IS_HALTED'")
                conn.commit()
        except Exception:
            pass

# 싱글톤 글로벌 인스턴스
global_event_bus = OutboxEventBus()
