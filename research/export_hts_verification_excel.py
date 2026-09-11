# -*- coding: utf-8 -*-
"""
research/export_hts_verification_excel.py
================================================================================
HTS 차트 대조 검증용: S/A급 38개 주도주 일자별·시간별 상세 포착 내역
- 엑셀 파일 1개에 종목별 시트로 분리 구성
- 각 시트별: 포착일자, 포착시간, 3분봉 거래대금, 진입가, 20선 눌림시각/가격, 반등폭, 오버나잇 결과 등
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
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

LOCAL_DATA_DIR = r"C:\Antigravity\data\종목데이터"
GDRIVE_DATA_DIR = r"G:\내 드라이브\Antigravity\종목데이터"

def sanitize_sheet_name(name):
    # Excel sheet name rules: max 31 chars, no : \ / ? * [ ]
    invalid_chars = [':', '\\', '/', '?', '*', '[', ']']
    for ch in invalid_chars:
        name = name.replace(ch, '_')
    return name[:31]

def get_stock_events(symbol, name, market, p_3m, threshold_eok):
    threshold_won = threshold_eok * 1e8
    events = []
    
    if not os.path.exists(p_3m):
        return events
        
    df = pd.read_csv(p_3m, encoding="utf-8-sig")
    if df.empty or len(df) < 1000:
        return events
        
    df["DateTime"] = pd.to_datetime(df["DateTime"].astype(str), errors="coerce")
    df = df.dropna(subset=["DateTime"]).sort_values("DateTime").reset_index(drop=True)
    
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["Date"] = df["DateTime"].dt.strftime("%Y%m%d")
    df["Time"] = df["DateTime"].dt.strftime("%H%M%S")
    df["Val"] = df["Close"] * df["Volume"]
    
    unique_dates = sorted(df["Date"].unique())
    date_to_idx = {d: i for i, d in enumerate(unique_dates)}
    
    grouped = df.groupby("Date")
    day_dfs = {d: g.reset_index(drop=True) for d, g in grouped}
    
    for date, day_df in day_dfs.items():
        if len(day_df) < 30: continue
        day_open = day_df["Open"].iloc[0]
        if day_open <= 0: continue
        
        # 09:06 ~ 14:30 사이 기준대금 돌파 캔들 탐색
        valid_candles = day_df[(day_df["Time"] >= "090600") & (day_df["Time"] <= "143000") & (day_df["Val"] >= threshold_won)]
        if valid_candles.empty:
            continue
            
        trigger_idx = valid_candles.index[0]
        trigger_row = day_df.iloc[trigger_idx]
        trigger_price = trigger_row["Close"]
        
        # 필터: 양봉 및 당일 상승률 1% ~ 15% 사이
        gain_at_trigger = (trigger_price - day_open) / day_open * 100
        if gain_at_trigger < 1.0 or gain_at_trigger > 15.0 or trigger_row["Close"] < trigger_row["Open"]:
            continue
            
        t_time_raw = str(trigger_row["Time"])
        t_time_fmt = f"{t_time_raw[:2]}:{t_time_raw[2:4]}"
        t_date_fmt = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        t_val_eok = round(trigger_row["Val"] / 1e8, 1)
        
        day_high = int(day_df["High"].max())
        day_close = int(day_df["Close"].iloc[-1])
        day_max_gain = round((day_high - day_open) / day_open * 100, 1)
        
        # 데이트레이딩 결과 판정
        after_trigger = day_df.iloc[trigger_idx + 1:]
        dt_result = "보합"
        if not after_trigger.empty:
            gains = (after_trigger["High"] - trigger_price) / trigger_price * 100
            drops = (trigger_price - after_trigger["Low"]) / trigger_price * 100
            
            t_hit = np.where(gains >= 3.25)[0]
            s_hit = np.where(drops >= 2.75)[0]
            t_first = t_hit[0] if len(t_hit) > 0 else 999999
            s_first = s_hit[0] if len(s_hit) > 0 else 999999
            
            if t_first < s_first:
                dt_result = "익절 (+3%)"
            elif s_first < t_first:
                dt_result = "손절 (-2.5%)"
            else:
                end_ret = (day_close - trigger_price) / trigger_price * 100
                dt_result = f"종가 ({end_ret:+.1f}%)"
                
        # 20선 눌림목 시뮬레이션
        pb_time_fmt = "-"
        pb_price = 0
        pb_mfe = 0.0
        pb_result = "-"
        
        for p_idx, p_row in after_trigger.iterrows():
            ma = p_row["MA20"]
            if pd.isna(ma) or ma <= 0: continue
            if p_row["Low"] <= ma * 1.005 and p_row["Close"] >= ma * 0.990:
                p_time_raw = str(p_row["Time"])
                pb_time_fmt = f"{p_time_raw[:2]}:{p_time_raw[2:4]}"
                pb_price = int(p_row["Close"])
                
                future_bars = day_df.iloc[p_idx + 1:]
                if not future_bars.empty:
                    post_high = future_bars["High"].max()
                    pb_mfe = round((post_high - pb_price) / pb_price * 100, 1)
                    
                    g_pb = (future_bars["High"] - pb_price) / pb_price * 100
                    d_pb = (pb_price - future_bars["Low"]) / pb_price * 100
                    t_pb = np.where(g_pb >= 3.25)[0]
                    s_pb = np.where(d_pb >= 2.75)[0]
                    t_f = t_pb[0] if len(t_pb) > 0 else 999999
                    s_f = s_pb[0] if len(s_pb) > 0 else 999999
                    
                    if t_f < s_f:
                        pb_result = "눌림 성공 (+3%)"
                    elif s_f < t_f:
                        pb_result = "눌림 손절 (-2.5%)"
                    else:
                        pb_result = f"눌림 종가 ({(day_close - pb_price)/pb_price*100:+.1f}%)"
                break
                
        # 오버나잇 결과
        cur_d_idx = date_to_idx.get(date, -1)
        next_open_gap = 0.0
        next_high_gain = 0.0
        on_result = "-"
        
        if cur_d_idx >= 0 and cur_d_idx + 1 < len(unique_dates):
            next_date = unique_dates[cur_d_idx + 1]
            next_day_df = day_dfs.get(next_date)
            if next_day_df is not None and not next_day_df.empty:
                next_open = next_day_df["Open"].iloc[0]
                next_high = next_day_df["High"].max()
                next_open_gap = round((next_open - day_close) / day_close * 100, 1)
                next_high_gain = round((next_high - day_close) / day_close * 100, 1)
                
                if next_high_gain >= 3.0:
                    on_result = f"성공 (고가 {next_high_gain:+.1f}%)"
                else:
                    on_result = f"미달 (고가 {next_high_gain:+.1f}%)"
                    
        events.append({
            "포착일자": t_date_fmt,
            "포착시간": t_time_fmt,
            "3분봉거래대금_억": t_val_eok,
            "포착가격_원": int(trigger_price),
            "포착등락률_%": round(gain_at_trigger, 1),
            "당일최고가_원": day_high,
            "당일최대상승률_%": day_max_gain,
            "당일매매결과": dt_result,
            "20선눌림시각": pb_time_fmt,
            "20선눌림가격_원": pb_price if pb_price > 0 else "-",
            "눌림후_최대상승률_%": pb_mfe if pb_price > 0 else "-",
            "눌림목결과": pb_result,
            "당일종가_원": day_close,
            "익일시가갭_%": next_open_gap,
            "익일최고가상승률_%": next_high_gain,
            "오버나잇결과": on_result
        })
        
    return events

def generate_hts_verification_workbook():
    print("=" * 80)
    print("[Multi-Agent Council] HTS 차트 검증용 종목별 시트 분리 엑셀 워크북 제작")
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
            targets.append((sym, name, mkt, p3, th, info["grade"], info["win_rate"]))
            
    # 승률 내림차순 정렬
    targets.sort(key=lambda x: x[6], reverse=True)
    print(f">> 총 {len(targets)}개 S/A급 종목 시트 생성 시작...")
    
    wb = openpyxl.Workbook()
    # 기본 시트를 요약 시트로 변경
    summary_ws = wb.active
    summary_ws.title = "00_주도주_요약목록"
    
    # 요약 시트 스타일 정의
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="맑은 고딕", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="맑은 고딕", size=10)
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    border_thin = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    # 1. 요약 시트 헤더 작성
    sum_headers = ["순번", "종목코드", "종목명", "소속시장", "3분봉 기준대금(억)", "주도주 등급", "돌파 승률(%)", "연간 포착일수", "시트 바로가기"]
    summary_ws.append(sum_headers)
    for col_idx in range(1, len(sum_headers) + 1):
        cell = summary_ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        
    summary_rows = []
    
    # 2. 각 종목별 시트 생성 및 데이터 채우기
    for idx, (sym, name, mkt, p3, th, grade, wr) in enumerate(targets, 1):
        sheet_name = sanitize_sheet_name(f"{idx:02d}_{name}")
        ws = wb.create_sheet(title=sheet_name)
        
        events = get_stock_events(sym, name, mkt, p3, th)
        
        # 타이틀 정보 행 추가
        ws.append([f"[{sym}] {name} (소속: {mkt}) - 3분봉 최적 기준 거래대금: {th:.0f}억 원 | 백테스트 돌파 승률: {wr:.1f}% | 총 포착일수: {len(events)}회"])
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=16)
        t_cell = ws.cell(row=1, column=1)
        t_cell.font = Font(name="맑은 고딕", size=12, bold=True, color="1F4E78")
        t_cell.alignment = Alignment(horizontal="left", vertical="center")
        
        # 종목 시트 헤더
        detail_headers = [
            "포착일자 (HTS 일봉)", "포착시간 (HTS 분봉)", "3분봉 대금(억)", "포착가격(원)", "포착등락률(%)",
            "당일최고가(원)", "당일최대상승(%)", "당일 매매결과",
            "20선 눌림시각", "20선 눌림가격(원)", "눌림후 최대상승(%)", "눌림목 결과",
            "당일 종가(원)", "익일 시가갭(%)", "익일 최고가(%)", "오버나잇 결과"
        ]
        ws.append(detail_headers)
        
        d_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
        for col_idx in range(1, len(detail_headers) + 1):
            cell = ws.cell(row=2, column=col_idx)
            cell.fill = d_fill
            cell.font = header_font
            cell.alignment = center_align
            
        for e in events:
            ws.append([
                e["포착일자"], e["포착시간"], e["3분봉거래대금_억"], e["포착가격_원"], e["포착등락률_%"],
                e["당일최고가_원"], e["당일최대상승률_%"], e["당일매매결과"],
                e["20선눌림시각"], e["20선눌림가격_원"], e["눌림후_최대상승률_%"], e["눌림목결과"],
                e["당일종가_원"], e["익일시가갭_%"], e["익일최고가상승률_%"], e["오버나잇결과"]
            ])
            
        # 서식 및 열 너비 자동 조정
        for r_idx in range(3, ws.max_row + 1):
            for c_idx in range(1, 17):
                c = ws.cell(row=r_idx, column=c_idx)
                c.font = data_font
                c.border = border_thin
                if c_idx in [1, 2, 8, 9, 12, 16]:
                    c.alignment = center_align
                else:
                    c.alignment = right_align
                    
                # 승리/성공 시 옅은 녹색 하이라이트
                val_str = str(c.value)
                if "성공" in val_str or "익절" in val_str:
                    c.fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
                elif "손절" in val_str:
                    c.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")

        # 열 너비 설정
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
            
        # 요약 행 데이터
        summary_rows.append([
            idx, sym, name, mkt, th, grade, wr, len(events), f"=HYPERLINK(\"#'{sheet_name}'!A1\", \"[시트 이동: {name}]\")"
        ])
        print(f"   • [{idx:02d}/38] {name} ({sym}): {len(events)}개 포착일 정리 완료 (시트명: {sheet_name})")

    # 요약 시트에 행 추가
    for s_row in summary_rows:
        summary_ws.append(s_row)
        
    for r_idx in range(2, summary_ws.max_row + 1):
        for c_idx in range(1, len(sum_headers) + 1):
            c = summary_ws.cell(row=r_idx, column=c_idx)
            c.font = data_font
            c.border = border_thin
            if c_idx in [1, 2, 4, 6, 9]:
                c.alignment = center_align
            elif c_idx == 3:
                c.alignment = Alignment(horizontal="left", vertical="center")
                c.font = Font(name="맑은 고딕", size=10, bold=True)
            else:
                c.alignment = right_align

    for col in summary_ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        summary_ws.column_dimensions[col_letter].width = max(max_len + 4, 14)
        
    # 저장
    out_file = os.path.join(LOCAL_DATA_DIR, "HTS검증용_SA급_주도주_일자별_포착내역.xlsx")
    wb.save(out_file)
    print(f"\n✅ [HTS 검증용 멀티시트 엑셀 생성 완료] {out_file}")
    
    # 구글 드라이브 동기화
    if os.path.exists(GDRIVE_DATA_DIR):
        try:
            shutil.copy2(out_file, os.path.join(GDRIVE_DATA_DIR, os.path.basename(out_file)))
            print(f"☁️ [Google Drive 동기화 완료] {GDRIVE_DATA_DIR}")
        except Exception as e:
            print(f"⚠️ [Google Drive 동기화 주의] {e}")

    return out_file

if __name__ == "__main__":
    generate_hts_verification_workbook()
