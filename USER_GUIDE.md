# 📖 Antigravity 완전 정복 설치 및 실전 운용 매뉴얼

본 매뉴얼은 **처음 Antigravity 자동매매 시스템을 접하는 사용자나 지인**이 동일한 9-AI 이사회 시스템을 구축하고 무인으로 운용할 수 있도록 돕는 실전 가이드북입니다.

---

## 🏗️ 1. 아키텍처 및 시스템 요구사항

- **운영체제**: Windows 10 / 11 (키움증권 OpenAPI 32비트/REST 64비트 및 업비트 호환)
- **런타임**: Python 3.10+ (32비트 또는 64비트)
- **개발환경**: Antigravity IDE
- **스토리지 권장**: C:\Antigravity (기본 작업 공간)

---

## ⚡ 2. 3분 원클릭 설치 절차

### 1단계: 프로젝트 다운로드 (Git Clone)
\\ash
git clone https://github.com/zzil777716-bit/autoproject.git C:\Antigravity
cd C:\Antigravity
\
### 2단계: 필수 패키지 설치
\\ash
pip install pandas numpy requests pyjwt python-dotenv dulwich
\
### 3단계: 거래소 및 텔레그램 API 키 설정
프로젝트 내 템플릿 파일을 복사하여 나만의 키를 입력합니다:
1. C:\Antigravity\.env.example -> C:\Antigravity\.env 로 복사 후 편집
2. C:\Antigravity\coin\coin_api_key.env.example -> C:\Antigravity\coin\coin_api_key.env 로 복사 후 편집

*입력할 항목*:
- **업비트**: Access Key, Secret Key (Open API 관리에서 발급, 자산조회/주문 권한 체크)
- **키움증권**: App Key, Secret Key, 계좌번호 (모의투자/실전)
- **텔레그램**: Bot Token (@BotFather), Chat ID (@userinfobot 등에서 확인)

---

## 🎯 3. Antigravity AI에게 한 번에 지시하는 법

1. Antigravity IDE를 실행하고 C:\Antigravity 폴더를 엽니다.
2. ANTIGRAVITY_ONECLICK_PROMPT.md 파일의 지시문을 복사하여 Antigravity 채팅창에 붙여넣습니다.
3. Antigravity가 자동으로:
   - 9대 AI 이사회를 소집하고,
   - 시스템 환경 및 계좌 연결을 검증하며,
   - 24시간 실시간 무인 코인 감시 엔진과 텔레그램 양방향 컨트롤러를 백그라운드에 구동합니다!

---

## 📱 4. 스마트폰 텔레그램으로 무인 관제하기

시스템이 가동되면 스마트폰 텔레그램 앱의 봇 채팅방에 **6대 터치 버튼**이 나타납니다:
- **📊 전체 상태**: 코인/주식 감시 엔진의 실시간 가동 상태 점검
- **💰 계좌 잔고**: 업비트 원화(KRW) 및 보유 코인 실시간 잔고 확인
- **🪙 코인 현황**: 최근 포착된 매수/익절/손절 타점 실시간 열람
- **📈 주식 현황**: 키움증권 자동매매 및 일봉 데이터 수집 상태 확인
- **🛑 긴급 정지**: 시장 급변 시 신규 진입 즉시 킬스위치 차단

---

## 🛡️ 5. 9대 AI 이사회의 절대 원칙 (Supreme Mission)

1. **원금 철통 방어 (MDD 극소화)**: 모든 진입에는 -3.5% 하드스탑이 자동으로 걸립니다.
2. **비트코인(BTC) 50일선 필터**: 비트코인이 50일선 아래인 하락장에서는 어떠한 알트코인도 매수하지 않습니다.
3. **고지로 대순환 제1기(퍼펙트오더)**: 10 EMA > 20 EMA > 50 SMA 완벽한 상승 국면에서만 진입합니다.
4. **알트코인 비중 축소**: 변동성이 큰 알트코인은 원금 대비 25~40%로 축소 배팅합니다.