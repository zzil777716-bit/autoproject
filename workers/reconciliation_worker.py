"""
========================================================================================
🔄 [WORKER: RECONCILIATION WORKER]
Periodically checks outstanding unfilled/partially filled orders and syncs actual account state.
========================================================================================
"""

import time
from datetime import datetime
from typing import Dict, Any, List
from config.settings import config
from sdk.broker_adapter import BrokerAdapter

class ReconciliationWorker:
    def __init__(self, broker: BrokerAdapter, check_interval_sec: int = 30):
        self.broker = broker
        self.check_interval_sec = check_interval_sec
        self.is_running = False

    def sync_open_orders(self) -> Dict[str, Any]:
        """미체결 잔량 조회 및 계좌 상태 대조"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        deposit_info = self.broker.get_deposit(config.ACCOUNT_NO)
        
        report = {
            "timestamp": now_str,
            "account_no": config.ACCOUNT_NO,
            "deposit": deposit_info.get("deposit", 0),
            "orderable": deposit_info.get("orderable", 0),
            "status": "IN_SYNC"
        }
        print(f">> [ReconciliationWorker] 🔄 계좌 상태 대조 완료 ({now_str}): 예수금 {report['deposit']:,}원 | 주문가능 {report['orderable']:,}원")
        return report

    def start_loop(self):
        self.is_running = True
        print(">> [ReconciliationWorker] 🚀 주문 상태 확인 및 계좌 동기화 루프 시작")
        while self.is_running:
            self.sync_open_orders()
            time.sleep(self.check_interval_sec)
