"""
Telegram Real-time Notification Dispatcher
Sends formatted trade alerts and risk state updates to the trader's smartphone.
"""

import urllib.request
import urllib.parse
import json
from datetime import datetime
from config.settings import config

class TelegramNotifier:
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.enabled = config.ENABLE_TELEGRAM and bool(self.bot_token) and bool(self.chat_id)

    def send_message(self, text: str):
        """동기식 텔레그램 메시지 발송"""
        if not self.enabled:
            print(f"[TELEGRAM SIMULATION]\n{text}\n")
            return

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            data = urllib.parse.urlencode(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=5) as response:
                pass
        except Exception as e:
            print(f">> [TELEGRAM ERROR] 메시지 전송 실패: {e}")

    def notify_entry(self, code: str, price: float, qty: int, reason: str, metrics: dict):
        msg = f"""🟢 *[자동매매 진입] 삼성전자 ({code})*
━━━━━━━━━━━━━━━━━━━━
⏰ *체결시간*: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
📍 *진입유형*: `MTF 15M/5M/3M Confluence Entry`

• *매수가격*: `{price:,}원`
• *매수수량*: `{qty}주` (약 {int(price * qty):,}원)
• *1차 목표가*: `{int(price * (1 + config.TAKE_PROFIT_1_PCT/100)):,}원` (+{config.TAKE_PROFIT_1_PCT:.2f}%)
• *손절 기준가*: `{int(price * (1 + config.STOP_LOSS_PCT/100)):,}원` ({config.STOP_LOSS_PCT:.2f}%)

📊 *지표 상태*:
• 15분봉: `EMA 정배열 & Bullish`
• 5분봉: `VWAP 상회 / RSI {metrics.get('5m_rsi', 0):.1f}`
• 3분봉: `RVOL {metrics.get('3m_rvol', 0):.1f}x / 체결강도 {metrics.get('intensity', 0):.1f}%`

🔒 *원칙 기반 리스크 관리 가동 중*"""
        self.send_message(msg)

    def notify_partial_tp(self, code: str, sold_qty: int, rem_qty: int, pnl_pct: float, pnl_won: int, entry_price: float):
        msg = f"""✨ *[1차 분할 익절 완료] 삼성전자 ({code})*
━━━━━━━━━━━━━━━━━━━━
⏰ *체결시간*: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
🎯 *실현수익률*: `+{pnl_pct:.2f}%`
💰 *실현손익*: `+{pnl_won:,}원`

• *체결수량*: `{sold_qty}주` (보유 비중 50% 분할 매도)
• *잔여수량*: `{rem_qty}주` (트레일링 스탑 가동)

🛡️ *[리스크 관리 업데이트]*
남은 {rem_qty}주의 손절 기준가를 `매수가 {int(entry_price):,}원`으로 상향했습니다.
👉 *원금 보존 모드(Break-Even Safe)가 활성화되었습니다!*"""
        self.send_message(msg)

    def notify_trailing_exit(self, code: str, exit_price: float, total_pnl_won: int, total_pnl_pct: float):
        msg = f"""🏁 *[트레일링 익절 완료] 삼성전자 ({code})*
━━━━━━━━━━━━━━━━━━━━
⏰ *체결시간*: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
📍 *청산사유*: `최고점 대비 -0.5% 반납으로 전량 익절`

• *최종 매도가*: `{int(exit_price):,}원`
• *종합 수익률*: `+{total_pnl_pct:.2f}%`
• *종합 실현손익*: `+{total_pnl_won:,}원`

📈 *원칙에 따른 성공적인 포지션 마감입니다.*"""
        self.send_message(msg)

    def notify_stop_loss(self, code: str, loss_won: int, loss_pct: float, cooldown_min: int):
        msg = f"""🔴 *[손절 청산 실행] 삼성전자 ({code})*
━━━━━━━━━━━━━━━━━━━━
⏰ *체결시간*: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
📍 *손절원인*: `고정 손절선(-0.80%) 도달`

• *확정 손실*: `-{abs(loss_won):,}원` ({loss_pct:.2f}%)

⚠️ *[심리 방어 쿨다운 발동]*
• `{cooldown_min}분간` 뇌동매매 방지 쿨다운 타이머가 가동됩니다.
• 다음 매매 가능 시간: `{datetime.now().strftime('%H:%M:%S')} 이후`

☕ *"손실은 트레이딩의 정당한 운영비용입니다. 원칙을 지킨 훌륭한 컷이었습니다."*"""
        self.send_message(msg)

    def notify_daily_summary(self, total_trades: int, wins: int, losses: int, net_pnl: int, final_equity: int):
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        msg = f"""📊 *[일일 자동매매 결산 리포트]*
━━━━━━━━━━━━━━━━━━━━
📅 *일자*: `{datetime.now().strftime('%Y-%m-%d')}`
🤖 *봇 상태*: `장마감 정지 (IDLE_CLOSED)`

[매매 성과 요약]
• *총 거래 횟수*: `{total_trades}회` ({wins}승 {losses}패 / 승률 {win_rate:.1f}%)
• *당일 실현 손익*: `{'+' if net_pnl >= 0 else ''}{net_pnl:,}원`
• *마감 예수금*: `{final_equity:,}원`
• *미청산 포지션*: `0종목` (오버나이트 0%)

오늘 하루도 수고 많으셨습니다. 편안한 저녁 되세요! ✨"""
        self.send_message(msg)
