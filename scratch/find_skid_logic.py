import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

js_url = "https://gemini.gstatic.com/_/mss/boq-bard-web/_/js/k=boq-bard-web.BardChatUi.en_US.G9Pe0NXST2E.2018.O/am=CQFo-A7A9v0GsImCX4SDAQkwoRcC-AAAAAAIAQ/d=1/excm=_b/ed=1/dg=0/br=1/wt=2/ujg=1/rs=AL3bBk3BEJMBFhkazeiGoh6l8Wwv75zQ8Q/ee=DGWCxb:CgYiQ;EmZ2Bf:zr1jrb;NJ1rfe:yGfSdd;Pjplud:PoEs9b;QGR0gd:Mlhmy;ScI3Yc:e7Hzgb;UYRIEb:HzTAQc;YIZmRd:A1yn5d;cEt90b:ws9Tlc;dIoSBb:SpsfSb;dowIGb:ebZ3mb;eBAeSb:zbML3c;iFQyKf:vfuNJf;oGtAuc:sOXFj;qQEoOc:KUM7Z;qddgKe:xQtZb;wNp4Gc:k56rsf;wR5FRb:siKnQd;yxTchf:KUM7Z/dti=1/m=_b"
r = requests.get(js_url)
print("JS length:", len(r.text))

# Search for skid occurrences
skid_indices = [m.start() for m in re.finditer(r'skid', r.text)]
print("skid occurrences:", len(skid_indices))
for idx in skid_indices:
    print("--- skid snippet ---")
    print(r.text[max(0, idx-100):min(len(r.text), idx+150)])

# Search for /share/ or share_id
share_indices = [m.start() for m in re.finditer(r'share/\w+', r.text)]
print("/share/ occurrences:", len(share_indices))
for idx in share_indices[:5]:
    print("--- share snippet ---")
    print(r.text[max(0, idx-80):min(len(r.text), idx+120)])
