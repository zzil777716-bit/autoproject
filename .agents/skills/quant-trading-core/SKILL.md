---
name: quant-trading-core
description: "Core quant strategies, multi-factor setups, risk parameters, and order execution guidelines for Antigravity (Upbit, Kiwoom, Kojiro Daisunhwan, Qullamaggie VCP, Adam Khoo 20 EMA, Tail-risk controls)."
---

# Quant Trading Core Skill

## 👑 SUPREME MISSION
- **사용자 자산의 압도적 복리 증식 및 원금 방어 (MDD 최소화)**
- 9대 AI 이사회 상시 교차 검증 통과 전략만 실전 채택

## 🏛️ 핵심 전략 타점 및 지표 공식

### 1. 고지로 강사 이동평균선 대순환 6단계 (Kojiro Daisunhwan)
- **이평선 설정**:
  - 단기: 10 EMA (지수이동평균)
  - 중기: 20 EMA (지수이동평균)
  - 장기: 50 SMA (단순이동평균)
- **6단계 사이클**:
  - **제1기 (안정 상승기 / 퍼펙트 오더)**: 10 EMA >= 20 EMA >= 50 SMA (★ 최우선 매수 국면)
  - **제2기 (상승 피로기)**: 20 EMA >= 10 EMA >= 50 SMA (분할 익절 준비)
  - **제3기 (하락 전환기)**: 20 EMA >= 50 SMA >= 10 EMA (매수 절대 금지)
  - **제4기 (안정 하락기)**: 50 SMA >= 20 EMA >= 10 EMA (인버스/숏 또는 전량 현금)
  - **제5기 (바닥 반등 모색기)**: 50 SMA >= 10 EMA >= 20 EMA (관망)
  - **제6기 (상승 전환 태동기)**: 10 EMA >= 50 SMA >= 20 EMA (골든크로스 예비 타점)

### 2. 쿨라매기 VCP (Volatility Contraction Pattern)
- 5일간의 고저점 변동폭 축소: `(High5 - Low5) / Close < 임계값 (BTC: 6%, ETH: 8%, 알트: 10~12%)`
- 거래량 수축 후 돌파 시 거래량 폭발: `Volume > 1.15 * VolSMA20` & `Close > PrevHigh5`

### 3. 아담 쿠 20 EMA 눌림목 지지 반등
- 20 EMA 근접 눌림: `Low <= 20 EMA * 1.015` 및 `Low >= 20 EMA * 0.97`
- 양봉 지지 반등 확인: `Close > Open` 및 `Close > 20 EMA`

### 4. 윗꼬리 매집봉 실전 최적화 룰 (2026-09 실증 검증 반영)
- **[규칙 1: 장중 분할 익절 & 본절 추종]**:
  - 윗꼬리 매집봉 포착 종목의 익일 장중 고가 돌파 승률은 **79.25% (평균 상승폭 +3.45%)**에 달함.
  - 진입 후 **장중 +2.5% ~ +3.5% 도달 시 보유 물량의 50%를 즉시 1차 익절**하여 수익을 확정한다.
  - 잔여 50%는 **진입가(본절가)에 스탑로스(Stop)를 상향**하여 하방 리스크를 원천 차단하고 추가 상승을 추종한다.
- **[규칙 2: 지수 및 대장주 거시 필터 (Market Regime Filter)]**:
  - 지수 급락일(삼성전자/하이닉스 -2% 이상 하락 또는 KOSPI 20일선 하회)에는 개별 종목 승률이 9.5%로 급락함.
  - **지수 대장주(삼성전자)가 당일 -1.5% 이상 하락 중이거나 KOSPI가 20일선 아래일 때는 윗꼬리 매집봉이 포착되더라도 신규 매수를 전면 보류(Cash 100%)**한다.

## 🛡️ 리스크 관리 가드레일
1. **대장주 필터**: 
   - 코인: BTC가 50 SMA 하회 시 알트코인 신규 매수 전면 차단
   - 주식: 삼성전자 -1.5% 급락 또는 KOSPI 20일선 하회 시 신규 매수 차단
2. **포지션 감축 배팅**: 
   - 코인: BTC(100%), ETH(80%), SOL(40%), XRP(30%), DOGE/ADA/SUI(25%)
   - 주식: 1회 1주~정액 분할 진입, 1일 최대 3회 거래 제한
3. **하드스탑 (Hard Stop-loss)**: 최대 -3.5% 또는 최근 5일 최저가 이탈 시 칼손절
4. **트레일링 스탑 (Trailing Stop)**: 1차 목표 수익(+2.5%~+3.0%) 달성 시 본절 스탑 전환

## 🔌 연동 파이프라인
- **업비트(Upbit)**: `D:\ANTIGRAVITY(자동매매)\coin\adapters\upbit_adapter.py`
- **키움증권(Kiwoom REST)**: `D:\ANTIGRAVITY(자동매매)\adapters\kiwoom_adapter.py`
- **텔레그램 컨트롤러**: `telegram_final_service.py` (@hong_auto_bot)