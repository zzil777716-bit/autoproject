# -*- coding: utf-8 -*-
"""
========================================================================================
🏛️ [COLLECTOR: INFOSTOCK THEME MAP COLLECTOR]
- 인포스탁/네이버 무료 제공 266개 전체 테마 및 전 종목 테마 지도 매일 자동 구축
- 산출물:
  1) D:\ANTIGRAVITY(자동매매)\data\themes\infostock_theme_map_latest.json
  2) D:\ANTIGRAVITY(자동매매)\data\themes\infostock_stock_to_themes.json (종목코드 -> 소속 테마 목록 역색인)
  3) G:\내 드라이브\Antigravity\테마\전종목_인포스탁_테마지도_YYYY-MM-DD.xlsx
  4) G:\내 드라이브\Antigravity\테마\전종목_인포스탁_테마지도_최신.xlsx
========================================================================================
"""

import os
import sys
import json
import time
import shutil
from datetime import datetime
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = r"D:\ANTIGRAVITY(자동매매)"
LOCAL_THEME_DIR = os.path.join(BASE_DIR, "data", "themes")
GDRIVE_THEME_DIR = r"G:\내 드라이브\Antigravity\테마"

os.makedirs(LOCAL_THEME_DIR, exist_ok=True)
try:
    os.makedirs(GDRIVE_THEME_DIR, exist_ok=True)
except Exception:
    pass

def safe_float(val, default=0.0):
    try:
        s = str(val).replace('%', '').replace(',', '').strip()
        if not s or s == '-':
            return default
        return float(s)
    except Exception:
        return default

def safe_int(val, default=0):
    try:
        s = str(val).replace(',', '').strip()
        if not s or s == '-':
            return default
        return int(float(s))
    except Exception:
        return default

class InfostockThemeMapCollector:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    def fetch_all_themes_list(self):
        """266개 전체 테마 목록 조회"""
        themes = []
        for page in range(1, 10):
            url = f"https://m.stock.naver.com/api/stocks/theme?page={page}&pageSize=50"
            req = urllib.request.Request(url, headers=self.headers)
            try:
                with urllib.request.urlopen(req, timeout=8) as res:
                    data = json.loads(res.read().decode('utf-8'))
                    groups = data.get('groups', [])
                    if not groups:
                        break
                    themes.extend(groups)
            except Exception:
                break
        return themes

    def fetch_theme_detail(self, theme_item):
        """개별 테마의 상세 설명 및 소속 종목 리스트 조회"""
        theme_no = theme_item['no']
        theme_name = theme_item.get('name', '')
        change_rate = safe_float(theme_item.get('changeRate', 0.0))
        
        url = f"https://m.stock.naver.com/api/stocks/theme/{theme_no}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=8) as res:
                data = json.loads(res.read().decode('utf-8'))
                desc = data.get('themeDescription', '')
                stocks = data.get('stocks', [])
                return {
                    'theme_no': theme_no,
                    'theme_name': theme_name,
                    'change_rate': change_rate,
                    'description': desc,
                    'stocks': stocks
                }
        except Exception:
            return {
                'theme_no': theme_no,
                'theme_name': theme_name,
                'change_rate': change_rate,
                'description': '',
                'stocks': []
            }

    def collect_and_build_map(self):
        t0 = time.time()
        today_str = datetime.now().strftime("%Y-%m-%d")
        print("=" * 85)
        print(f"🏛️ [Antigravity] 인포스탁 전종목 테마지도 무료 취합 및 자동 생성 시작 ({today_str})")
        print("=" * 85)

        theme_list = self.fetch_all_themes_list()
        print(f">> [1/3] 전체 테마 목록 취합 완료: 총 {len(theme_list)}개 테마 발견")

        print(f">> [2/3] 266개 테마 상세 소속 종목 동시 수집 중 (ThreadPool 15)...")
        with ThreadPoolExecutor(max_workers=15) as executor:
            theme_details = list(executor.map(self.fetch_theme_detail, theme_list))

        theme_rows = []
        stock_to_themes = {}

        for td in theme_details:
            t_no = td['theme_no']
            t_name = td['theme_name']
            t_rate = td['change_rate']
            t_desc = td['description']
            stocks = td['stocks']

            for s in stocks:
                code = s.get('itemCode', '')
                name = s.get('stockName', '')
                close_p = s.get('closePrice', '')
                fluc = s.get('fluctuationsRatio', '0.0')
                market = s.get('stockExchangeType', {}).get('nameKor', '')
                trade_val = s.get('accumulatedTradingValue', '0')

                theme_rows.append({
                    '테마코드': t_no,
                    '테마명': t_name,
                    '테마등락률_%': t_rate,
                    '종목코드': code,
                    '종목명': name,
                    '시장': market,
                    '현재가': close_p,
                    '등락률_%': safe_float(fluc),
                    '거래대금(백만)': safe_int(trade_val),
                    '테마설명': t_desc
                })

                if code not in stock_to_themes:
                    stock_to_themes[code] = {
                        'code': code,
                        'name': name,
                        'market': market,
                        'themes': []
                    }
                stock_to_themes[code]['themes'].append({
                    'theme_no': t_no,
                    'theme_name': t_name,
                    'theme_rate': t_rate
                })

        df_theme_map = pd.DataFrame(theme_rows)
        print(f">> [3/3] 테마-종목 매핑 완료: 총 {len(theme_rows)}개 테마-종목 연결선, 고유 종목수: {len(stock_to_themes)}개")

        local_json_theme = os.path.join(LOCAL_THEME_DIR, "infostock_theme_map_latest.json")
        local_json_stock = os.path.join(LOCAL_THEME_DIR, "infostock_stock_to_themes.json")
        with open(local_json_theme, "w", encoding="utf-8") as f:
            json.dump(theme_details, f, indent=2, ensure_ascii=False)
        with open(local_json_stock, "w", encoding="utf-8") as f:
            json.dump(stock_to_themes, f, indent=2, ensure_ascii=False)

        excel_name_date = f"전종목_인포스탁_테마지도_{today_str}.xlsx"
        excel_name_latest = "전종목_인포스탁_테마지도_최신.xlsx"
        
        stock_summary_rows = []
        for code, info in stock_to_themes.items():
            t_names = [t['theme_name'] for t in info['themes']]
            stock_summary_rows.append({
                '종목코드': code,
                '종목명': info['name'],
                '시장': info['market'],
                '소속테마수': len(t_names),
                '소속테마목록': ", ".join(t_names)
            })
        df_stock_summary = pd.DataFrame(stock_summary_rows).sort_values(by="소속테마수", ascending=False)

        target_dirs = [LOCAL_THEME_DIR]
        if os.path.exists(r"G:\내 드라이브\Antigravity"):
            target_dirs.append(GDRIVE_THEME_DIR)

        for d in target_dirs:
            p_date = os.path.join(d, excel_name_date)
            p_latest = os.path.join(d, excel_name_latest)
            try:
                with pd.ExcelWriter(p_date, engine='openpyxl') as writer:
                    df_stock_summary.to_excel(writer, sheet_name="종목별_소속테마_요약", index=False)
                    df_theme_map.to_excel(writer, sheet_name="테마별_소속종목_상세", index=False)
                shutil.copyfile(p_date, p_latest)
                print(f"   • 엑셀 테마지도 배포 성공: {p_date}")
            except Exception as e:
                print(f"   • 엑셀 저장 중 예외 ({d}): {e}")

        elapsed = time.time() - t0
        print("=" * 85)
        print(f"🎉 [성공] 인포스탁 전종목 테마지도 구축 완료! (소요 시간: {elapsed:.1f}초)")
        print(f"   • 총 테마 수: {len(theme_details)}개 | 연동 종목 수: {len(stock_to_themes)}개")
        print(f"   • 로컬 저장: {LOCAL_THEME_DIR}")
        print(f"   • 구글 드라이브: {GDRIVE_THEME_DIR}")
        print("=" * 85)
        return df_theme_map

if __name__ == "__main__":
    collector = InfostockThemeMapCollector()
    collector.collect_and_build_map()
