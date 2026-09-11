import urllib.request
import urllib.parse
import json
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

share_id = "Z9iMrUloicFW"
url = "https://gemini.google.com/_/BardChatUi/data/batchexecute"

# Potential RPC IDs for GetSharedChat in Google Bard/Gemini
rpc_candidates = ["fK5qq", "D6AUpd", "v9vO7", "hOuadb", "b9bVef", "G9fV7", "F5r6Wd", "d8rV6e", "i8uJ2", "kO1V8", "w9vO7"]

# Let's search inside content.md for any rpcid or share rpc names
file_path = r"C:\Users\HONG\.gemini\antigravity\brain\b201b829-ba8c-4b1a-82e5-8fa15dc4f939\.system_generated\steps\1210\content.md"
with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# Look for rpc mappings like: "fK5qq":... or "share":...
found_rpcs = re.findall(r'"([A-Za-z0-9_]{5,7})":\s*\[?"(?:rpc|data|batchexecute)', html)
print("Found potential RPCs in HTML:", set(found_rpcs))

# Also search for 'share' in JS bundle names or data
share_matches = re.findall(r'[a-zA-Z0-9_]{5,7}(?=[",\':\s]+[^"]*?[sS]hare)', html)
print("Share related identifiers:", set(share_matches[:20]))

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "Referer": f"https://gemini.google.com/share/{share_id}"
}

for rpc in rpc_candidates:
    req_data = f'[[["{rpc}", "{json.dumps([share_id]).replace(chr(34), chr(92)+chr(34))}", null, "generic"]]]'
    body = urllib.parse.urlencode({"f.req": req_data}).encode('utf-8')
    req = urllib.request.Request(f"{url}?rpcids={rpc}", data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp_text = resp.read().decode('utf-8')
            if len(resp_text) > 100 and "null" not in resp_text[:50]:
                print(f"RPC {rpc} SUCCESS! Response length: {len(resp_text)}")
                print(resp_text[:500])
            else:
                pass
    except Exception as e:
        pass
