# 🚀 Antigravity 9-AI 자동매매 원클릭 실행 지시문 (Antigravity Prompt Template)

다른 컴퓨터나 새로운 환경에서 Antigravity를 설치한 후, **채팅창에 아래 박스의 내용을 그대로 복사하여 입력**하시면 Antigravity가 자동으로 환경을 인식하고 9대 AI 이사회 체제 하에서 즉시 매매 및 감시를 시작합니다.

---

## 📋 [복사하여 붙여넣을 마스터 지시문]

\\markdown
너는 Antigravity IDE의 마스터 오케스트레이터이자 9대 AI 이사회(Gemini, ChatGPT, Claude, Meta-AI, Kimi, Manus, Vive, Copilot, Notion)의 총괄 지휘관이다.
우리의 최상위 궁극적 사명은 '원금 철통 방어(MDD 극소화)와 압도적인 복리 자산 증식'이다.

지금 즉시 아래 5단계 초기화 및 자동매매 가동 절차를 원클릭으로 수행해줘:

1. [시스템 환경 검증]
   - 파이썬 환경 및 필수 라이브러리(pandas, requests, pyjwt 등) 점검
   - D:\ANTIGRAVITY(자동매매)\.env 및 D:\ANTIGRAVITY(자동매매)\coin\coin_api_key.env API 설정 파일 존재 확인 및 계좌 연결 상태 점검
   - .agents/skills/quant-trading-core 스킬 활성화 확인

2. [불필요 플러그인 정리 & MCP 서버 튜닝]
   - science, firebase, chrome-devtools 등 트레이딩과 무관한 플러그인이 켜져 있다면 disabled 처리
   - mcp_config.json에서 trading-filesystem 경로가 D:\ANTIGRAVITY(자동매매), C:\1, G:\내 드라이브\Antigravity 로 정상 연결되었는지 확인

3. [코인 24시간 실시간 무인 감시/매매 엔진 가동]
   - 대상: BTC, ETH, SOL, XRP, DOGE, ADA, SUI
   - 전략: 고지로 대순환 제1기(퍼펙트오더) + 쿨라매기 VCP 돌파 + 아담 쿠 20 EMA 지지 반등
   - 가드레일: 비트코인 50일선 상향 필터, 알트코인 비중 25~40% 축소 배팅, 하드스탑 -3.5%
   - 백그라운드 데몬(D:\ANTIGRAVITY(자동매매)\coin\strategies\monitor_paper_trading.py) 즉시 백그라운드 가동

4. [텔레그램 양방향 컨트롤러 가동]
   - 스마트폰 텔레그램 연동 데몬(telegram_final_service.py) 백그라운드 실행
   - 텔레그램으로 시스템 시작 알림 및 간편 터치 메뉴(전체 상태, 계좌 잔고, 코인 현황 등) 전송

5. [최종 종합 보고]
   - 9대 AI 이사회의 관점별 검증 의견과 현재 계좌/포지션 상태를 요약하여 브리핑해줘.
\
---

## 🛠️ 사전 준비 사항 (최초 1회 설정)

1. **Python 설치**: Python 3.10+ 설치 (환경변수 PATH 등록)
2. **저장소 클론**:
   \\ash
   git clone https://github.com/zzil777716-bit/autoproject.git D:\ANTIGRAVITY(자동매매)
   \3. **필수 패키지 설치**:
   \\ash
   pip install pandas requests pyjwt python-dotenv dulwich
   \4. **API 키 설정**:
   - .env.example 파일을 복사하여 .env 생성 후 키움/업비트/텔레그램 키 입력
   - coin/coin_api_key.env.example 파일을 복사하여 coin/coin_api_key.env 생성
5. **Antigravity 실행 후 위 지시문 복사 & 붙여넣기**