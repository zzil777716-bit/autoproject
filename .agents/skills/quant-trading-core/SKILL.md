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

## 🛡️ 리스크 관리 가드레일
1. **대장주(BTC) 50일선 필터**: BTC가 50 SMA 하회 시 알트코인 신규 매수 전면 차단
2. **알트코인 포지션 감축 배팅**: BTC(100%), ETH(80%), SOL(40%), XRP(30%), DOGE/ADA/SUI(25%)
3. **하드스탑 (Hard Stop-loss)**: 최대 -3.5% 또는 최근 5일 최저가 이탈 시 칼손절
4. **트레일링 스탑 (Trailing Stop)**: 1차 목표 수익(+2.0%) 달성 시 본절 스탑 전환, 10 EMA 이탈 시 분할 익절

## 🔌 연동 파이프라인
- **업비트(Upbit)**: `C:\Antigravity\coin\adapters\upbit_adapter.py`
- **키움증권(Kiwoom REST)**: `C:\Antigravity\adapters\kiwoom_adapter.py`
- **텔레그램 컨트롤러**: `telegram_final_service.py` (@hong_auto_bot)