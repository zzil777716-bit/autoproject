import sys
import re
import json

sys.stdout.reconfigure(encoding='utf-8')

file_path = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\.system_generated\steps\1188\content.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

scripts = re.findall(r"<script[^>]*>(.*?)</script>", content, re.DOTALL)

for i in [0, 4, 9, 10, 14]:
    s = scripts[i]
    print(f"=== SCRIPT {i} ===")
    def decode_match(m):
        try:
            return chr(int(m.group(1), 16))
        except Exception:
            return m.group(0)
    decoded_s = re.sub(r'\\u([0-9a-fA-F]{4})', decode_match, s)
    # Print first 2000 chars of decoded_s
    print(decoded_s[:1500])
    print("...")
    # Also search for 'share' or conversation content
    lines = decoded_s.split('\n')
    for line in lines:
        if any(keyword in line for keyword in ['삼성', '하이닉스', '전략', '매매', '조건', '15분봉', 'VWAP', '이평선', '일목', '주식', '퀀트', '손익비']):
            print("FOUND KEYWORD LINE:", line[:300])
