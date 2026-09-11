import requests
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

share_id = "1b6af13f2ac0"
url = f"https://gemini.google.com/share/{share_id}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}

r = requests.get(url, headers=headers)
print("Page length:", len(r.text))

# Let's extract SNlM0e (at token) or similar tokens from r.text
snlm = re.findall(r'"SNlM0e":"([^"]+)"', r.text)
at_token = snlm[0] if snlm else ""
print("Found SNlM0e token:", bool(at_token))

# In Gemini shared chats, the RPC to fetch shared chat is often 'K9nSxe' or 'hXbMfd' or 'ut78Te' or 'H9Vu7e'
# Let's search in JS bundles for the RPC that takes shareId
js_urls = re.findall(r'https://gemini\.gstatic\.com/_/mss/boq-bard-web/_/js/[^"]+', r.text)
print("Found JS URLs:", len(js_urls))

target_rpc = None
for j_url in js_urls[:3]:
    j_resp = requests.get(j_url, headers=headers)
    found = re.findall(r'(\w+),\["share/(\w+)"', j_resp.text)
    if found:
        print("Found share RPC mapping:", found)
    # Search for shareId references
    matches = re.findall(r'"([a-zA-Z0-9_]{5,8})",null,\[null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]', j_resp.text)

# Let's try known Bard/Gemini share RPCs:
# Known RPC for get shared chat: 'f9QDxe' or 'hXbMfd' or 'K9nSxe'
rpc_candidates = ['hXbMfd', 'F9QDxe', 'K9nSxe', 'Zz6yMe', 'G6gHve', 'G2L0Eb', 'c4rGec']

for rpc in rpc_candidates:
    req_data = [rpc, json.dumps([share_id]), None, "generic"]
    payload = {
        'f.req': json.dumps([[req_data]]),
        'at': at_token
    }
    batch_url = "https://gemini.google.com/_/BardChatUi/data/batchexecute"
    res = requests.post(batch_url, data=payload, headers=headers)
    if res.status_code == 200 and len(res.text) > 100:
        print(f"RPC {rpc} response len:", len(res.text))
        # Check if contains korean
        korean = re.findall(r'[\uac00-\ud7a3]{2,}', res.text)
        if korean:
            print(f"  -> SUCCESS with RPC {rpc}! Found {len(korean)} Korean words!")
            with open("scratch/gemini_share_response.txt", "w", encoding="utf-8") as out_f:
                out_f.write(res.text)
            break
