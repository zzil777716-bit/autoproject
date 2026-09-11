# -*- coding: utf-8 -*-
"""
research/analyze_universe_350_stocks.py
================================================================================
코스피200 + 코스닥150 (350개 전 종목) 거래대금 및 시세 전수 분석 엔진
================================================================================
[핵심 분석 항목]
1. 종목별 고유 거래대금 기준 확보:
   - 20일/60일 일평균 거래대금 (ADTV-20, ADTV-60)
   - 3분봉 평시 중위 거래대금 (P50), 상위 90% 거래대금 (P90)
   - 3분봉 수급 기준봉 임계치 (P99 / 억원 단위)
   - 1년 내 단일 3분봉 역대 최대 거래대금 (All-Time Max 3M Volume)
2. 시세 추세 및 매물대(Volume Profile):
   - 일봉 20-60-120선 정배열 점수 (0~100점)
   - 15분봉 리샘플링 후 핵심 매물대(POC: Point of Control) 1, 2, 3차 지지저항선
3. 전략 적합도 및 주도주 등급화 (S/A/B/C)
4. 결과물 출력:
   - C:\Antigravity\data\종목데이터\350종목_거래대금_수급분석_마스터.xlsx
   - C:\Antigravity\data\종목데이터\350종목_거래대금_기준치.json
   - Google Drive 백업
"""

import os
import glob
import json
import time
import shutil
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

LOCAL_DATA_DIR = r"C:\Antigravity\data\종목데이터"
GDRIVE_DATA_DIR = r"G:\내 드라이브\Antigravity\종목데이터"

def analyze_single_stock(symbol, name, market, p_3m, p_daily):
    """단일 종목의 1년치 3분봉 및 일봉 데이터 정밀 퀀트 분석"""
    result = {
        "종목코드": symbol,
        "종목명": name,
        "소속시장": market,
        "분석일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # 일봉 지표
        "최근종가": 0,
        "20일평균거래대금_억": 0.0,
        "60일평균거래대금_억": 0.0,
        "거래대금가속도_5D_vs_20D": 0.0,
        "일봉정배열점수": 0,
        "52주고점대비_이격도_%": 0.0,
        # 3분봉 지표
        "3분봉_총캔들수": 0,
        "3분봉_평시중위거래대금_백만": 0.0,
        "3분봉_P90_거래대금_백만": 0.0,
        "3분봉_수급기준봉_임계치_억": 0.0,
        "3분봉_1년최대거래대금_억": 0.0,
        "수급기준봉_발생빈도_1년회수": 0,
        # 매물대 및 지지저항
        "1차핵심지지저항_POC1": 0,
        "2차핵심지지저항_POC2": 0,
        "주도주등급": "C",
        "자동매매_추천전략": "관망"
    }

    try:
        # 1. 일봉 분석
        if os.path.exists(p_daily):
            df_d = pd.read_csv(p_daily, encoding="utf-8-sig")
            if not df_d.empty and len(df_d) >= 20:
                if "Date" in df_d.columns:
                    df_d["Date"] = pd.to_datetime(df_d["Date"])
                    df_d = df_d.sort_values("Date").reset_index(drop=True)
                
                close = df_d["Close"].values
                vol = df_d["Volume"].values
                val = close * vol  # 추정 거래대금 (원)

                curr_close = int(close[-1])
                result["최근종가"] = curr_close
                
                # ADTV 계산 (억원)
                adtv_20 = float(np.mean(val[-20:]) / 1e8) if len(val) >= 20 else 0.0
                adtv_60 = float(np.mean(val[-60:]) / 1e8) if len(val) >= 60 else adtv_20
                adtv_5 = float(np.mean(val[-5:]) / 1e8) if len(val) >= 5 else adtv_20
                
                result["20일평균거래대금_억"] = round(adtv_20, 1)
                result["60일평균거래대금_억"] = round(adtv_60, 1)
                result["거래대금가속도_5D_vs_20D"] = round(adtv_5 / (adtv_20 + 1e-6), 2)
                
                # 52주 고점 대비
                high_52w = np.max(close[-250:]) if len(close) >= 250 else np.max(close)
                result["52주고점대비_이격도_%"] = round((curr_close - high_52w) / high_52w * 100, 1)
                
                # 정배열 점수 계산 (20, 60, 120 이평)
                score = 0
                if len(close) >= 120:
                    ma20 = np.mean(close[-20:])
                    ma60 = np.mean(close[-60:])
                    ma120 = np.mean(close[-120:])
                    if curr_close > ma20: score += 25
                    if ma20 > ma60: score += 35
                    if ma60 > ma120: score += 40
                elif len(close) >= 60:
                    ma20 = np.mean(close[-20:])
                    ma60 = np.mean(close[-60:])
                    if curr_close > ma20: score += 40
                    if ma20 > ma60: score += 60
                result["일봉정배열점수"] = score

        # 2. 3분봉 분석
        if os.path.exists(p_3m):
            df_3m = pd.read_csv(p_3m, encoding="utf-8-sig")
            if not df_3m.empty and len(df_3m) > 100:
                result["3분봉_총캔들수"] = len(df_3m)
                
                c_3m = df_3m["Close"].values
                v_3m = df_3m["Volume"].values
                val_3m = c_3m * v_3m  # 3분봉 거래대금 (원)
                
                # 백분위수 거래대금
                p50_val = float(np.percentile(val_3m, 50) / 1e6)  # 백만원
                p90_val = float(np.percentile(val_3m, 90) / 1e6)  # 백만원
                p99_val = float(np.percentile(val_3m, 99) / 1e8)  # 억원
                max_val = float(np.max(val_3m) / 1e8)             # 억원
                
                result["3분봉_평시중위거래대금_백만"] = round(p50_val, 1)
                result["3분봉_P90_거래대금_백만"] = round(p90_val, 1)
                result["3분봉_수급기준봉_임계치_억"] = round(p99_val, 2)
                result["3분봉_1년최대거래대금_억"] = round(max_val, 1)
                
                # 수급 기준봉 발생 횟수 (임계치 초과 봉 수)
                anchor_count = int(np.sum(val_3m >= (p99_val * 1e8)))
                result["수급기준봉_발생빈도_1년회수"] = anchor_count
                
                # 매물대 분석 (Volume Profile - POC 1, 2)
                bins = 50
                hist, bin_edges = np.histogram(c_3m, bins=bins, weights=v_3m)
                top_indices = np.argsort(hist)[::-1]
                
                poc1 = int((bin_edges[top_indices[0]] + bin_edges[top_indices[0] + 1]) / 2)
                poc2 = int((bin_edges[top_indices[1]] + bin_edges[top_indices[1] + 1]) / 2) if len(top_indices) > 1 else poc1
                
                result["1차핵심지지저항_POC1"] = poc1
                result["2차핵심지지저항_POC2"] = poc2

        # 3. 주도주 등급 판정 및 최적 전략 매칭
        adtv = result["20일평균거래대금_억"]
        p99 = result["3분봉_수급기준봉_임계치_억"]
        score = result["일봉정배열점수"]

        if adtv >= 500 and score >= 60 and p99 >= 10.0:
            result["주도주등급"] = "S급 (최우선 주도주)"
            result["자동매매_추천전략"] = "15분봉 3선 눌림목 & 3분봉 스퀴즈"
        elif adtv >= 200 and score >= 50 and p99 >= 5.0:
            result["주도주등급"] = "A급 (핵심 우량 수급주)"
            result["자동매매_추천전략"] = "기준봉 돌파 스캘핑 & 60선 반등"
        elif adtv >= 50:
            result["주도주등급"] = "B급 (일반 스윙 타겟)"
            result["자동매매_추천전략"] = "박스권 매물대(POC) 역추세"
        else:
            result["주도주등급"] = "C급 (유동성 부족 주의)"
            result["자동매매_추천전략"] = "매매 제외 (슬리피지 위험)"

    except Exception as e:
        result["주도주등급"] = f"에러: {e}"

    return result

def run_universe_analysis():
    print("=" * 80)
    print("🏛️ [Multi-Agent Council] 코스피200 & 코스닥150 350개 전 종목 거래대금 전수 분석 가동")
    print(f">> 분석 시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    tasks = []
    for market in ["코스피200", "코스닥150"]:
        market_dir = os.path.join(LOCAL_DATA_DIR, market)
        p_3m_dir = os.path.join(market_dir, "3분봉")
        p_d_dir = os.path.join(market_dir, "일봉")
        
        if not os.path.exists(p_3m_dir):
            continue
            
        csv_3m_files = glob.glob(os.path.join(p_3m_dir, "*_3M.csv"))
        for f3m in csv_3m_files:
            fname = os.path.basename(f3m)
            parts = fname.replace("_3M.csv", "").split("_")
            sym = parts[0]
            name = parts[1] if len(parts) > 1 else sym
            
            # 매칭되는 일봉 파일 경로
            fdaily = os.path.join(p_d_dir, f"{sym}_{name}.csv")
            if not os.path.exists(fdaily):
                fdaily = os.path.join(p_d_dir, f"{sym}.csv")
                
            tasks.append((sym, name, market, f3m, fdaily))

    print(f">> 총 분석 대상 종목 수: {len(tasks)}개 종목")
    
    start_time = time.time()
    results = []
    
    max_workers = min(os.cpu_count() or 4, 8)
    print(f">> 멀티프로세싱 가동 (Worker 수: {max_workers})...")
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_single_stock, sym, name, mkt, p3, pd_): sym for sym, name, mkt, p3, pd_ in tasks}
        completed = 0
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            completed += 1
            if completed % 50 == 0 or completed == len(tasks):
                print(f"   • 분석 진행도: {completed}/{len(tasks)} ({completed/len(tasks)*100:.1f}%)")

    elapsed = time.time() - start_time
    print(f">> 전수 분석 완료! 총 소요 시간: {elapsed:.2f}초")

    df_result = pd.DataFrame(results)
    if not df_result.empty:
        df_result = df_result.sort_values(by="20일평균거래대금_억", ascending=False).reset_index(drop=True)

        # 1. 엑셀 마스터 파일 저장
        excel_path = os.path.join(LOCAL_DATA_DIR, "350종목_거래대금_수급분석_마스터.xlsx")
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df_result.to_excel(writer, sheet_name="350종목_전체분석", index=False)
            
            df_leading = df_result[df_result["주도주등급"].str.startswith(("S급", "A급"))]
            df_leading.to_excel(writer, sheet_name="S_A급_핵심주도주", index=False)
            
            summary = df_result.groupby("소속시장").agg({
                "종목코드": "count",
                "20일평균거래대금_억": ["mean", "median", "max"],
                "3분봉_수급기준봉_임계치_억": ["mean", "max"]
            })
            summary.to_excel(writer, sheet_name="시장별_유동성_요약")

        print(f"✅ [마스터 엑셀 생성 완료] {excel_path}")

        # 2. 실시간 봇 캐싱용 JSON 저장
        threshold_cache = {}
        for _, row in df_result.iterrows():
            threshold_cache[row["종목코드"]] = {
                "name": row["종목명"],
                "market": row["소속시장"],
                "adtv_20_eok": row["20일평균거래대금_억"],
                "anchor_threshold_3m_eok": row["3분봉_수급기준봉_임계치_억"],
                "max_3m_eok": row["3분봉_1년최대거래대금_억"],
                "grade": row["주도주등급"],
                "poc1": row["1차핵심지지저항_POC1"],
                "poc2": row["2차핵심지지저항_POC2"],
                "trend_score": row["일봉정배열점수"]
            }
        
        json_path = os.path.join(LOCAL_DATA_DIR, "350종목_거래대금_기준치.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(threshold_cache, jf, ensure_ascii=False, indent=2)
        print(f"✅ [봇 캐싱용 JSON 생성 완료] {json_path}")

        # 3. 구글 드라이브 동기화
        if os.path.exists(GDRIVE_DATA_DIR):
            try:
                shutil.copy2(excel_path, os.path.join(GDRIVE_DATA_DIR, os.path.basename(excel_path)))
                shutil.copy2(json_path, os.path.join(GDRIVE_DATA_DIR, os.path.basename(json_path)))
                print(f"☁️ [Google Drive 동기화 완료] {GDRIVE_DATA_DIR}")
            except Exception as ge:
                print(f"⚠️ [Google Drive 동기화 주의] {ge}")

    return df_result

if __name__ == "__main__":
    run_universe_analysis()
