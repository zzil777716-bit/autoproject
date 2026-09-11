"""
========================================================================================
🔌 [STRATEGY SDK: BROKER ADAPTER INTERFACE]
Abstract base class defining broker interaction (Kiwoom, Korea Investment, Mock)
========================================================================================
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class BrokerAdapter(ABC):
    """증권사 브로커 어댑터 표준 인터페이스"""

    @abstractmethod
    def login(self) -> bool:
        """증권사 API 로그인"""
        pass

    @abstractmethod
    def get_deposit(self, account_no: str) -> Dict[str, Any]:
        """예수금 및 주문 가능 금액 조회"""
        pass

    @abstractmethod
    def get_stock_info(self, code: str) -> Dict[str, Any]:
        """종목 기본 시세 및 등락률 조회"""
        pass

    @abstractmethod
    def send_order(
        self,
        rq_name: str,
        screen_no: str,
        acc_no: str,
        order_type: int,  # 1:신규매수, 2:신규매도
        code: str,
        qty: int,
        price: int,
        hoga_type: str    # "00":지정가, "03":시장가
    ) -> int:
        """주문 전송"""
        pass

    @abstractmethod
    def subscribe_realtime(self, screen_no: str, code: str, fids: str):
        """실시간 시세 등록"""
        pass
