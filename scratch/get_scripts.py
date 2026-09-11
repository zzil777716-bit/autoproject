import requests
from bs4 import BeautifulSoup

url = 'https://gemini.google.com/share/1b6af13f2ac0?skid=7a707a14-e852-4ca1-9960-b13c9e05b76b'
r = requests.get(url)
soup = BeautifulSoup(r.text, 'html.parser')
for s in soup.find_all('script'):
    src = s.get('src')
    if src:
        print('src:', src)
    elif s.string and len(s.string) > 200:
        print('inline script len:', len(s.string), s.string[:100].replace('\n', ' '))
