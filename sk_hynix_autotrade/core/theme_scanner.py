"""
========================================================================================
📊 [HTS THEME & LEADING STOCKS MONTHLY EXCEL ENGINE]
1달 단위 단일 엑셀 파일(HTS_테마_주도주_분석_YYYY-MM.xlsx) 내에 날짜별 시트를 생성하여:
1. [0659] 3대 주도 테마 (1등: 지역화폐, 2등: 정유, 3등: 전자결재) & 9대 대장주
2. [0198] 키움 실시간 조회수/검색 급등 20종목
3. [0184] 당일 거래대금 순수 KOSPI 20종목 (엄격한 코스피 개별주만)
4. [0184] 당일 거래대금 순수 KOSDAQ 20종목 (엄격한 코스닥 개별주만)
전체를 일목요연하게 매일 누적 업데이트하고 구글드라이브(G:\내 드라이브\Antigravity\테마)로 동기화합니다.
========================================================================================
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from core.gdrive_sync import GDriveSync
from core.hts_market_collector import HTSMarketCollector

class ThemeScanner:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.themes_dir = os.path.join(base_dir, "data", "themes")
        os.makedirs(self.themes_dir, exist_ok=True)
        self.gdrive_sync = GDriveSync()

    def scan_market_themes(self, api_instance=None) -> Dict[str, Any]:
        collector = HTSMarketCollector(api_instance)
        market_data = collector.collect_all()
        now = datetime.now()

        month_str = now.strftime('%Y-%m')
        date_str = now.strftime('%Y-%m-%d')
        monthly_excel_path = os.path.join(self.themes_dir, f"HTS_테마_주도주_분석_{month_str}.xlsx")

        if os.path.exists(monthly_excel_path):
            try:
                wb = openpyxl.load_workbook(monthly_excel_path)
            except Exception:
                wb = openpyxl.Workbook()
        else:
            wb = openpyxl.Workbook()

        if date_str in wb.sheetnames:
            del wb[date_str]

        ws = wb.create_sheet(title=date_str)
        ws.views.sheetView[0].showGridLines = True

        if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
            del wb["Sheet"]

        navy_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
        theme_hdr_fill = PatternFill(start_color="2B6CB0", end_color="2B6CB0", fill_type="solid")
        sub_hdr_fill = PatternFill(start_color="EDF2F7", end_color="EDF2F7", fill_type="solid")
        amber_hdr_fill = PatternFill(start_color="78350F", end_color="78350F", fill_type="solid")
        emerald_hdr_fill = PatternFill(start_color="064E3B", end_color="064E3B", fill_type="solid")
        blue_hdr_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")

        title_font = Font(name="맑은 고딕", size=15, bold=True, color="FFFFFF")
        section_font = Font(name="맑은 고딕", size=11, bold=True, color="FFFFFF")
        hdr_font = Font(name="맑은 고딕", size=9, bold=True, color="2D3748")
        bold_font = Font(name="맑은 고딕", size=9, bold=True)
        regular_font = Font(name="맑은 고딕", size=9)
        red_font = Font(name="맑은 고딕", size=9, bold=True, color="C53030")
        blue_font = Font(name="맑은 고딕", size=9, bold=True, color="2B6CB0")

        thin_border = Border(
            left=Side(style='thin', color='CBD5E0'),
            right=Side(style='thin', color='CBD5E0'),
            top=Side(style='thin', color='CBD5E0'),
            bottom=Side(style='thin', color='CBD5E0')
        )

        ws.merge_cells("A1:H2")
        title_cell = ws["A1"]
        title_cell.value = f"📊 [{date_str}] 키움증권 HTS 4대 시장 데이터 (0659 테마 / 0198 급등 / 0184 코스피·코스닥 거래대금 20)"
        title_cell.font = title_font
        title_cell.fill = navy_fill
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        current_row = 4

        # SECTION 1: 0659 테마
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        s1_cell = ws.cell(row=current_row, column=1)
        s1_cell.value = "  🏆 SECTION 1. [0659] 당일 3대 주도 테마 & 9대 대장주 (1등: 지역화폐 / 2등: 정유 / 3등: 전자결재)"
        s1_cell.font = section_font
        s1_cell.fill = theme_hdr_fill
        s1_cell.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[current_row].height = 26
        current_row += 1

        for t in market_data["themes_0659"]:
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
            t_sub = ws.cell(row=current_row, column=1)
            t_sub.value = f"  [{t['rank']}위 테마] {t['theme_name']}  |  평균 등락: +{t['avg_rate']:.2f}%  |  테마 총 거래대금: {t['total_trade_value']:,.0f}억원  |  주도사유: {t['description']}"
            t_sub.font = Font(name="맑은 고딕", size=9, bold=True, color="1A365D")
            t_sub.fill = sub_hdr_fill
            t_sub.alignment = Alignment(horizontal="left", vertical="center")
            ws.row_dimensions[current_row].height = 22
            current_row += 1

            headers = ["대장순위", "종목코드", "종목명", "시장구분", "현재가(원)", "등락률(%)", "거래대금(억원)", "AI 주도주 판정 코멘트"]
            for col_idx, h in enumerate(headers, 1):
                c = ws.cell(row=current_row, column=col_idx, value=h)
                c.font = hdr_font
                c.fill = sub_hdr_fill
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.border = thin_border
            ws.row_dimensions[current_row].height = 20
            current_row += 1

            for s in t["top3_stocks"]:
                row_vals = [
                    f"{s['rank']}등 대장",
                    s["code"],
                    s["name"],
                    s["market"],
                    s["price"],
                    s["rate"] / 100.0,
                    s["trade_value_eok"],
                    s["reason"]
                ]
                for col_idx, val in enumerate(row_vals, 1):
                    c = ws.cell(row=current_row, column=col_idx, value=val)
                    c.font = regular_font
                    c.border = thin_border
                    if col_idx in [1, 2, 4]:
                        c.alignment = Alignment(horizontal="center", vertical="center")
                    elif col_idx == 3:
                        c.alignment = Alignment(horizontal="left", vertical="center")
                        c.font = bold_font
                    elif col_idx == 5:
                        c.alignment = Alignment(horizontal="right", vertical="center")
                        c.number_format = '#,##0'
                    elif col_idx == 6:
                        c.alignment = Alignment(horizontal="right", vertical="center")
                        c.number_format = '+0.00%;-0.00%;0.00%'
                        c.font = red_font if s["rate"] > 0 else blue_font
                    elif col_idx == 7:
                        c.alignment = Alignment(horizontal="right", vertical="center")
                        c.number_format = '#,##0.0'
                    elif col_idx == 8:
                        c.alignment = Alignment(horizontal="left", vertical="center")
                ws.row_dimensions[current_row].height = 19
                current_row += 1

        current_row += 1

        # SECTION 2: 0198 조회수 급등 20
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        s2_cell = ws.cell(row=current_row, column=1)
        s2_cell.value = "  ⚡ SECTION 2. [0198] 키움증권 실시간 조회수 / 검색 급등 TOP 20 종목"
        s2_cell.font = section_font
        s2_cell.fill = amber_hdr_fill
        s2_cell.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[current_row].height = 26
        current_row += 1

        headers_0198 = ["순위", "종목코드", "종목명", "시장구분", "현재가(원)", "등락률(%)", "거래대금(억원)", "검색급등률 & 사유"]
        for col_idx, h in enumerate(headers_0198, 1):
            c = ws.cell(row=current_row, column=col_idx, value=h)
            c.font = hdr_font
            c.fill = sub_hdr_fill
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = thin_border
        ws.row_dimensions[current_row].height = 20
        current_row += 1

        for s in market_data["momentum_0198"]:
            row_vals = [
                s["rank"],
                s["code"],
                s["name"],
                s["market"],
                s["price"],
                s["rate"] / 100.0,
                s["trade_value_eok"],
                f"[{s['search_surge_rate']} 급등] {s['reason']}"
            ]
            for col_idx, val in enumerate(row_vals, 1):
                c = ws.cell(row=current_row, column=col_idx, value=val)
                c.font = regular_font
                c.border = thin_border
                if col_idx in [1, 2, 4]:
                    c.alignment = Alignment(horizontal="center", vertical="center")
                elif col_idx == 3:
                    c.alignment = Alignment(horizontal="left", vertical="center")
                    c.font = bold_font
                elif col_idx == 5:
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    c.number_format = '#,##0'
                elif col_idx == 6:
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    c.number_format = '+0.00%;-0.00%;0.00%'
                    c.font = red_font if s["rate"] > 0 else blue_font
                elif col_idx == 7:
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    c.number_format = '#,##0.0'
                elif col_idx == 8:
                    c.alignment = Alignment(horizontal="left", vertical="center")
            ws.row_dimensions[current_row].height = 19
            current_row += 1

        current_row += 1

        # SECTION 3: 0184 KOSPI 순수 20
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=7)
        s3_cell = ws.cell(row=current_row, column=1)
        s3_cell.value = "  🟢 SECTION 3. [0184] 당일 거래대금 상위 순수 KOSPI 20종목 (ETF, ETN, 우선주 제외)"
        s3_cell.font = section_font
        s3_cell.fill = emerald_hdr_fill
        s3_cell.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[current_row].height = 26
        current_row += 1

        headers_kospi = ["순위", "종목코드", "종목명", "시장", "현재가(원)", "등락률(%)", "당일 거래대금(억원)"]
        for col_idx, h in enumerate(headers_kospi, 1):
            c = ws.cell(row=current_row, column=col_idx, value=h)
            c.font = hdr_font
            c.fill = sub_hdr_fill
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = thin_border
        ws.row_dimensions[current_row].height = 20
        current_row += 1

        for s in market_data["kospi_0184"]:
            row_vals = [
                s["rank"],
                s["code"],
                s["name"],
                s["market"],
                s["price"],
                s["rate"] / 100.0,
                s["trade_value_eok"]
            ]
            for col_idx, val in enumerate(row_vals, 1):
                c = ws.cell(row=current_row, column=col_idx, value=val)
                c.font = regular_font
                c.border = thin_border
                if col_idx in [1, 2, 4]:
                    c.alignment = Alignment(horizontal="center", vertical="center")
                elif col_idx == 3:
                    c.alignment = Alignment(horizontal="left", vertical="center")
                    c.font = bold_font
                elif col_idx == 5:
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    c.number_format = '#,##0'
                elif col_idx == 6:
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    c.number_format = '+0.00%;-0.00%;0.00%'
                    c.font = red_font if s["rate"] > 0 else blue_font
                elif col_idx == 7:
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    c.number_format = '#,##0.0'
            ws.row_dimensions[current_row].height = 19
            current_row += 1

        current_row += 1

        # SECTION 4: 0184 KOSDAQ 순수 20
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=7)
        s4_cell = ws.cell(row=current_row, column=1)
        s4_cell.value = "  🔵 SECTION 4. [0184] 당일 거래대금 상위 순수 KOSDAQ 20종목 (ETF, 스팩 제외)"
        s4_cell.font = section_font
        s4_cell.fill = blue_hdr_fill
        s4_cell.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[current_row].height = 26
        current_row += 1

        headers_kosdaq = ["순위", "종목코드", "종목명", "시장", "현재가(원)", "등락률(%)", "당일 거래대금(억원)"]
        for col_idx, h in enumerate(headers_kosdaq, 1):
            c = ws.cell(row=current_row, column=col_idx, value=h)
            c.font = hdr_font
            c.fill = sub_hdr_fill
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = thin_border
        ws.row_dimensions[current_row].height = 20
        current_row += 1

        for s in market_data["kosdaq_0184"]:
            row_vals = [
                s["rank"],
                s["code"],
                s["name"],
                s["market"],
                s["price"],
                s["rate"] / 100.0,
                s["trade_value_eok"]
            ]
            for col_idx, val in enumerate(row_vals, 1):
                c = ws.cell(row=current_row, column=col_idx, value=val)
                c.font = regular_font
                c.border = thin_border
                if col_idx in [1, 2, 4]:
                    c.alignment = Alignment(horizontal="center", vertical="center")
                elif col_idx == 3:
                    c.alignment = Alignment(horizontal="left", vertical="center")
                    c.font = bold_font
                elif col_idx == 5:
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    c.number_format = '#,##0'
                elif col_idx == 6:
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    c.number_format = '+0.00%;-0.00%;0.00%'
                    c.font = red_font if s["rate"] > 0 else blue_font
                elif col_idx == 7:
                    c.alignment = Alignment(horizontal="right", vertical="center")
                    c.number_format = '#,##0.0'
            ws.row_dimensions[current_row].height = 19
            current_row += 1

        col_widths = [12, 12, 22, 12, 14, 14, 18, 40]
        for idx, width in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(idx)].width = width

        wb.save(monthly_excel_path)
        print(f">> [ThemeScanner] ✅ 1달 단위 통합 엑셀 파일 저장 완료: {os.path.abspath(monthly_excel_path)} (시트: {date_str})")

        self._sync_to_google_drive(monthly_excel_path)
        return market_data

    def _sync_to_google_drive(self, excel_path: str):
        target_gdrive = self.gdrive_sync.target_dir
        if not target_gdrive:
            return
        theme_gdrive_dir = os.path.join(target_gdrive, "테마")
        os.makedirs(theme_gdrive_dir, exist_ok=True)
        try:
            self.gdrive_sync.sync_file(excel_path, "테마")
            print(f">> [ThemeScanner] ☁️ 구글 드라이브 [테마] 폴더 월간 엑셀 동기화 완료: {theme_gdrive_dir}")
        except Exception as e:
            print(f">> [ThemeScanner] 구글 드라이브 동기화 오류: {e}")

if __name__ == "__main__":
    scanner = ThemeScanner()
    scanner.scan_market_themes()
