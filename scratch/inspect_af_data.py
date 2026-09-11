import requests
import json
import re
from bs4 import BeautifulSoup

url = 'https://gemini.google.com/share/1b6af13f2ac0?skid=7a707a14-e852-4ca1-9960-b13c9e05b76b'
r = requests.get(url)
soup = BeautifulSoup(r.text, 'html.parser')

scripts = soup.find_all('script')
for idx, s in enumerate(scripts):
    text = s.string or ''
    if 'AF_dataServiceRequests' in text or 'AF_initDataCallback' in text or 'ds:' in text:
        print(f"--- Script {idx} (len {len(text)}) ---")
        print(text[:300])

# Also check data attributes in html elements
for tag in soup.find_all(attrs={"data-id": True}):
    print("tag data-id:", tag.get("data-id"))

# Check for all strings that might contain the chat title or prompts
for script in scripts:
    text = script.string or ''
    if '1b6af13f2ac0' in text:
        print("Found share id in script len:", len(text))
