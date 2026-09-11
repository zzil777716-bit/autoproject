# -*- coding: utf-8 -*-
"""
research/scan_optimal_3m_thresholds.py
================================================================================
350개 전 종목 대상 3분봉 '최적 성공률 기준 거래대금' 정밀 탐색 엔진
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
from concurrent.futures import ProcessPoolExecutor, as_completed

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

LOCAL_DATA_DIR = r"C:\Antigravity\data\종목데이터"
GDRIVE_DATA_DIR = r"G:\내 드라이브\Antigravity\종목데이터"

def evaluate_single_stock(symbol, name, market, p_3m):
    result = {
        "종목코드": symbol,
        "종목명": name,
        "소속시장": market,
        "상태": "정상",
        "20일평균거래대금_억": 0.0,
        "최적_3분봉기준대금_억": 0.0,
        "연간_신호수": 0,
        "성공률_%": 0.0,
        "평균손익_%": 0.0,
        "기대값": 0.0,
        "평시중위_3분봉_백만": 0.0,
        "1년_최대3분봉_억": 0.0,
        "주도주_등급": "제외"
    }

    try:
        if not os.path.exists(p_3m):
            result["상태"] = "데이터없음"
            return result
            
        df = pd.read_csv(p_3m, encoding="utf-8-sig")
        if df.empty or len(df) < 1000:
            result["상태"] = "데이터부족"
            return result
            
        # Parse datetime
        df["DateTime"] = pd.to_datetime(df["DateTime"].astype(str), errors="coerce")
        df = df.dropna(subset=["DateTime"]).sort_values("DateTime").reset_index(drop=True)
        
        dates = df["DateTime"].dt.strftime("%Y%m%d").values
        times = df["DateTime"].dt.strftime("%H%M%S").values
        opens = df["Open"].values.astype(float)
        highs = df["High"].values.astype(float)
        lows = df["Low"].values.astype(float)
        closes = df["Close"].values.astype(float)
        volumes = df["Volume"].values.astype(float)
        vals = closes * volumes
        
        # 1. 일평균 거래대금
        unique_dates = np.unique(dates)
        daily_vals = [np.sum(vals[dates == dt]) for dt in unique_dates[-20:]]
        adtv_20 = float(np.mean(daily_vals) / 1e8) if daily_vals else 0.0
        result["20일평균거래대금_억"] = round(adtv_20, 1)
        
        # 2. 저유동성 종목 스킵 (일평균 100억 미만)
        if adtv_20 < 100.0:
            result["상태"] = "거래저조_스킵"
            return result
            
        # 3분봉 통계
        p50 = float(np.percentile(vals, 50) / 1e6)
        max_val = float(np.max(vals) / 1e8)
        result["평시중위_3분봉_백만"] = round(p50, 1)
        result["1년_최대3분봉_억"] = round(max_val, 1)
        
        # 3. 그리드 후보군 생성
        grid_base = [5, 10, 15, 20, 30, 50, 70, 100, 150, 200, 300, 500]
        # 해당 종목 최대치보다 작은 후보만 선택
        candidate_thresholds = [g for g in grid_base if g <= max_val * 0.9 and g >= 5]
        if not candidate_thresholds:
            candidate_thresholds = [max(5, int(max_val * 0.3))]
            
        best_th = 0.0
        best_wr = 0.0
        best_cnt = 0
        best_avg = 0.0
        best_exp = -999.0
        
        # 4. 시뮬레이션
        for th in candidate_thresholds:
            th_won = th * 1e8
            trades = []
            
            for dt in unique_dates:
                mask = (dates == dt)
                t_arr = times[mask]
                v_arr = vals[mask]
                c_arr = closes[mask]
                h_arr = highs[mask]
                l_arr = lows[mask]
                o_arr = opens[mask]
                
                day_open = o_arr[0]
                if day_open <= 0: continue
                
                for i in range(len(c_arr)):
                    t_str = t_arr[i]
                    if t_str < '090600' or t_str > '143000': continue
                    if v_arr[i] < th_won: continue
                    
                    # 당일 상승률 1% ~ 12% (낮은 구간 돌파)
                    gain_from_open = (c_arr[i] - day_open) / day_open * 100
                    if gain_from_open < 1.0 or gain_from_open > 12.0: continue
                    if c_arr[i] < o_arr[i]: continue # 양봉만
                    
                    # RVOL: 직전 5봉 평균 대비 2.0배 이상
                    if i >= 5:
                        p_val = np.mean(v_arr[max(0, i-5):i])
                        if p_val > 0 and (v_arr[i] / p_val) < 2.0: continue
                        
                    entry_p = c_arr[i]
                    future_h = h_arr[i+1:]
                    future_l = l_arr[i+1:]
                    if len(future_h) == 0: break
                    
                    gains = (future_h - entry_p) / entry_p * 100
                    drops = (entry_p - future_l) / entry_p * 100
                    
                    hit_target = np.where(gains >= 3.25)[0] # +3% 익절 (수수료 0.25% 반영)
                    hit_stop = np.where(drops >= 2.75)[0]   # -2.5% 손절
                    
                    t_idx = hit_target[0] if len(hit_target) > 0 else 999999
                    s_idx = hit_stop[0] if len(hit_stop) > 0 else 999999
                    
                    won = False
                    ret = 0.0
                    if t_idx < s_idx:
                        won = True
                        ret = 3.0
                    elif s_idx < t_idx:
                        won = False
                        ret = -2.5
                    else:
                        ret = (c_arr[-1] - entry_p) / entry_p * 100 - 0.25
                        won = (ret > 0)
                        
                    trades.append({"won": won, "ret": ret})
                    break # 하루 1회
                    
            if len(trades) >= 8:
                w_count = sum(1 for t in trades if t["won"])
                w_rate = (w_count / len(trades)) * 100
                avg_ret = float(np.mean([t["ret"] for t in trades]))
                exp = avg_ret * (w_rate / 100)
                
                # 승률 60% 이상 우선, 또는 기대값 최대
                if w_rate >= 60.0 and exp > best_exp:
                    best_th = th
                    best_wr = w_rate
                    best_cnt = len(trades)
                    best_avg = avg_ret
                    best_exp = exp
                elif best_th == 0.0 and w_rate > best_wr:
                    best_th = th
                    best_wr = w_rate
                    best_cnt = len(trades)
                    best_avg = avg_ret
                    best_exp = exp

        if best_th > 0:
            result["최적_3분봉기준대금_억"] = round(best_th, 1)
            result["연간_신호수"] = best_cnt
            result["성공률_%"] = round(best_wr, 1)
            result["평균손익_%"] = round(best_avg, 2)
            result["기대값"] = round(best_exp, 2)
            
            if best_wr >= 70.0:
                result["주도주_등급"] = "S급 주도주 (승률 70%+)"
            elif best_wr >= 60.0:
                result["주도주_등급"] = "A급 핵심주 (승률 60%+)"
            elif best_wr >= 50.0:
                result["주도주_등급"] = "B급 일반주"
            else:
                result["주도주_등급"] = "C급 부적합"
        else:
            result["상태"] = "신호부족_스킵"

    except Exception as e:
        result["상태"] = f"에러: {e}"

    return result

def run_all():
    print("=" * 80)
    print("[Multi-Agent Council] 350종목 3분봉 최적 성공률 기준 거래대금 전수 탐색 가동")
    print(f">> 시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    tasks = []
    for market in ["코스피200", "코스닥150"]:
        p_dir = os.path.join(LOCAL_DATA_DIR, market, "3분봉")
        if not os.path.exists(p_dir): continue
        for f in glob.glob(os.path.join(p_dir, "*_3M.csv")):
            fname = os.path.basename(f).replace("_3M.csv", "")
            parts = fname.split("_")
            sym = parts[0]
            name = parts[1] if len(parts) > 1 else sym
            tasks.append((sym, name, market, f))
            
    print(f">> 총 탐색 대상 종목 수: {len(tasks)}개")
    
    workers = min(os.cpu_count() or 4, 8)
    print(f">> 멀티프로세싱 가동 (Worker: {workers})...")
    
    results = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(evaluate_single_stock, sym, name, mkt, p3): sym for sym, name, mkt, p3 in tasks}
        done = 0
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            done += 1
            if done % 50 == 0 or done == len(tasks):
                print(f"   • 분석 진행률: {done}/{len(tasks)} ({done/len(tasks)*100:.1f}%)")
                
    elapsed = time.time() - t0
    print(f">> 전수 탐색 완료! 소요 시간: {elapsed:.2f}초")
    
    df_all = pd.DataFrame(results)
    # 정렬: 성공률 내림차순, 기대값 내림차순
    valid_df = df_all[df_all["상태"] == "정상"].sort_values(by=["성공률_%", "기대값"], ascending=[False, False]).reset_index(drop=True)
    skipped_df = df_all[df_all["상태"] != "정상"].reset_index(drop=True)
    
    print(f">> [결과 요약] 유효 분석 종목: {len(valid_df)}개, 거래저조/스킵 종목: {len(skipped_df)}개")
    
    # 엑셀 저장
    excel_path = os.path.join(LOCAL_DATA_DIR, "350종목_성공률_최적_3분봉_기준거래대금.xlsx")
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        valid_df.to_excel(writer, sheet_name="최적기준대금_랭킹", index=False)
        
        # S/A급 주도주 시트
        top_df = valid_df[valid_df["주도주_등급"].str.startswith(("S급", "A급"))]
        top_df.to_excel(writer, sheet_name="S_A급_고승률_주도주", index=False)
        
        skipped_df.to_excel(writer, sheet_name="거래저조_스킵종목", index=False)
    print(f"[OK] [마스터 엑셀 저장 완료] {excel_path}")
    
    # JSON 저장 (S/A급 주도주 캐싱)
    top_dict = {}
    for _, r in valid_df.iterrows():
        top_dict[r["종목코드"]] = {
            "name": r["종목명"],
            "market": r["소속시장"],
            "adtv_20_eok": r["20일평균거래대금_억"],
            "optimal_3m_threshold_eok": r["최적_3분봉기준대금_억"],
            "annual_signals": r["연간_신호수"],
            "win_rate": r["성공률_%"],
            "avg_ret": r["평균손익_%"],
            "expectancy": r["기대값"],
            "grade": r["주도주_등급"]
        }
    json_path = os.path.join(LOCAL_DATA_DIR, "350종목_고승률_주도주_기준치.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(top_dict, jf, ensure_ascii=False, indent=2)
    print(f"[OK] [주도주 JSON 저장 완료] {json_path}")
    
    # 구글 드라이브 동기화
    if os.path.exists(GDRIVE_DATA_DIR):
        try:
            shutil.copy2(excel_path, os.path.join(GDRIVE_DATA_DIR, os.path.basename(excel_path)))
            shutil.copy2(json_path, os.path.join(GDRIVE_DATA_DIR, os.path.basename(json_path)))
            print(f"[OK] [Google Drive 동기화 완료] {GDRIVE_DATA_DIR}")
        except Exception as e:
            print(f"[WARN] [Google Drive 동기화 주의] {e}")

    # 상위 20개 출력
    print("\n" + "=" * 80)
    print("[성공률 Top 20 주도주 및 3분봉 최적 기준 거래대금]")
    print("=" * 80)
    cols = ["종목코드", "종목명", "소속시장", "20일평균거래대금_억", "최적_3분봉기준대금_억", "연간_신호수", "성공률_%", "기대값", "주도주_등급"]
    print(valid_df[cols].head(20).to_string(index=False))


if __name__ == "__main__":
    run_all()
