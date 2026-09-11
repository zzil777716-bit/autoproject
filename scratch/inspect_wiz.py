import requests
import json
import re
from bs4 import BeautifulSoup

url = 'https://gemini.google.com/share/1b6af13f2ac0?skid=7a707a14-e852-4ca1-9960-b13c9e05b76b'
r = requests.get(url)
m = re.search(r'window\.WIZ_global_data\s*=\s*(\{.*?\});', r.text, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print("WIZ_global_data keys:", list(data.keys()))
    for k, v in data.items():
        if isinstance(v, str) and len(v) > 50:
            print(f"Key {k} (len {len(v)}):", v[:150].replace('\n', ' '))
        elif isinstance(v, (list, dict)):
            print(f"Key {k} ({type(v).__name__}):", str(v)[:150])
