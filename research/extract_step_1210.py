import sys
import re
import json

sys.stdout.reconfigure(encoding='utf-8')

file_path = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\.system_generated\steps\1210\content.md"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

print("File size:", len(content))

# Look for data-initial-data or WIZ_global_data or AF_initDataCallback or any embedded JSON
matches = re.findall(r"AF_initDataCallback\((.*?)\);", content, re.DOTALL)
print("AF_initDataCallback count:", len(matches))

# Look for window.WIZ_global_data
wiz = re.findall(r"window\.WIZ_global_data\s*=\s*(\{.*?\});", content, re.DOTALL)
print("WIZ_global_data count:", len(wiz))

# Search for any large JSON arrays or script contents
scripts = re.findall(r"<script[^>]*>(.*?)</script>", content, re.DOTALL)
print("Total script tags:", len(scripts))

for i, s in enumerate(scripts):
    # Decode unicode escapes
    def decode_u(text):
        return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
    
    dec = decode_u(s)
    # Check for keywords
    keywords = ["전략", "매매", "조건", "삼성", "하이닉스", "15분봉", "3분봉", "5분봉", "VWAP", "이동평균", "익절", "손절", "퀀트", "백테스트", "키움", "HTS", "share", "prompt", "response"]
    found = [k for k in keywords if k in dec]
    if found:
        print(f"Script {i} (len {len(dec)}) matches keywords: {found}")
        # Print matching paragraphs
        paragraphs = re.findall(r'.{0,100}(?:' + '|'.join(found) + r').{0,100}', dec)
        for p in paragraphs[:10]:
            print("   >>>", p.strip())

# Search outside scripts (HTML body)
body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.DOTALL)
if body_match:
    body_text = body_match.group(1)
    body_clean = re.sub(r'<script.*?</script>', '', body_text, flags=re.DOTALL)
    body_clean = re.sub(r'<style.*?</style>', '', body_clean, flags=re.DOTALL)
    body_clean = re.sub(r'<[^>]+>', ' ', body_clean)
    print("\n--- BODY TEXT SAMPLE ---")
    print(body_clean[:1000])
