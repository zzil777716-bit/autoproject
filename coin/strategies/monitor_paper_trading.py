# -*- coding: utf-8 -*-
"""
========================================================================================
🪙 [COIN REAL-TIME PAPER TRADING ENGINE (업비트 실시간 모의 감시 엔진)]
- 24시간 백그라운드 무인 구동 (실제 돈은 나가지 않는 안전한 모의 검증)
- 유튜브 9대 강좌 핵심:
  1) 비트코인(BTC) 50일선 상위 필터 (하락장 알트 진입 절대 차단)
  2) 쿨라매기 VCP 변동성 수축 돌파 (거래량 폭발)
  3) 아담 쿠 20 EMA 눌림목 지지 반등
- 알트코인은 사용자 지침대로 매수 비중 대폭 축소 (25%~40%)
- 신호 발생 시 콘솔 출력 및 실시간 로그 파일 영구 기록
========================================================================================
"""

import os
import sys
import time
import datetime
import pandas as pd
import requests

# 프로젝트 경로 추가
BASE_DIR = r"C:\Antigravity\coin"
if BASE_DIR in sys.path:
    sys.path.remove(BASE_DIR)
sys.path.insert(0, BASE_DIR)

from config.settings import coin_config
from adapters.upbit_adapter import UpbitAdapter

# 감시 대상 및 포트폴리오 가중치
WATCH_UNIVERSE = {
    "KRW-BTC": {"name": "비트코인", "type": "대장주", "weight": 1.0,  "vcp_max_range": 0.06},
    "KRW-ETH": {"name": "이더리움", "type": "대장주", "weight": 0.8,  "vcp_max_range": 0.08},
    "KRW-SOL": {"name": "솔라나",   "type": "알트",   "weight": 0.4,  "vcp_max_range": 0.10},
    "KRW-XRP": {"name": "리플",     "type": "알트",   "weight": 0.3,  "vcp_max_range": 0.10},
    "KRW-DOGE": {"name": "도지코인", "type": "알트",   "weight": 0.25, "vcp_max_range": 0.12},
    "KRW-ADA":  {"name": "에이다",   "type": "알트",   "weight": 0.25, "vcp_max_range": 0.12},
    "KRW-SUI":  {"name": "수이",     "type": "알트",   "weight": 0.25, "vcp_max_range": 0.12},
}

LOG_FILE = os.path.join(BASE_DIR, "data", "paper_trading_signals.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8988429416:AAG3FGLLleRF-dapt2XYSL2D5Eo-zoJNaO8")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8169345022")

def send_telegram(text: str):
    """텔레그램 실시간 푸시 발송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
        data = urllib.parse.urlencode(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as _:
            pass
    except Exception:
        pass

def log_msg(msg: str, push_telegram: bool = False):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{now_str}] {msg}"
    try:
        print(formatted.encode("cp949", errors="replace").decode("cp949"))
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass
    if push_telegram:
        send_telegram(msg)

def fetch_daily_df(adapter: UpbitAdapter, market: str, count: int = 100) -> pd.DataFrame:
    """일봉 캔들 조회 및 기술적 지표 계산"""
    url = f"{adapter.server_url}/v1/candles/days"
    params = {"market": market, "count": count}
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df = df[['candle_date_time_kst', 'opening_price', 'high_price', 'low_price', 'trade_price', 'candle_acc_trade_volume']]
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').reset_index(drop=True)
            
            # 이동평균선
            df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
            df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['VolSMA20'] = df['Volume'].rolling(20).mean()
            
            # 5일 변동성 수축(VCP) 및 고저점
            df['High5'] = df['High'].shift(1).rolling(5).max()
            df['Low5'] = df['Low'].shift(1).rolling(5).min()
            df['Range5'] = (df['High5'] - df['Low5']) / df['Close'].shift(1)
            
            return df
    except Exception as e:
        log_msg(f">> {market} 캔들 조회 실패: {e}")
    return pd.DataFrame()

class CryptoPaperTrader:
    def __init__(self):
        self.adapter = UpbitAdapter(coin_config.UPBIT_ACCESS_KEY, coin_config.UPBIT_SECRET_KEY)
        self.paper_positions = {}  # {market: {'entry_price': ..., 'stop_loss': ..., 'strategy': ..., 'weight': ...}}
        log_msg("="*75)
        log_msg("🚀 [Antigravity] 코인 실시간 모의 감시 엔진 가동 시작!")
        log_msg("   - 감시 전략: 쿨라매기 VCP 돌파 & 아담 쿠 20 EMA 눌림목")
        log_msg("   - 리스크 관리: BTC 50일선 필터 + 알트코인 비중 축소 (25%~40%)")
        log_msg("="*75)

    def check_market_regime(self) -> bool:
        """비트코인(BTC) 50일선 상향 지지 여부 검증 (대장주 필터)"""
        btc_df = fetch_daily_df(self.adapter, "KRW-BTC", count=60)
        if btc_df.empty or len(btc_df) < 50:
            return False
        
        last = btc_df.iloc[-1]
        is_bullish = last['Close'] >= last['SMA50']
        pct_diff = (last['Close'] - last['SMA50']) / last['SMA50'] * 100
        # log_msg(f"👑 [비트코인 시황] 종가: {last['Close']:,.0f}원 | 50 SMA: {last['SMA50']:,.0f}원 ({pct_diff:+.2f}%) | 상태: {'상승장(알트진입허용)' if is_bullish else '하락장(알트진입금지)'}")
        return is_bullish

    def scan_signals(self):
        """전체 유니버스 실시간 타점 스캔"""
        btc_bullish = self.check_market_regime()
        
        for market, meta in WATCH_UNIVERSE.items():
            name = meta['name']
            weight = meta['weight']
            coin_type = meta['type']
            vcp_limit = meta['vcp_max_range']
            
            # 알트코인은 BTC가 50일선 아래이면 신규 진입 절대 금지
            if coin_type == "알트" and not btc_bullish:
                continue
                
            df = fetch_daily_df(self.adapter, market, count=60)
            if df.empty or len(df) < 50:
                continue
                
            c = df.iloc[-1]
            prev = df.iloc[-2]
            
            # 고지로 강사 이동평균선 대순환 6단계 판별
            # 단기: 10 EMA, 중기: 20 EMA, 장기: 50 SMA
            stage = 0
            if c['EMA10'] >= c['EMA20'] and c['EMA20'] >= c['SMA50']:
                stage = 1  # 제1기: 안정 상승기 (퍼펙트 오더 - 최우선 매수 국면)
            elif c['EMA20'] >= c['EMA10'] and c['EMA10'] >= c['SMA50']:
                stage = 2  # 제2기: 상승 피로기 (분할 익절 준비)
            elif c['EMA20'] >= c['SMA50'] and c['SMA50'] >= c['EMA10']:
                stage = 3  # 제3기: 하락 전환기 (매수 절대 금지)
            elif c['SMA50'] >= c['EMA20'] and c['EMA20'] >= c['EMA10']:
                stage = 4  # 제4기: 안정 하락기 (인버스/숏 또는 전량 현금)
            elif c['SMA50'] >= c['EMA10'] and c['EMA10'] >= c['EMA20']:
                stage = 5  # 제5기: 바닥 반등 모색기
            elif c['EMA10'] >= c['SMA50'] and c['SMA50'] >= c['EMA20']:
                stage = 6  # 제6기: 상승 전환 태동기 (골든크로스 예비 단계)

            # 1. 이미 보유 중인 모의 포지션 관리
            if market in self.paper_positions:
                pos = self.paper_positions[market]
                entry_p = pos['entry_price']
                stop_p = pos['stop_loss']
                strat = pos['strategy']
                
                # 손익률 계산
                ret_pct = (c['Close'] - entry_p) / entry_p * 100
                
                # 손절 체크
                if c['Low'] <= stop_p:
                    t_msg = f"🛑 *[코인 모의 손절] {name} ({market})*\n━━━━━━━━━━━━━━━━━━━━\n• 손익률: `{ret_pct:.2f}%`\n• 현재가: `{c['Close']:,.0f}원`\n• 사유: 손절선 이탈 방어"
                    log_msg(f"🛑 [모의 손절 체결] {name}({market}) | 손익률: {ret_pct:.2f}% | 사유: 손절선 이탈 ({c['Close']:,.0f}원)")
                    send_telegram(t_msg)
                    del self.paper_positions[market]
                # 고지로 대순환 청산: 제1기가 깨지고 제2기/제3기로 진입하거나, 10 EMA 하향 이탈 시
                elif (stage in [2, 3, 4] or c['Close'] < c['EMA10']) and ret_pct > 1.5:
                    t_msg = f"🎯 *[코인 모의 익절] {name} ({market})*\n━━━━━━━━━━━━━━━━━━━━\n• 손익률: `+{ret_pct:.2f}%`\n• 현재가: `{c['Close']:,.0f}원`\n• 사유: 대순환 {stage}기 전환/10 EMA 이탈 트레일링 익절"
                    log_msg(f"🎯 [모의 익절 체결] {name}({market}) | 손익률: +{ret_pct:.2f}% | 사유: 대순환 {stage}기 전환/10 EMA 이탈 익절 ({c['Close']:,.0f}원)")
                    send_telegram(t_msg)
                    del self.paper_positions[market]
                continue
            
            # 2. 신규 매수 타점 탐색 (반드시 대순환 제1기 퍼펙트오더 또는 제6기 전환 구간에서만 진입!)
            if stage not in [1, 6]:
                continue

            # 전략 A: [대순환 1기 + 쿨라매기 VCP] 수축 후 고가 돌파
            vcp_ok = prev['Range5'] < vcp_limit
            breakout_ok = (c['Close'] > prev['High5']) and (c['Volume'] > 1.15 * c['VolSMA20']) and (c['Close'] > c['Open'])
            
            if stage == 1 and vcp_ok and breakout_ok:
                stop_loss = max(prev['Low5'], c['Close'] * 0.96)
                self.paper_positions[market] = {
                    'entry_price': c['Close'],
                    'stop_loss': stop_loss,
                    'strategy': '대순환1기_쿨라매기VCP돌파',
                    'weight': weight,
                    'entry_time': datetime.datetime.now()
                }
                log_msg(f"🔥 [모의 매수 신호] {name}({market}) - [대순환 제1기(퍼펙트오더) + 쿨라매기 VCP 돌파]")
                t_msg = f"🔥 *[코인 모의 매수] {name} ({market})*\n━━━━━━━━━━━━━━━━━━━━\n• 전략: `고지로 대순환 1기 + 쿨라매기 VCP 돌파`\n• 진입가: `{c['Close']:,.0f}원`\n• 손절가: `{stop_loss:,.0f}원` (-{(c['Close']-stop_loss)/c['Close']*100:.2f}%)\n• 권장 비중: `{weight*100:.0f}%` (원금 대비)\n• 거래량: 평소 대비 `{c['Volume']/c['VolSMA20']:.2f}배` 폭발"
                send_telegram(t_msg)
                continue
                
            # 전략 B: [대순환 1기 + 아담 쿠] 20 EMA 눌림목 지지 반등
            pullback_ok = (c['Low'] <= c['EMA20'] * 1.015) and (c['Low'] >= c['EMA20'] * 0.97)
            bounce_ok = (c['Close'] > c['Open']) and (c['Close'] > c['EMA20'])
            
            if stage == 1 and pullback_ok and bounce_ok:
                stop_loss = min(c['Low'], c['Close'] * 0.965)
                self.paper_positions[market] = {
                    'entry_price': c['Close'],
                    'stop_loss': stop_loss,
                    'strategy': '대순환1기_20EMA눌림목',
                    'weight': weight,
                    'entry_time': datetime.datetime.now()
                }
                log_msg(f"⚡ [모의 매수 신호] {name}({market}) - [대순환 제1기(퍼펙트오더) + 아담 쿠 20 EMA 눌림목]")
                t_msg = f"⚡ *[코인 모의 매수] {name} ({market})*\n━━━━━━━━━━━━━━━━━━━━\n• 전략: `고지로 대순환 1기 + 20 EMA 눌림목 지지`\n• 진입가: `{c['Close']:,.0f}원`\n• 손절가: `{stop_loss:,.0f}원` (-{(c['Close']-stop_loss)/c['Close']*100:.2f}%)\n• 권장 비중: `{weight*100:.0f}%` (원금 대비)\n• 20 EMA: `{c['EMA20']:,.0f}원` (지지 양봉 반등)"
                send_telegram(t_msg)
                continue

def run_loop():
    trader = CryptoPaperTrader()
    log_msg(">> 실시간 모의 감시 주기: 1분(60초)마다 자동 스캔 중...")
    
    # 1회 스캔 즉시 실행
    trader.scan_signals()
    
    # 60초 루프
    while True:
        try:
            time.sleep(60)
            trader.scan_signals()
        except KeyboardInterrupt:
            log_msg("모의 감시 엔진 사용자 종료.")
            break
        except Exception as e:
            log_msg(f"루프 에러 발생: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_loop()
