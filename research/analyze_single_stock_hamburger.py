# -*- coding: utf-8 -*-
"""
research/analyze_single_stock_hamburger.py
================================================================================
'햄버거' 기법 단일 종목 정밀 분석 및 노션(Notion) 업로드 포맷 생성기
================================================================================
사용자 호출: "[종목명/코드] 햄버거로 분석해" -> 즉시 해당 종목의 1년치 3분봉을 분석하여
1. 최적 기준 거래대금 및 주도주 등급
2. 돌파 / 눌림목 / 오버나잇 성적표 (MFE, 승률)
3. HTS 대조용 전체 포착일시 테이블
4. 노션(Notion) 바로 붙여넣기용 구조화 블록 출력
"""

import os
import sys
import glob
import json
import pandas as pd
import numpy as np
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

LOCAL_DATA_DIR = r"D:\ANTIGRAVITY(자동매매)\data\종목데이터"

def find_stock_file(query):
    query = str(query).strip()
    for market in ["코스닥150", "코스피200"]:
        p3_dir = os.path.join(LOCAL_DATA_DIR, market, "3분봉")
        if not os.path.exists(p3_dir): continue
        files = glob.glob(os.path.join(p3_dir, "*_3M.csv"))
        for f in files:
            fname = os.path.basename(f)
            if query in fname:
                parts = fname.replace("_3M.csv", "").split("_")
                sym = parts[0]
                name = parts[1] if len(parts) > 1 else sym
                return sym, name, market, f
    return None, None, None, None

def analyze_hamburger(query):
    sym, name, market, p3 = find_stock_file(query)
    if not p3:
        return f"❌ 종목 '{query}'의 3분봉 데이터를 찾을 수 없습니다."

    # 기준치 JSON에서 최적 기준대금 확인
    json_path = os.path.join(LOCAL_DATA_DIR, "350종목_고승률_주도주_기준치.json")
    threshold_eok = 50.0
    grade = "B급"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as jf:
            cache = json.load(jf)
            if sym in cache:
                threshold_eok = cache[sym]["optimal_3m_threshold_eok"]
                grade = cache[sym]["grade"]

    threshold_won = threshold_eok * 1e8

    df = pd.read_csv(p3, encoding="utf-8-sig")
    df["DateTime"] = pd.to_datetime(df["DateTime"].astype(str), errors="coerce")
    df = df.dropna(subset=["DateTime"]).sort_values("DateTime").reset_index(drop=True)
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["Date"] = df["DateTime"].dt.strftime("%Y%m%d")
    df["Time"] = df["DateTime"].dt.strftime("%H%M%S")
    df["Val"] = df["Close"] * df["Volume"]

    unique_dates = sorted(df["Date"].unique())
    date_to_idx = {d: i for i, d in enumerate(unique_dates)}
    day_dfs = {d: g.reset_index(drop=True) for d, g in df.groupby("Date")}

    # 20일 일평균 거래대금
    daily_vals = [day_dfs[d]["Val"].sum() for d in unique_dates[-20:] if d in day_dfs]
    adtv_20 = float(np.mean(daily_vals) / 1e8) if daily_vals else 0.0

    events = []
    for date, day_df in day_dfs.items():
        if len(day_df) < 30: continue
        day_open = day_df["Open"].iloc[0]
        if day_open <= 0: continue

        # 09:06 ~ 14:30 사이 기준대금 돌파 캔들
        valid_candles = day_df[(day_df["Time"] >= "090600") & (day_df["Time"] <= "143000") & (day_df["Val"] >= threshold_won)]
        if valid_candles.empty: continue

        trigger_idx = valid_candles.index[0]
        t_row = day_df.iloc[trigger_idx]
        t_price = t_row["Close"]

        gain_at_trigger = (t_price - day_open) / day_open * 100
        if gain_at_trigger < 1.0 or gain_at_trigger > 15.0 or t_row["Close"] < t_row["Open"]:
            continue

        day_high = int(day_df["High"].max())
        day_close = int(day_df["Close"].iloc[-1])
        day_val_total = day_df["Val"].sum() / 1e8
        max_day_gain = round((day_high - day_open) / day_open * 100, 1)

        is_real_leader = (max_day_gain >= 8.0 and day_val_total >= 300.0)

        # 돌파 결과
        after_trigger = day_df.iloc[trigger_idx + 1:]
        breakout_won = False
        if not after_trigger.empty:
            gains = (after_trigger["High"] - t_price) / t_price * 100
            drops = (t_price - after_trigger["Low"]) / t_price * 100
            t_hit = np.where(gains >= 3.25)[0]
            s_hit = np.where(drops >= 2.75)[0]
            t_f = t_hit[0] if len(t_hit) > 0 else 999999
            s_f = s_hit[0] if len(s_hit) > 0 else 999999
            breakout_won = (t_f < s_f)

        # 20선 눌림목
        pb_entered = False
        pb_price = 0
        pb_mfe = 0.0
        pb_won = False
        pb_time = "-"

        for p_idx, p_row in after_trigger.iterrows():
            ma = p_row["MA20"]
            if pd.isna(ma) or ma <= 0: continue
            if p_row["Low"] <= ma * 1.005 and p_row["Close"] >= ma * 0.990:
                pb_entered = True
                pb_price = int(p_row["Close"])
                pb_time = f"{str(p_row['Time'])[:2]}:{str(p_row['Time'])[2:4]}"
                future_bars = day_df.iloc[p_idx + 1:]
                if not future_bars.empty:
                    pb_mfe = round((future_bars["High"].max() - pb_price) / pb_price * 100, 1)
                    g_pb = (future_bars["High"] - pb_price) / pb_price * 100
                    d_pb = (pb_price - future_bars["Low"]) / pb_price * 100
                    t_pb = np.where(g_pb >= 3.25)[0]
                    s_pb = np.where(d_pb >= 2.75)[0]
                    t_f = t_pb[0] if len(t_pb) > 0 else 999999
                    s_f = s_pb[0] if len(s_pb) > 0 else 999999
                    pb_won = (t_f < s_f)
                break

        # 오버나잇
        cur_d_idx = date_to_idx.get(date, -1)
        next_open_gap = 0.0
        next_high_gain = 0.0
        on_won = False
        if cur_d_idx >= 0 and cur_d_idx + 1 < len(unique_dates):
            next_d = unique_dates[cur_d_idx + 1]
            next_df = day_dfs.get(next_d)
            if next_df is not None and not next_df.empty:
                next_open = next_df["Open"].iloc[0]
                next_high = next_df["High"].max()
                next_open_gap = round((next_open - day_close) / day_close * 100, 1)
                next_high_gain = round((next_high - day_close) / day_close * 100, 1)
                on_won = (next_high_gain >= 3.0)

        t_time_str = str(t_row["Time"])
        events.append({
            "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
            "time": f"{t_time_str[:2]}:{t_time_str[2:4]}",
            "val_eok": round(t_row["Val"] / 1e8, 1),
            "price": int(t_price),
            "gain_at_trigger": round(gain_at_trigger, 1),
            "day_high": day_high,
            "max_day_gain": max_day_gain,
            "is_real_leader": is_real_leader,
            "breakout_won": breakout_won,
            "pb_entered": pb_entered,
            "pb_time": pb_time,
            "pb_price": pb_price,
            "pb_mfe": pb_mfe,
            "pb_won": pb_won,
            "next_open_gap": next_open_gap,
            "next_high_gain": next_high_gain,
            "on_won": on_won
        })

    # 통계 집계
    total_cnt = len(events)
    real_leader_pct = round(sum(1 for e in events if e["is_real_leader"]) / total_cnt * 100, 1) if total_cnt else 0.0
    bo_win_rate = round(sum(1 for e in events if e["breakout_won"]) / total_cnt * 100, 1) if total_cnt else 0.0

    pb_list = [e for e in events if e["pb_entered"]]
    pb_cnt = len(pb_list)
    pb_avg_mfe = round(np.mean([e["pb_mfe"] for e in pb_list]), 1) if pb_cnt else 0.0
    pb_max_mfe = round(np.max([e["pb_mfe"] for e in pb_list]), 1) if pb_cnt else 0.0
    pb_win_rate = round(sum(1 for e in pb_list if e["pb_won"]) / pb_cnt * 100, 1) if pb_cnt else 0.0

    on_win_rate = round(sum(1 for e in events if e["on_won"]) / total_cnt * 100, 1) if total_cnt else 0.0
    on_avg_gap = round(np.mean([e["next_open_gap"] for e in events]), 1) if total_cnt else 0.0

    return {
        "symbol": sym,
        "name": name,
        "market": market,
        "adtv_20": adtv_20,
        "threshold_eok": threshold_eok,
        "grade": grade,
        "total_cnt": total_cnt,
        "real_leader_pct": real_leader_pct,
        "bo_win_rate": bo_win_rate,
        "pb_cnt": pb_cnt,
        "pb_avg_mfe": pb_avg_mfe,
        "pb_max_mfe": pb_max_mfe,
        "pb_win_rate": pb_win_rate,
        "on_win_rate": on_win_rate,
        "on_avg_gap": on_avg_gap,
        "events": events
    }

def format_notion_blocks(res):
    """노션(Notion) 업로드 및 복사용 마크다운 블록 생성"""
    md = []
    md.append(f"# 🍔 [햄버거 분석] {res['name']} ({res['symbol']})")
    md.append(f"> **소속 시장**: `{res['market']}` | **주도주 등급**: `{res['grade']}` | **20일 일평균 거래대금**: `{res['adtv_20']:.1f}억 원`")
    md.append("")
    md.append("## 📌 1. 햄버거 핵심 기준선 (Fuel Benchmark)")
    md.append(f"- 🔑 **3분봉 최적 기준 거래대금**: **`{res['threshold_eok']:.0f}억 원`**")
    md.append(f"- 🏆 **기준봉 발생 시 당일 진짜 주도주 등극률**: **`{res['real_leader_pct']}%`** (연간 {res['total_cnt']}회 발생)")
    md.append("")
    md.append("## 📊 2. 타점별 실전 성적표 (돌파 vs 눌림목 vs 오버나잇)")
    md.append("| 타점 유형 | 진입 기준 | 승률 (+3% 익절) | 핵심 지표 (반등폭 / 갭) | 권고 전략 |")
    md.append("| :--- | :--- | :---: | :--- | :--- |")
    md.append(f"| **돌파 매매** | 당일 등락률 ≤ 10% 낮은 자리 | **`{res['bo_win_rate']}%`** | 기준봉 종가 즉시 진입 | 적극 진입 타점 |")
    md.append(f"| **20선 눌림목** | 3분봉 20이평 터치 후 지지 | **`{res['pb_win_rate']}%`** | **평균 반등 +{res['pb_avg_mfe']}%** (최고 +{res['pb_max_mfe']}%) | 안전 지지 반등 타점 |")
    md.append(f"| **오버나잇** | 당일 종가 매수 후 익일 청산 | **`{res['on_win_rate']}%`** | 익일 평균 갭 {res['on_avg_gap']:+.1f}% | {'허용 (고가 마감 시)' if res['on_win_rate'] >= 55 else '🚫 금지 (당일 청산)'} |")
    md.append("")
    md.append("## 🗓️ 3. HTS 차트 대조용 전체 포착 일자·시간 타임라인")
    md.append("| 포착일자 | 포착시간 | 3분봉 거래대금 | 진입가격 | 당일 최고가 | 20선 눌림시각 | 눌림 후 최대상승폭 | 돌파 결과 | 눌림목 결과 | 오버나잇 결과 |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for e in res["events"]:
        bo_res = "✅ 익절" if e["breakout_won"] else "❌ 손절"
        pb_res = "✅ 성공" if e["pb_won"] else ("❌ 실패" if e["pb_entered"] else "-")
        on_res = "✅ 성공" if e["on_won"] else "미달"
        md.append(f"| {e['date']} | {e['time']} | **{e['val_eok']}억** | {e['price']:,}원 | {e['day_high']:,}원 (+{e['max_day_gain']}%) | {e['pb_time']} | **+{e['pb_mfe']}%** | {bo_res} | {pb_res} | {on_res} |")
    return "\n".join(md)

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "레인보우로보틱스"
    res = analyze_hamburger(q)
    if isinstance(res, dict):
        print(format_notion_blocks(res))
    else:
        print(res)
