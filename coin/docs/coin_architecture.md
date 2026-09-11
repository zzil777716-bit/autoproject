# 🪙 Antigravity Crypto Trading Engine Architecture Blueprint
**작성 주체: 9대 AI 영구 이사회 (Permanent Council)**  
**목적: 24시간 365일 무중단 가상자산 퀀트 복리 증식 및 원금 방어**  
**위치: `C:\Antigravity\coin`**

---

## 1. 🏛️ 시스템 개요 및 비전

주식 시장(08:00 ~ 20:00)과 달리 가상자산 시장은 **24시간 365일 실시간으로 가동**됩니다.  
본 엔진은 주식 자동매매에서 검증된 **"3중 리스크 락(Triple-Lock)"**, **"VWAP/이격도 스마트 눌림목"**, **"AI 가디언 실시간 심사"** 메커니즘을 가상자산 시장에 이식하여, **업비트(Upbit)** 및 **빗썸(Bithumb)** 양대 거래소에서 사용자 자산을 복리로 증식시키는 것을 목표로 합니다.

---

## 2. 📂 디렉토리 구조도 (`C:\Antigravity\coin`)

```
C:\Antigravity\coin\
├── adapters\                  # [거래소 통신 어댑터 계층]
│   ├── upbit_adapter.py       # 업비트 REST API (JWT 토큰, 계좌, 시세, 주문)
│   └── bithumb_adapter.py     # 빗썸 REST API (HMAC-SHA512 서명, 계좌, 시세, 주문)
├── config\                    # [환경 및 킬스위치 설정]
│   ├── settings.py            # API 자격증명 및 전역 파라미터 (손절 -1.2%, 익절 2~4.5%)
│   └── coin_risk_rules.json   # 코인 전용 급락 방어 킬스위치 룰셋
├── strategies\                # [코인 퀀트 전략 계층]
│   ├── vwap_pullback.py       # 15분봉 VWAP 지지반등 및 거래량 급감 눌림목 전략
│   └── volatility_breakout.py # 래리 윌리엄스 변동성 돌파 개량형 전략
├── risk_engine\               # [24시간 무중단 리스크 방어선]
│   ├── coin_local_risk.py     # 틱 단위 트레일링 스탑, -1.2% 하드 손절
│   └── coin_global_risk.py    # 비트코인 급락(-3% 이상 덤핑) 시 알트코인 전량 매수 차단
├── collectors\                # [실시간 시세 수집기]
│   └── websocket_feeder.py    # 업비트/빗썸 웹소켓 실시간 틱/호가 오더북 수집기
├── storage\                   # [데이터 보존]
│   └── coin_data_lake.py      # SQLite WAL 기반 코인 전용 매매일지 (trade_journal_coin.sqlite)
├── docs\                      # [설계 문서 및 보고서]
│   └── coin_architecture.md   # 본 설계도
└── run_coin_bot.py            # [실행 진입점] 24시간 백그라운드 워커 런처
```

---

## 3. 🔌 양대 거래소 API 규격 비교 및 특징

| 항목 | 업비트 (Upbit) | 빗썸 (Bithumb) | 안티그래비티 구현 방식 |
| :--- | :--- | :--- | :--- |
| **인증 방식** | **JWT (JSON Web Token)**<br>(Query SHA-512 해시 포함) | **HMAC-SHA512**<br>(Base64 인코딩 시그니처) | `UpbitAdapter` 및 `BithumbAdapter` 모듈 분리 탑재 완료 |
| **주문 방식** | `bid`(매수), `ask`(매도)<br>지정가(`limit`), 시장가(`price`/`market`) | `bid`(매수), `ask`(매도)<br>지정가 및 시장가 지원 | 동일한 인터페이스로 래핑하여 전략 코드 재사용 |
| **호출 제한** | 초당 초과 시 HTTP 429 반환 | 초당 제한 초과 시 블록 | 초당 8회 이내 자동 슬립(Rate Limiter) 탑재 |
| **수수료 체계** | 원화 마켓 0.05% 수준 | 원화 마켓 0.04% 수준 (쿠폰 적용 시) | 왕복 수수료(0.1%) 감안한 최소 익절 마진(+1.0% 이상) 강제 |

---

## 4. 🛡️ 코인 시장 전용 3대 방어선 (9대 AI 이사회 합의)

1. **BTC 덤핑 킬스위치 (Bitcoin Panic Dump Shield - Meta-AI / Claude)**:
   - 비트코인이 15분봉 기준 -2.5% 이상 급락할 경우, 모든 알트코인은 커플링되어 투매가 나오므로 **신규 매수를 100% 즉시 차단**하고 기존 포지션은 손절 마진을 타이트하게 축소.
2. **거래량 없는 잡알트 배제 유니버스 (Liquidity Filter - Kimi / ChatGPT)**:
   - 일 거래대금 50억 원 미만 잡코인은 세력 덤핑 및 슬리피지가 크므로, **BTC, ETH, SOL, XRP 및 당일 거래대금 TOP 10 상위 코인으로 유니버스 제한**.
3. **가변 트레일링 스탑 (Vive / Gemini)**:
   - 코인의 강한 상방 랠리를 놓치지 않기 위해 **1차 익절(+2.0%) 도달 시 본절 스탑 전환, 2차 익절(+4.5%) 이후 고점 대비 -0.8% 하락 시 자동 익절 청산**.

---

## 5. 🚀 향후 가동 절차
1. 사용자 선택: **업비트(Upbit)** 또는 **빗썸(Bithumb)** 중 사용할 거래소 결정.
2. API Key 발급: 해당 거래소 홈페이지에서 `OpenAPI Key`(입출금 금지, 조회/주문만 허용) 발급 후 `.env` 등록.
3. 무인 백그라운드 구동: `python C:\Antigravity\coin\run_coin_bot.py` 실행 시 24시간 자율 가동.
