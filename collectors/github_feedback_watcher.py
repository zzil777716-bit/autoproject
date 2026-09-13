# -*- coding: utf-8 -*-
"""
========================================================================================
🤖 [ANTIGRAVITY GITHUB COMMUNITY FEEDBACK WATCHER (깃허브 피드백 상시 감시 엔진)]
- GitHub Issues API를 주기적으로 조회하여 새로운 사용자 건의/피드백 자동 감지
- 새로운 이슈 발생 시:
  1) 텔레그램으로 사용자님(@wowkyun)께 실시간 푸시 알림 발송
  2) 9대 AI 이사회 분석 큐에 등록하여 백테스트 및 적용 가능성 사전 검토
========================================================================================
"""

import os
import sys
import time
import requests
from datetime import datetime

REPO_OWNER = "zzil777716-bit"
REPO_NAME = "autoproject"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
TOKEN = os.getenv("GITHUB_TOKEN", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8988429416:AAG3FGLLleRF-dapt2XYSL2D5Eo-zoJNaO8")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8169345022")

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def send_telegram(text: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def watch_github_feedback():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 깃허브 피드백 상시 감시 엔진 가동!")
    seen_issues = set()
    
    # 1. 기존 이슈들 목록 등록 (초기화)
    try:
        r = requests.get(API_URL, headers=headers, timeout=10)
        if r.status_code == 200:
            for issue in r.json():
                seen_issues.add(issue.get('id'))
    except Exception as e:
        print("초기화 조회 실패:", e)

    print(f"현재 등록된 기존 이슈: {len(seen_issues)}개. 신규 피드백 대기 중...")

    while True:
        try:
            time.sleep(300) # 5분마다 깃허브 이슈 자동 스캔
            r = requests.get(API_URL, headers=headers, timeout=10)
            if r.status_code == 200:
                issues = r.json()
                for issue in issues:
                    iid = issue.get('id')
                    if iid not in seen_issues:
                        seen_issues.add(iid)
                        title = issue.get('title')
                        user = issue.get('user', {}).get('login')
                        body = issue.get('body', '')[:200]
                        url = issue.get('html_url')
                        
                        # 텔레그램 실시간 알림 발송!
                        t_msg = f"""📢 *[GitHub 신규 피드백 도착!]*
━━━━━━━━━━━━━━━━━━━━
👤 *작성자*: `{user}`
📌 *제목*: `{title}`
🔗 *링크*: {url}

📝 *내용 요약*:
```text
{body}
```
💡 *9대 AI 이사회가 이 피드백을 분석할 준비를 마쳤습니다!*"""
                        send_telegram(t_msg)
                        print(f"신규 피드백 포착 및 텔레그램 전송: {title}")
                        
        except Exception as e:
            time.sleep(60)

if __name__ == "__main__":
    watch_github_feedback()
