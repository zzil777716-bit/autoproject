"""
Configuration settings for Samsung Electronics (005930) Kiwoom MTF Trading Bot.
Active Strategy: Strategy 2 [변동성 수축 및 수급 반등형 (MTF-Squeeze & Divergence Reversal)]
"""

from dataclasses import dataclass, field
from datetime import time

@dataclass
class TradingConfig:
    # -------------------------------------------------------------
    # 1. 종목 및 계좌 기본 설정
    # -------------------------------------------------------------
    STOCK_CODE: str = "005930"          # 삼성전자
    STOCK_NAME: str = "삼성전자"
    ACCOUNT_NO: str = "8132211811"       # 키움 모의투자 계좌번호 (검증 완료)
    IS_SIMULATION: bool = True          # True: 모의투자, False: 실전투자
    
    # -------------------------------------------------------------
    # 2. 운용 자금 및 주문 수량 (1주 고정)
    # -------------------------------------------------------------
    ACTIVE_STRATEGY: str = "STRATEGY_2_SQUEEZE"  # 전략 2 (변동성 수축/수급 반등형)
    DEFAULT_TRADE_QTY: int = 1         # 1회 주문 수량 (무조건 1주 고정)
    MAX_SPLIT_ORDERS: int = 1          # 분할 매수 횟수 (1회 진입)
    MAX_DAILY_TRADES: int = 3          # 1일 최대 매매 횟수 제한 (3회)
    
    # -------------------------------------------------------------
    # 3. 전략 2 지표 파라미터 (15M -> 5M -> 3M)
    # -------------------------------------------------------------
    # 15분봉 (Macro Squeeze Filter)
    BB_PERIOD_15M: int = 20
    BB_STD_15M: float = 2.0
    BB_BW_SQUEEZE_MAX_15M: float = 0.018 # 볼린저 밴드폭 1.8% 이하 극대 수축
    KC_PERIOD_15M: int = 20             # 켈트너 채널 EMA 기간
    KC_MULT_15M: float = 1.5            # 켈트너 채널 ATR 승수
    EMA_SUPPORT_15M: int = 120          # 거시 생명 지지선 (120 EMA)
    
    # 5분봉 (Meso Divergence & Rejection)
    RSI_PERIOD_5M: int = 14
    STOCH_K_5M: int = 12
    STOCH_D_5M: int = 5
    DIVERGENCE_LOOKBACK_5M: int = 12    # 다이버전스 탐색 캔들 수
    RSI_OVERSOLD_5M: float = 38.0       # 과매도 기준
    
    # 3분봉 (Micro Orderbook & Flow Trigger)
    INTENSITY_MIN_3M: float = 110.0     # 실시간 체결강도 110% 이상
    INTENSITY_V_DELTA_MIN: float = 25.0 # V자 반등 최소 폭 (+25%p)
    ORDERBOOK_RATIO_MIN: float = 1.30   # 매도총잔량 / 매수총잔량 비대칭 (1.3 이상)
    
    # -------------------------------------------------------------
    # 4. 익절 / 손절 / 트레일링 룰 (1주 단일 포지션 최적화)
    # -------------------------------------------------------------
    TAKE_PROFIT_1_PCT: float = 0.90     # 목표 익절선 (+0.90% 도달 또는 15M 밴드 중심선)
    TAKE_PROFIT_2_PCT: float = 1.80     # 상단 팽창 최종 익절선 (+1.80%)
    STOP_LOSS_PCT: float = -0.60        # 직전 저점 -2틱 손절선 (-0.60%)
    TRAILING_STOP_TRIGGER_PCT: float = 1.20 # 트레일링 발동 수익률 (+1.20%)
    TRAILING_STOP_DROP_PCT: float = -0.40   # 최고점 대비 허용 하락폭 (-0.40%)
    TIMEOUT_MINUTES: int = 60           # 60분간 팽창 실패 시 타임아웃 청산
    
    # -------------------------------------------------------------
    # 5. 레드팀 6대 하드코어 가드레일
    # -------------------------------------------------------------
    DAILY_MAX_LOSS_PCT: float = -1.50   # 일일 최대 손실 한도 (-1.50% 도달 시 당일 킬스위치)
    MIN_15M_ATR_PCT: float = 0.60       # 최소 변동성 게이트 (15분봉 ATR 0.60% 미만 시 진입 금지)
    CONSECUTIVE_LOSS_LIMIT: int = 2     # 연속 손절 2회 시 30분 쿨다운
    COOLDOWN_MINUTES_DEFAULT: int = 15  # 1회 손절 후 쿨다운 15분
    COOLDOWN_MINUTES_CONSECUTIVE: int = 30 # 2회 연속 손절 후 쿨다운 30분
    
    # -------------------------------------------------------------
    # 6. 매매 시간 제어 (한국 정규장 기준)
    # -------------------------------------------------------------
    TIME_BLACKOUT_START: time = field(default_factory=lambda: time(9, 0))   # 09:00
    TIME_BLACKOUT_END: time = field(default_factory=lambda: time(9, 15))     # 09:15 (시초가 갭 방어)
    TIME_ENTRY_DEADLINE: time = field(default_factory=lambda: time(15, 15))  # 15:15 (신규 진입 차단)
    TIME_MARKET_CLOSE_SELL: time = field(default_factory=lambda: time(15, 20)) # 15:20 (오버나이트 방지 전량 청산)
    
    # -------------------------------------------------------------
    # 7. 키움 OpenAPI+ 호출 제어 및 텔레그램
    # -------------------------------------------------------------
    MAX_TR_PER_SECOND: float = 3.5      # 초당 최대 TR 요청 수 (3.5회 안전폭)
    SCREEN_NO_REAL: str = "1000"
    SCREEN_NO_TR: str = "2000"
    SCREEN_NO_ORDER: str = "3000"
    
    TELEGRAM_BOT_TOKEN: str = "8988429416:AAG3FGLLleRF-dapt2XYSL2D5Eo-zoJNaO8"
    TELEGRAM_CHAT_ID: str = "8169345022"
    ENABLE_TELEGRAM: bool = True

config = TradingConfig()
