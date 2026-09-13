"""
========================================================================================
⚙️ [UNIFIED SYSTEM CONFIGURATION]
Enterprise-grade modular settings for Antigravity Multi-Bot Trading System.
========================================================================================
"""

import os
from dataclasses import dataclass

@dataclass
class SystemConfig:
    # 1. 시스템 식별자 및 기본 경로
    SYSTEM_NAME: str = "Antigravity Multi-Bot Trading System"
    BASE_DIR: str = r"D:\ANTIGRAVITY(자동매매)"
    GDRIVE_DIR: str = r"G:\내 드라이브\Antigravity"

    # 2. 키움증권 계좌 및 모의투자 설정
    ACCOUNT_NO: str = "8133507611"
    USER_NAME: str = "김홍균"
    USER_ID: str = "zzil77"
    IS_MOCK_TRADING: bool = True
    DEFAULT_TRADE_QTY: int = 1  # 1주 고정 주문

    # 3. 거래 대상 종목
    SAMSUNG_CODE: str = "005930"
    SAMSUNG_NAME: str = "삼성전자"
    HYNIX_CODE: str = "000660"
    HYNIX_NAME: str = "SK하이닉스"

    # 4. 키움 OpenAPI+ 화면 번호
    SCREEN_NO_REAL: str = "1000"
    SCREEN_NO_ORDER: str = "2000"
    SCREEN_NO_TR: str = "3000"

    # 5. 리스크 파라미터 (1주 기본 - MFE 실증형 하이브리드 세팅)
    STOP_LOSS_PCT: float = -0.90      # 기본 손절선 (-0.90%)
    TAKE_PROFIT_1_PCT: float = 1.50   # 1차 익절선 (+1.50%) -> 본절 스탑(+0.10%) 전환
    TAKE_PROFIT_2_PCT: float = 2.80   # 2차 익절선 (+2.80%) -> 트레일링 스탑
    TRAILING_GAP_PCT: float = 0.50    # 고점 대비 트레일링 스탑 마진 (0.50%)

    MAX_DAILY_TRADES: int = 3
    MAX_DAILY_LOSS_WON: int = 500_000

    # 6. 대체거래소 (NXT / Nextrade) 및 SOR (스마트 최선주문집행) 설정
    NXT_ENABLED: bool = True
    ORDER_ROUTING_MODE: str = "SOR"   # SOR (통합최선집행-추천) | KRX (한국거래소) | NXT (넥스트레이드)
    MORNING_TRIGGER_TIME: str = "07:50"  # NXT 프리마켓(08:00) 대비 10분 전 기상 알림
    
    # 7. 텔레그램 알림 설정
    TELEGRAM_ENABLED: bool = True
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "7488339498:AAGxExampleTokenForMockTest")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "123456789")

config = SystemConfig()
