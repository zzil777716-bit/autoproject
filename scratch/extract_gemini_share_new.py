import re
import json
from bs4 import BeautifulSoup

file_path = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\.system_generated\steps\3153\content.md"

with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

# 1. Search for conversational text or Korean strings
korean_matches = re.findall(r'[\uac00-\ud7a30-9a-zA-Z\s\.,\?!:;%\(\)\[\]\-~_]{20,}', text)
print(f"Total potential Korean/text chunks: {len(korean_matches)}")

# Filter for relevant chunks mentioning trading, 거래대금, 분봉, 전략, 15분봉, etc.
relevant = []
keywords = ["거래대금", "3분봉", "15분봉", "정배열", "이격도", "시뮬레이션", "종목", "코스피", "코스닥", "기준", "매수", "매도", "수급", "대장주"]
for m in korean_matches:
    if any(k in m for k in keywords):
        relevant.append(m.strip())

print(f"Found {len(relevant)} relevant chunks:")
for idx, r in enumerate(relevant[:30], 1):
    print(f"\n--- [Chunk {idx}] ---")
    print(r[:500])
