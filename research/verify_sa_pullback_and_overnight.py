# -*- coding: utf-8 -*-
"""
research/verify_sa_pullback_and_overnight.py
================================================================================
S/A급 주도주 38개 종목 대상:
1. 수급 분석 및 포착 당시 진짜 주도주 여부 (당일 대금, 장중 고가)
2. 3분봉 20선 눌림목 진입 시 위로 최대 몇 % 올라갔는가 (Max MFE)
3. 오버나잇 성공 확률 (익일 갭, 익일 +3% 도달률, 클로드 보수 필터 적용 여부)
================================================================================
"""

import os
import sys
import glob
import json
import time
import shutil
import pandas as pd
import numpy as np
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

LOCAL_DATA_DIR = r"C:\Antigravity\data\종목데이터"
GDRIVE_DATA_DIR = r"G:\내 드라이브\Antigravity\종목데이터"

def analyze_stock_pullback_and_overnight(symbol, name, market, p_3m, threshold_eok):
    threshold_won = threshold_eok * 1e8
    
    res = {
        "종목코드": symbol,
        "종목명": name,
        "소속시장": market,
        "기준대금_억": threshold_eok,
        "총포착일수": 0,
        "진짜주도주일수": 0,
        "진짜주도주비율_%": 0.0,
        "평균당일최대상승_%": 0.0,
        "눌림진입성공수": 0,
        "눌림_평균최대상승_%": 0.0,
        "눌림_최고상승기록_%": 0.0,
        "눌림_3퍼익절승률_%": 0.0,
        "오버나잇_평균익일갭_%": 0.0,
        "오버나잇_익일갭상승확률_%": 0.0,
        "오버나잇_익일3퍼도달확률_%": 0.0,
        "클로드필터_오버나잇_승률_%": 0.0
    }
    
    if not os.path.exists(p_3m):
        return None
        
    df = pd.read_csv(p_3m, encoding="utf-8-sig")
    if df.empty or len(df) < 1000:
        return None
        
    df["DateTime"] = pd.to_datetime(df["DateTime"].astype(str), errors="coerce")
    df = df.dropna(subset=["DateTime"]).sort_values("DateTime").reset_index(drop=True)
    
    # 20이평 계산
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["Date"] = df["DateTime"].dt.strftime("%Y%m%d")
    df["Time"] = df["DateTime"].dt.strftime("%H%M%S")
    df["Val"] = df["Close"] * df["Volume"]
    
    unique_dates = sorted(df["Date"].unique())
    date_to_idx = {d: i for i, d in enumerate(unique_dates)}
    
    event_days = []
    
    grouped = df.groupby("Date")
    day_dfs = {d: g.reset_index(drop=True) for d, g in grouped}
    
    for date, day_df in day_dfs.items():
        if len(day_df) < 30: continue
        
        day_open = day_df["Open"].iloc[0]
        if day_open <= 0: continue
        
        valid_candles = day_df[(day_df["Time"] >= "090600") & (day_df["Time"] <= "143000") & (day_df["Val"] >= threshold_won)]
        if valid_candles.empty:
            continue
            
        trigger_idx = valid_candles.index[0]
        trigger_candle = day_df.iloc[trigger_idx]
        trigger_price = trigger_candle["Close"]
        
        gain_at_trigger = (trigger_price - day_open) / day_open * 100
        if gain_at_trigger < 1.0 or gain_at_trigger > 15.0 or trigger_candle["Close"] < trigger_candle["Open"]:
            continue
            
        day_high = day_df["High"].max()
        day_close = day_df["Close"].iloc[-1]
        day_val_total = day_df["Val"].sum() / 1e8
        max_day_gain = (day_high - day_open) / day_open * 100
        
        is_real_leader = (max_day_gain >= 8.0 and day_val_total >= 300.0)
        
        # 눌림목(20선 지지) 시뮬레이션
        after_trigger = day_df.iloc[trigger_idx + 1:]
        pullback_entered = False
        pullback_entry_price = 0
        pullback_max_mfe = 0.0
        pullback_won = False
        
        for p_idx, p_row in after_trigger.iterrows():
            ma = p_row["MA20"]
            if pd.isna(ma) or ma <= 0: continue
            
            # 20선 접근 및 지지 반등
            if p_row["Low"] <= ma * 1.005 and p_row["Close"] >= ma * 0.990:
                pullback_entered = True
                pullback_entry_price = p_row["Close"]
                
                future_bars = day_df.iloc[p_idx + 1:]
                if not future_bars.empty:
                    post_high = future_bars["High"].max()
                    pullback_max_mfe = (post_high - pullback_entry_price) / pullback_entry_price * 100
                    
                    gains = (future_bars["High"] - pullback_entry_price) / pullback_entry_price * 100
                    drops = (pullback_entry_price - future_bars["Low"]) / pullback_entry_price * 100
                    
                    t_hit = np.where(gains >= 3.25)[0]
                    s_hit = np.where(drops >= 2.75)[0]
                    
                    t_first = t_hit[0] if len(t_hit) > 0 else 999999
                    s_first = s_hit[0] if len(s_hit) > 0 else 999999
                    
                    if t_first < s_first:
                        pullback_won = True
                    elif s_first < t_first:
                        pullback_won = False
                    else:
                        pullback_won = ((future_bars["Close"].iloc[-1] - pullback_entry_price) / pullback_entry_price * 100 > 0)
                break
                
        # 오버나잇 시뮬레이션
        cur_d_idx = date_to_idx.get(date, -1)
        next_open_gap = 0.0
        next_day_max_gain = 0.0
        next_day_won = False
        claude_filter_pass = False
        claude_won = False
        
        if cur_d_idx >= 0 and cur_d_idx + 1 < len(unique_dates):
            next_date = unique_dates[cur_d_idx + 1]
            next_day_df = day_dfs.get(next_date)
            if next_day_df is not None and not next_day_df.empty:
                next_open = next_day_df["Open"].iloc[0]
                next_high = next_day_df["High"].max()
                
                next_open_gap = (next_open - day_close) / day_close * 100
                next_day_max_gain = (next_high - day_close) / day_close * 100
                next_day_won = (next_day_max_gain >= 3.0)
                
                day_range = day_high - day_df["Low"].min()
                if day_range > 0 and (day_close - day_df["Low"].min()) / day_range >= 0.65:
                    claude_filter_pass = True
                    claude_won = (next_day_max_gain >= 3.0 and next_open_gap >= -1.5)
                    
        event_days.append({
            "date": date,
            "is_real_leader": is_real_leader,
            "max_day_gain": max_day_gain,
            "day_val_total": day_val_total,
            "pullback_entered": pullback_entered,
            "pullback_max_mfe": pullback_max_mfe,
            "pullback_won": pullback_won,
            "next_open_gap": next_open_gap,
            "next_day_max_gain": next_day_max_gain,
            "next_day_won": next_day_won,
            "claude_filter_pass": claude_filter_pass,
            "claude_won": claude_won
        })
        
    if not event_days:
        return None
        
    total_events = len(event_days)
    real_leaders = sum(1 for e in event_days if e["is_real_leader"])
    avg_day_gain = np.mean([e["max_day_gain"] for e in event_days])
    
    pb_events = [e for e in event_days if e["pullback_entered"]]
    pb_count = len(pb_events)
    if pb_count > 0:
        avg_pb_mfe = np.mean([e["pullback_max_mfe"] for e in pb_events])
        max_pb_mfe = np.max([e["pullback_max_mfe"] for e in pb_events])
        pb_win_rate = sum(1 for e in pb_events if e["pullback_won"]) / pb_count * 100
    else:
        avg_pb_mfe, max_pb_mfe, pb_win_rate = 0.0, 0.0, 0.0
        
    avg_gap = np.mean([e["next_open_gap"] for e in event_days])
    gap_up_prob = sum(1 for e in event_days if e["next_open_gap"] > 0) / total_events * 100
    on_win_rate = sum(1 for e in event_days if e["next_day_won"]) / total_events * 100
    
    claude_events = [e for e in event_days if e["claude_filter_pass"]]
    if claude_events:
        claude_win_rate = sum(1 for e in claude_events if e["claude_won"]) / len(claude_events) * 100
    else:
        claude_win_rate = on_win_rate
        
    res["총포착일수"] = total_events
    res["진짜주도주일수"] = real_leaders
    res["진짜주도주비율_%"] = round((real_leaders / total_events) * 100, 1)
    res["평균당일최대상승_%"] = round(avg_day_gain, 1)
    res["눌림진입성공수"] = pb_count
    res["눌림_평균최대상승_%"] = round(avg_pb_mfe, 1)
    res["눌림_최고상승기록_%"] = round(max_pb_mfe, 1)
    res["눌림_3퍼익절승률_%"] = round(pb_win_rate, 1)
    res["오버나잇_평균익일갭_%"] = round(avg_gap, 2)
    res["오버나잇_익일갭상승확률_%"] = round(gap_up_prob, 1)
    res["오버나잇_익일3퍼도달확률_%"] = round(on_win_rate, 1)
    res["클로드필터_오버나잇_승률_%"] = round(claude_win_rate, 1)
    
    return res

def run_sa_verification():
    print("=" * 80)
    print("[Multi-Agent Council] 38개 S/A급 주도주 눌림목 최대상승폭 & 오버나잇 정밀 검증 가동")
    print(f">> 시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    with open(os.path.join(LOCAL_DATA_DIR, "350종목_고승률_주도주_기준치.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
        
    targets = []
    for sym, info in data.items():
        if "S급" in info["grade"] or "A급" in info["grade"]:
            mkt = info["market"]
            th = info["optimal_3m_threshold_eok"]
            name = info["name"]
            p3 = os.path.join(LOCAL_DATA_DIR, mkt, "3분봉", f"{sym}_{name}_3M.csv")
            if not os.path.exists(p3):
                p3_list = glob.glob(os.path.join(LOCAL_DATA_DIR, mkt, "3분봉", f"{sym}_*_3M.csv"))
                if p3_list: p3 = p3_list[0]
            targets.append((sym, name, mkt, p3, th, info["grade"]))
            
    print(f">> 검증 대상: S/A급 총 {len(targets)}개 종목")
    
    results = []
    for sym, name, mkt, p3, th, grade in targets:
        r = analyze_stock_pullback_and_overnight(sym, name, mkt, p3, th)
        if r:
            r["주도주등급"] = grade
            results.append(r)
            
    df_res = pd.DataFrame(results)
    df_res = df_res.sort_values(by=["눌림_3퍼익절승률_%", "클로드필터_오버나잇_승률_%"], ascending=[False, False]).reset_index(drop=True)
    
    excel_path = os.path.join(LOCAL_DATA_DIR, "38개_SA급_주도주_눌림목_오버나잇_정밀분석.xlsx")
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_res.to_excel(writer, sheet_name="눌림목_오버나잇_전수결과", index=False)
        s_df = df_res[df_res["주도주등급"].str.startswith("S급")]
        s_df.to_excel(writer, sheet_name="S급_주도주_정밀검증", index=False)
        
    print(f"[OK] [정밀분석 엑셀 저장 완료] {excel_path}")
    
    json_path = os.path.join(LOCAL_DATA_DIR, "38개_SA급_주도주_눌림목_오버나잇_요약.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(results, jf, ensure_ascii=False, indent=2)
    print(f"[OK] [요약 JSON 저장 완료] {json_path}")
    
    if os.path.exists(GDRIVE_DATA_DIR):
        try:
            shutil.copy2(excel_path, os.path.join(GDRIVE_DATA_DIR, os.path.basename(excel_path)))
            shutil.copy2(json_path, os.path.join(GDRIVE_DATA_DIR, os.path.basename(json_path)))
            print(f"[OK] [Google Drive 동기화 완료] {GDRIVE_DATA_DIR}")
        except Exception as e:
            print(f"[WARN] [Google Drive 동기화 주의] {e}")
            
    print("\n" + "=" * 80)
    print("[S/A급 주도주 눌림목 반등폭 & 오버나잇 성공률 Top 20]")
    print("=" * 80)
    show_cols = ["종목명", "소속시장", "기준대금_억", "진짜주도주비율_%", "평균당일최대상승_%", "눌림_평균최대상승_%", "눌림_최고상승기록_%", "눌림_3퍼익절승률_%", "오버나잇_익일3퍼도달확률_%", "클로드필터_오버나잇_승률_%"]
    print(df_res[show_cols].head(20).to_string(index=False))

if __name__ == "__main__":
    run_sa_verification()
