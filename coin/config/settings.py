# -*- coding: utf-8 -*-
"""
========================================================================================
🪙 [COIN TRADING CONFIGURATION: UPBIT & BITHUMB]
Dual exchange credentials and parameters.
========================================================================================
"""

import os
from dataclasses import dataclass
from pathlib import Path

# C:\Antigravity\coin\coin_api_key.env 자동 로드
def load_env_file():
    env_paths = [
        Path(r"C:\Antigravity\coin\coin_api_key.env"),
        Path(r"C:\Antigravity\coin\coin_api_key.env.txt")
    ]
    for p in env_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip("'").strip('"')

load_env_file()

@dataclass
class CoinConfig:
    SYSTEM_NAME: str = "Antigravity Crypto Trading Engine"
    BASE_DIR: str = r"C:\Antigravity\coin"
    
    # 기본 거래소 선택: 'UPBIT' 또는 'BITHUMB'
    ACTIVE_EXCHANGE: str = os.getenv("ACTIVE_EXCHANGE", "UPBIT")

    # 1. 업비트(Upbit) API 자격증명
    UPBIT_ACCESS_KEY: str = os.getenv("UPBIT_ACCESS_KEY", "")
    UPBIT_SECRET_KEY: str = os.getenv("UPBIT_SECRET_KEY", "")
    UPBIT_SERVER_URL: str = "https://api.upbit.com"

    # 2. 빗썸(Bithumb) API 자격증명
    BITHUMB_CONNECT_KEY: str = os.getenv("BITHUMB_CONNECT_KEY", "")
    BITHUMB_SECRET_KEY: str = os.getenv("BITHUMB_SECRET_KEY", "")
    BITHUMB_SERVER_URL: str = "https://api.bithumb.com"

    # 3. 리스크 & 매매 공통 파라미터
    MAX_POSITION_KRW: int = 500_000         # 1회 진입 기본 주문 금액 (50만원)
    STOP_LOSS_PCT: float = -1.20            # 코인 변동성 고려 손절선 (-1.20%)
    TAKE_PROFIT_1_PCT: float = 2.00         # 1차 익절 (+2.00%) -> 본절 전환
    TAKE_PROFIT_2_PCT: float = 4.50         # 2차 익절 (+4.50%) -> 트레일링 스탑
    TRAILING_GAP_PCT: float = 0.80          # 고점 대비 트레일링 갭 (0.80%)

    # 4. 대상 코인 유니버스 (기본 탑재)
    PRIMARY_SYMBOLS = ["KRW-BTC", "KRW-ETH", "KRW-SOL", "KRW-XRP"]

coin_config = CoinConfig()
