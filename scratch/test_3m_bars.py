import requests
import re
import pandas as pd
from datetime import datetime

def fetch_minute_bars(code: str, count: int = 6000) -> pd.DataFrame:
    url = f"https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe=minute&count={count}&requestType=0"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    text = r.content.decode('euc-kr', 'replace')
    raw_items = re.findall(r'<item data="([^"]+)"', text)
    
    rows = []
    for item in raw_items:
        parts = item.split('|')
        if len(parts) >= 6:
            dt_str, o, h, l, c, v = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
            close_val = float(c) if c != 'null' else 0.0
            open_val = float(o) if o != 'null' else close_val
            high_val = float(h) if h != 'null' else close_val
            low_val = float(l) if l != 'null' else close_val
            vol_val = int(v) if v != 'null' else 0
            
            try:
                dt = datetime.strptime(dt_str, "%Y%m%d%H%M")
                rows.append({
                    "DateTime": dt,
                    "Open": open_val,
                    "High": high_val,
                    "Low": low_val,
                    "Close": close_val,
                    "Volume": vol_val
                })
            except Exception:
                continue

    df_1m = pd.DataFrame(rows)
    if df_1m.empty:
        return pd.DataFrame()
        
    df_1m.set_index("DateTime", inplace=True)
    df_1m.sort_index(inplace=True)
    
    # 3-Minute Resampling: Open=first, High=max, Low=min, Close=last, Volume=sum
    df_3m = df_1m.resample("3min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    }).dropna()
    
    df_3m = df_3m.between_time("08:00", "20:00")
    return df_3m

if __name__ == "__main__":
    df_3m = fetch_minute_bars("005930", count=6000)
    print("Samsung 3M Bars count:", len(df_3m))
    print("Period:", df_3m.index[0], "to", df_3m.index[-1])
    print(df_3m.head())
    print(df_3m.tail())
