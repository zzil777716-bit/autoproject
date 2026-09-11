# 🚀 [SAM-BOT v2.0] 삼성전자(005930) 키움증권 다중 주기(15M/5M/3M) 자동매매 시스템

이 프로젝트는 **15분봉(거시 추세 필터) $\rightarrow$ 5분봉(눌림목 검증) $\rightarrow$ 3분봉(정밀 체결 트리거)**의 다중 주기(Multi-Timeframe Cascading) 전략을 탑재한 키움증권 OpenAPI+ 기반 실시간 주식 자동매매 프로그램입니다.

---

## 📁 프로젝트 구조

```text
C:\Users\HONG\.gemini\antigravity\scratch\
├── config/
│   └── settings.py          # 전략 파라미터, 익절/손절선, 쿨다운, 텔레그램 설정
├── core/
│   ├── kiwoom_api.py        # 32비트 PyQt5 QAxWidget 래퍼 & Token Bucket Rate Limiter
│   ├── candle_engine.py     # 실시간 틱 데이터 기반 15m/5m/3m 롤링 캔들 합성기
│   ├── indicators.py        # EMA, VWAP, RSI, ADX, SuperTrend, RVOL 지표 계산
│   ├── strategy_mtf.py      # MTF 다중 주기 상태 머신 및 엣지 케이스 필터
│   ├── risk_manager.py      # 포지션 사이징, 서킷 브레이커, 트레일링 스탑
│   └── telegram_notifier.py # 스마트폰 실시간 5종 알림 발송 모듈
├── data/
│   └── timeseries_db.py     # 1분봉 데이터 SQLite/Parquet 로컬 저장소
├── tasks/
│   ├── debate_gpt.md        # GPT 토론 보고서 (UX / 엣지케이스 / 알림)
│   ├── debate_meta-ai.md    # Meta-AI 토론 보고서 (수수료 / 기대값 / 서킷브레이커)
│   ├── debate_manus.md      # Manus 토론 보고서 (실전 구현 / 툴 연동)
│   ├── debate_kimi.md       # Kimi 토론 보고서 (TR 스펙 / 시계열 파이프라인)
│   └── final_result.md      # Gemini 감독자 최종 승인 설계서
├── main_trader.py           # 단일 통합 실행 메인 엔트리포인트
├── requirements.txt         # 파이썬 의존성 패키지 목록
└── README.md                # 사용 설명서
```

---

## ⚙️ 사전 필수 준비사항 (Windows 환경)

1. **키움증권 Open API+ 설치 및 모의투자 신청**:
   - 키움증권 홈페이지에서 `Open API+` 모듈 다운로드 및 설치.
   - 키움증권 모의투자(상시모의투자) 신청 후 HTS(영웅문4 또는 번개3)에서 로그인 테스트.
   - `KOA Studio` 실행하여 정상 로그인 및 계좌번호 확인.

2. **32비트 Python 환경 구축**:
   - 키움 Open API+는 32비트 Active-X COM 객체이므로 반드시 **32-bit Python** 환경이 필요합니다.
   ```powershell
   # Anaconda 사용 시 (32비트 가상환경 생성)
   set CONDA_FORCE_32BIT=1
   conda create -n kiwoom32 python=3.10
   conda activate kiwoom32
   
   # 또는 32비트 Python 3.10 설치 후 venv 생성
   py -3.10-32 -m venv venv32
   .\venv32\Scripts\activate
   ```

3. **의존성 패키지 설치**:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 🎯 실행 방법

```powershell
cd C:\Users\HONG\.gemini\antigravity\scratch
python main_trader.py
```

실행 시 키움증권 로그인 창이 팝업되며, 로그인이 완료되면 자동으로 삼성전자(005930) 실시간 호가/체결 데이터를 수신하고 5초 주기로 터미널 TUI 대시보드가 갱신됩니다.

---

## 🛡️ 주요 전략 및 리스크 관리 규칙

| 구분 | 조건 및 룰셋 |
| :--- | :--- |
| **15분봉 매크로 필터** | `EMA(60) > EMA(120)` 정배열 + `현재가 > EMA(20)` + `SuperTrend == Bullish` |
| **5분봉 눌림목 검증** | `현재가 >= VWAP(기관평단)` + `RSI 38~48` 눌림 후 반등 + `ADX > 20` |
| **3분봉 정밀 진입** | `5 EMA 상향돌파` + `RVOL ≥ 200%` + `실시간 체결강도 ≥ 110%` |
| **1차 분할 익절** | `+1.20%` 도달 시 50% 분할 매도 $\rightarrow$ **본절 스탑(매수가) 즉시 전환** |
| **2차 트레일링 익절** | `+1.50%` 이상 구간에서 최고점 대비 `-0.50%` 반납 시 잔여 전량 익절 |
| **절대 손절선** | 진입가 대비 `-0.80%` 도달 시 전량 칼손절 |
| **시초가 갭 방어** | `09:00 ~ 09:15` 15분간 매매 금지 $\rightarrow$ 09:15 ORB 레인지 돌파 검증 |
| **연속 손절 서킷브레이커** | 2회 연속 손절 시 `30분간 강제 쿨다운` (1회는 15분) |
| **장마감 오버나이트 방지** | `15:15` 신규 진입 차단 $\rightarrow$ `15:20` 보유 잔여물량 **전량 시장가 청산** |
