"""
Configuration settings for SK Hynix (000660) Kiwoom MTF Trading Bot.
Strategy: [부자회사원 7개월 검증] 삼중 스크린(Triple-Screen) 엔벨로프/EMA 주도주 눌림목 매매 전략
"""

from dataclasses import dataclass, field
from datetime import time

@dataclass
class TradingConfig:
    # -------------------------------------------------------------
    # 1. 종목 및 계좌 기본 설정
    # -------------------------------------------------------------
    STOCK_CODE: str = "000660"          # SK하이닉스
    STOCK_NAME: str = "SK하이닉스"
    ACCOUNT_NO: str = "8132211811"       # 키움 모의투자 계좌번호
    IS_SIMULATION: bool = True          # True: 모의투자, False: 실전투자
    
    # -------------------------------------------------------------
    # 2. 운용 자금 및 주문 수량 (1주 고정)
    # -------------------------------------------------------------
    ACTIVE_STRATEGY: str = "BUJA_ENVELOPE_PULLBACK"  # 부자회사원 삼중스크린 엔벨로프 눌림목 전략
    DEFAULT_TRADE_QTY: int = 1         # 1회 주문 수량 (1주 고정)
    MAX_SPLIT_ORDERS: int = 1          # 분할 매수 횟수 (1회)
    MAX_DAILY_TRADES: int = 3          # 1일 최대 매매 횟수 (3회 제한)
    
    # -------------------------------------------------------------
    # 3. 부자회사원 삼중 스크린 지표 파라미터 (15M -> 5M -> 3M)
    # -------------------------------------------------------------
    # [Screen 1] 15분봉 조류(Tide) 추세 필터
    EMA_FAST_15M: int = 20              # 15분봉 단기 추세선 (20 EMA)
    EMA_MID_15M: int = 60               # 15분봉 중기 추세선 (60 EMA)
    EMA_SLOW_15M: int = 120             # 15분봉 장기 생명선 (120 EMA)
    MACD_FAST_15M: int = 12
    MACD_SLOW_15M: int = 26
    MACD_SIGNAL_15M: int = 9
    
    # [Screen 2] 5분봉 파도(Wave) 엔벨로프/VWAP 눌림목 포착
    ENVELOPE_PERIOD_5M: int = 20        # 엔벨로프 중심선 (20 SMA)
    ENVELOPE_PERCENT_5M: float = 1.8    # 엔벨로프 하단 이격률 (1.8% ~ 2.0% 눌림목)
    RSI_PERIOD_5M: int = 14
    RSI_PULLBACK_MIN_5M: float = 35.0   # 과매도 눌림 하한
    RSI_PULLBACK_MAX_5M: float = 48.0   # 과매도 눌림 상한
    RSI_REBOUND_5M: float = 42.0        # 턴어라운드 상향 돌파
    
    # [Screen 3] 3분봉 잔물결(Ripple) 정밀 수급 & 틱 트리거
    EMA_TRIGGER_3M: int = 5             # 3분봉 5 EMA 돌파
    RVOL_THRESHOLD_3M: float = 2.0      # 상대거래량 200% 이상 폭발
    INTENSITY_MIN_3M: float = 110.0     # 체결강도 110% 이상
    ORDERBOOK_RATIO_MIN: float = 1.25   # 매도총잔량 / 매수총잔량 비대칭
    
    # -------------------------------------------------------------
    # 4. 익절 / 손절 / 트레일링 룰 (SK하이닉스 변동성 맞춤)
    # -------------------------------------------------------------
    TAKE_PROFIT_1_PCT: float = 1.30     # 1차 익절 (+1.30% 또는 5M 엔벨로프 상단) -> 본절 스탑 전환
    TAKE_PROFIT_2_PCT: float = 2.50     # 2차 최종 익절 (+2.50% 또는 15M 엔벨로프 상단)
    STOP_LOSS_PCT: float = -0.90        # 고정 손절선 (-0.90%, 직전 눌림 저점 이탈)
    TRAILING_STOP_TRIGGER_PCT: float = 1.60 # 트레일링 발동 수익률 (+1.60%)
    TRAILING_STOP_DROP_PCT: float = -0.50   # 최고점 대비 허용 하락폭 (-0.50%)
    TIMEOUT_MINUTES: int = 45           # 45분간 모멘텀 정체 시 본전 탈출
    
    # -------------------------------------------------------------
    # 5. 레드팀 6대 하드코어 가드레일
    # -------------------------------------------------------------
    DAILY_MAX_LOSS_PCT: float = -1.50   # 일일 최대 손실 한도 (-1.50% 킬스위치)
    MIN_15M_ATR_PCT: float = 0.70       # SK하이닉스 최소 변동성 게이트 (15M ATR 0.70% 미만 진입 차단)
    CONSECUTIVE_LOSS_LIMIT: int = 2     # 연속 2회 손절 시 30분 쿨다운
    COOLDOWN_MINUTES_DEFAULT: int = 15
    COOLDOWN_MINUTES_CONSECUTIVE: int = 30
    
    # -------------------------------------------------------------
    # 6. 매매 시간 제어
    # -------------------------------------------------------------
    TIME_BLACKOUT_START: time = field(default_factory=lambda: time(9, 0))   # 09:00
    TIME_BLACKOUT_END: time = field(default_factory=lambda: time(9, 15))     # 09:15 (시초가 갭 방어)
    TIME_ENTRY_DEADLINE: time = field(default_factory=lambda: time(15, 15))  # 15:15 (신규 진입 차단)
    TIME_MARKET_CLOSE_SELL: time = field(default_factory=lambda: time(15, 20)) # 15:20 (오버나이트 방지 전량 청산)
    
    # -------------------------------------------------------------
    # 7. 키움 OpenAPI+ 호출 제어
    # -------------------------------------------------------------
    MAX_TR_PER_SECOND: float = 3.5
    SCREEN_NO_REAL: str = "1100"
    SCREEN_NO_TR: str = "2100"
    SCREEN_NO_ORDER: str = "3100"
    
    TELEGRAM_BOT_TOKEN: str = "8988429416:AAG3FGLLleRF-dapt2XYSL2D5Eo-zoJNaO8"
    TELEGRAM_CHAT_ID: str = "8169345022"
    ENABLE_TELEGRAM: bool = True

config = TradingConfig()
