"""
========================================================================================
📅 [DESKTOP THEME CALENDAR GENERATOR] (v2.0)
Builds an Interactive Desktop Calendar HTML on the Desktop:
- In each date box: 1,2,3등 테마명 & 1등 테마의 1등 종목 1개 표기
  (1등: 지역화폐 (코나아이) / 2등: 정유 / 3등: 전자결재)
- Click date -> Full HTS 0659 / 0198 / 0184 (KOSPI 20 + KOSDAQ 20 Pure Stocks) Modal!
- Also updates the Monthly Excel Sheet (HTS_테마_주도주_분석_YYYY-MM.xlsx) in Google Drive!
========================================================================================
"""

import sys
import os
import json
import calendar
from datetime import datetime, date
from typing import Dict, Any, List

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.gdrive_sync import GDriveSync
from core.hts_market_collector import HTSMarketCollector
from core.theme_scanner import ThemeScanner

class DesktopCalendarGenerator:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.calendar_dir = os.path.join(base_dir, "data", "calendar")
        os.makedirs(self.calendar_dir, exist_ok=True)
        self.history_file = os.path.join(self.calendar_dir, "market_calendar_history.json")
        self.desktop_html_path = r"C:\Users\HONG\Desktop\증시_주도테마_캘린더.html"
        self.gdrive_sync = GDriveSync()

    def update_and_build(self, api_instance=None) -> str:
        theme_scanner = ThemeScanner(self.base_dir)
        daily_data = theme_scanner.scan_market_themes(api_instance)
        today_str = daily_data["date"]

        history = self._load_history()
        history[today_str] = daily_data
        self._save_history(history)

        now = datetime.now()
        html_content = self._render_calendar_html(history, now.year, now.month)

        with open(self.desktop_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f">> [CalendarGenerator] 📅 바탕화면 캘린더 생성 완료: {self.desktop_html_path}")

        self._sync_to_google_drive(self.desktop_html_path, self.history_file)
        return self.desktop_html_path

    def _load_history(self) -> Dict[str, Any]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_history(self, history: Dict[str, Any]):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def _render_calendar_html(self, history: Dict[str, Any], year: int, month: int) -> str:
        history_json_str = json.dumps(history, ensure_ascii=False)
        
        html = f"""<!DOCTYPE html>
<html lang="ko" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>증시 주도 테마 & HTS 4종 주도주 캘린더</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&display=swap');
    body {{
      font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .custom-scrollbar::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    .custom-scrollbar::-webkit-scrollbar-track {{
      background: rgba(30, 41, 59, 0.5);
    }}
    .custom-scrollbar::-webkit-scrollbar-thumb {{
      background: rgba(100, 116, 139, 0.5);
      border-radius: 3px;
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-4 md:p-8 antialiased selection:bg-blue-600 selection:text-white">

  <div class="max-w-7xl mx-auto mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl backdrop-blur">
    <div>
      <div class="flex items-center gap-3 mb-1">
        <span class="inline-flex items-center justify-center p-2 bg-blue-600/20 text-blue-400 rounded-xl border border-blue-500/30">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
        </span>
        <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400">
          대한민국 증시 주도 테마 & HTS 4종 캘린더
        </h1>
      </div>
      <p class="text-slate-400 text-sm">
        키움증권 HTS <span class="text-blue-400 font-semibold">[0659 테마 3x3]</span> · <span class="text-amber-400 font-semibold">[0198 조회수 급등 20]</span> · <span class="text-emerald-400 font-semibold">[0184 코스피 20]</span> · <span class="text-cyan-400 font-semibold">[0184 코스닥 20]</span>
      </p>
    </div>

    <div class="flex items-center gap-3 bg-slate-800/80 p-2 rounded-xl border border-slate-700">
      <button onclick="changeMonth(-1)" class="p-2 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg transition">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>
      </button>
      <span id="currentMonthYear" class="text-lg font-bold px-3 text-slate-100 min-w-[130px] text-center"></span>
      <button onclick="changeMonth(1)" class="p-2 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg transition">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
      </button>
      <button onclick="goToToday()" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow-sm transition">오늘</button>
    </div>
  </div>

  <div class="max-w-7xl mx-auto grid grid-cols-7 gap-2 mb-2 text-center font-bold text-sm">
    <div class="p-2 text-red-400 bg-red-950/30 rounded-lg border border-red-900/30">일 (SUN)</div>
    <div class="p-2 text-slate-300 bg-slate-900/50 rounded-lg border border-slate-800">월 (MON)</div>
    <div class="p-2 text-slate-300 bg-slate-900/50 rounded-lg border border-slate-800">화 (TUE)</div>
    <div class="p-2 text-slate-300 bg-slate-900/50 rounded-lg border border-slate-800">수 (WED)</div>
    <div class="p-2 text-slate-300 bg-slate-900/50 rounded-lg border border-slate-800">목 (THU)</div>
    <div class="p-2 text-slate-300 bg-slate-900/50 rounded-lg border border-slate-800">금 (FRI)</div>
    <div class="p-2 text-blue-400 bg-blue-950/30 rounded-lg border border-blue-900/30">토 (SAT)</div>
  </div>

  <div id="calendarGrid" class="max-w-7xl mx-auto grid grid-cols-7 gap-2 mb-8"></div>

  <div id="detailModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
    <div class="bg-slate-900 border border-slate-700 w-full max-w-5xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
      
      <div class="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
        <div class="flex items-center gap-3">
          <span class="p-2 bg-indigo-500/20 text-indigo-400 rounded-lg border border-indigo-500/30">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
          </span>
          <div>
            <h2 id="modalDateTitle" class="text-xl font-bold text-white"></h2>
            <p class="text-xs text-slate-400">키움증권 HTS [0659/0198/0184] 상세 데이터 리포트</p>
          </div>
        </div>
        <button onclick="closeModal()" class="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>

      <div class="flex border-b border-slate-800 bg-slate-900/80 px-5 gap-2 pt-2">
        <button onclick="switchTab('tab_0659')" id="btn_tab_0659" class="px-4 py-2.5 text-sm font-semibold border-b-2 border-blue-500 text-blue-400 transition">
          [0659] 3대 주도 테마 & 9대 대장주
        </button>
        <button onclick="switchTab('tab_0198')" id="btn_tab_0198" class="px-4 py-2.5 text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition">
          [0198] 실시간 조회수 급등 20종목
        </button>
        <button onclick="switchTab('tab_kospi')" id="btn_tab_kospi" class="px-4 py-2.5 text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition">
          [0184] KOSPI 순수 거래대금 TOP 20
        </button>
        <button onclick="switchTab('tab_kosdaq')" id="btn_tab_kosdaq" class="px-4 py-2.5 text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition">
          [0184] KOSDAQ 순수 거래대금 TOP 20
        </button>
      </div>

      <div class="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6">
        <div id="content_tab_0659" class="space-y-6">
          <div id="themeCardsContainer" class="space-y-4"></div>
        </div>

        <div id="content_tab_0198" class="hidden">
          <div class="overflow-x-auto rounded-xl border border-slate-800">
            <table class="w-full text-left text-sm text-slate-300">
              <thead class="bg-slate-950 text-slate-400 font-bold uppercase text-xs">
                <tr>
                  <th class="p-3 text-center">순위</th>
                  <th class="p-3">종목명 (코드)</th>
                  <th class="p-3 text-center">시장</th>
                  <th class="p-3 text-right">현재가</th>
                  <th class="p-3 text-right">등락률</th>
                  <th class="p-3 text-right">거래대금</th>
                  <th class="p-3 text-center">검색급등률</th>
                  <th class="p-3">주도 및 급등 사유</th>
                </tr>
              </thead>
              <tbody id="table_0198_body" class="divide-y divide-slate-800/60"></tbody>
            </table>
          </div>
        </div>

        <div id="content_tab_kospi" class="hidden">
          <div class="mb-3 text-xs text-slate-400 flex items-center gap-1.5">
            <span class="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
            엄격한 KOSPI 순수 기업 개별주만 선별 (ETF, ETN, 우선주 제외)
          </div>
          <div class="overflow-x-auto rounded-xl border border-slate-800">
            <table class="w-full text-left text-sm text-slate-300">
              <thead class="bg-slate-950 text-slate-400 font-bold uppercase text-xs">
                <tr>
                  <th class="p-3 text-center">순위</th>
                  <th class="p-3">종목명 (코드)</th>
                  <th class="p-3 text-center">시장</th>
                  <th class="p-3 text-right">현재가</th>
                  <th class="p-3 text-right">등락률</th>
                  <th class="p-3 text-right">당일 거래대금(억원)</th>
                </tr>
              </thead>
              <tbody id="table_kospi_body" class="divide-y divide-slate-800/60"></tbody>
            </table>
          </div>
        </div>

        <div id="content_tab_kosdaq" class="hidden">
          <div class="mb-3 text-xs text-slate-400 flex items-center gap-1.5">
            <span class="inline-block w-2 h-2 rounded-full bg-blue-500"></span>
            엄격한 KOSDAQ 순수 기업 개별주만 선별 (ETF, 스팩 제외)
          </div>
          <div class="overflow-x-auto rounded-xl border border-slate-800">
            <table class="w-full text-left text-sm text-slate-300">
              <thead class="bg-slate-950 text-slate-400 font-bold uppercase text-xs">
                <tr>
                  <th class="p-3 text-center">순위</th>
                  <th class="p-3">종목명 (코드)</th>
                  <th class="p-3 text-center">시장</th>
                  <th class="p-3 text-right">현재가</th>
                  <th class="p-3 text-right">등락률</th>
                  <th class="p-3 text-right">당일 거래대금(억원)</th>
                </tr>
              </thead>
              <tbody id="table_kosdaq_body" class="divide-y divide-slate-800/60"></tbody>
            </table>
          </div>
        </div>

      </div>

    </div>
  </div>

  <script>
    const marketHistory = {history_json_str};
    let currentYear = {year};
    let currentMonth = {month};

    function renderCalendar() {{
      const grid = document.getElementById("calendarGrid");
      grid.innerHTML = "";

      document.getElementById("currentMonthYear").innerText = `${{currentYear}}년 ${{currentMonth}}월`;

      const firstDayIndex = new Date(currentYear, currentMonth - 1, 1).getDay();
      const lastDate = new Date(currentYear, currentMonth, 0).getDate();
      const prevMonthLastDate = new Date(currentYear, currentMonth - 1, 0).getDate();

      for (let i = firstDayIndex - 1; i >= 0; i--) {{
        const day = prevMonthLastDate - i;
        const cell = document.createElement("div");
        cell.className = "min-h-[140px] p-2.5 bg-slate-950/40 border border-slate-900 rounded-xl opacity-30";
        cell.innerHTML = `<span class="text-xs font-semibold text-slate-600">${{day}}</span>`;
        grid.appendChild(cell);
      }}

      for (let day = 1; day <= lastDate; day++) {{
        const dateStr = `${{currentYear}}-${{String(currentMonth).padStart(2, '0')}}-${{String(day).padStart(2, '0')}}`;
        const dayData = marketHistory[dateStr];
        const dayOfWeek = new Date(currentYear, currentMonth - 1, day).getDay();

        const isToday = (dateStr === new Date().toISOString().slice(0, 10));
        const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);

        const cell = document.createElement("div");
        let borderClass = isToday ? "border-blue-500 shadow-lg shadow-blue-500/10 ring-1 ring-blue-500" : "border-slate-800 hover:border-slate-700";
        let bgClass = isToday ? "bg-slate-900/90" : "bg-slate-900/50 hover:bg-slate-900/80";

        cell.className = `min-h-[145px] p-2.5 rounded-xl border ${{borderClass}} ${{bgClass}} transition cursor-pointer flex flex-col justify-between group`;
        cell.onclick = () => openModal(dateStr);

        let headerColor = dayOfWeek === 0 ? "text-red-400" : (dayOfWeek === 6 ? "text-blue-400" : "text-slate-300");
        let todayBadge = isToday ? `<span class="ml-1.5 px-1.5 py-0.5 bg-blue-600 text-[10px] font-bold text-white rounded">오늘</span>` : "";

        let themesHtml = "";
        if (dayData && dayData.themes_0659 && dayData.themes_0659.length >= 3) {{
          const t1 = dayData.themes_0659[0];
          const t2 = dayData.themes_0659[1];
          const t3 = dayData.themes_0659[2];
          const topStock = (t1.top3_stocks && t1.top3_stocks.length > 0) ? t1.top3_stocks[0].name : "";

          themesHtml = `
            <div class="mt-1 space-y-1 text-xs">
              <div class="p-1 rounded bg-amber-500/15 border border-amber-500/30 text-amber-300 font-semibold truncate" title="1등: ${{t1.theme_name}} (${{topStock}})">
                🥇 <span class="font-bold">${{t1.theme_name.split('(')[0].trim()}}</span> <span class="text-amber-200 font-normal">(${{topStock}})</span>
              </div>
              <div class="p-1 rounded bg-slate-800/80 border border-slate-700 text-slate-300 truncate" title="2등: ${{t2.theme_name}}">
                🥈 ${{t2.theme_name.split('(')[0].trim()}}
              </div>
              <div class="p-1 rounded bg-slate-800/60 border border-slate-700/60 text-slate-400 truncate" title="3등: ${{t3.theme_name}}">
                🥉 ${{t3.theme_name.split('(')[0].trim()}}
              </div>
            </div>
          `;
        }} else {{
          themesHtml = `
            <div class="flex-1 flex items-center justify-center text-[11px] text-slate-600 italic">
              ${{isWeekend ? "휴장일" : "데이터 수집 대기"}}
            </div>
          `;
        }}

        cell.innerHTML = `
          <div>
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm font-bold ${{headerColor}}">${{day}}</span>
              ${{todayBadge}}
            </div>
            ${{themesHtml}}
          </div>
          <div class="text-[10px] text-right text-slate-500 opacity-0 group-hover:opacity-100 transition">
            클릭하여 HTS 상세보기 →
          </div>
        `;
        grid.appendChild(cell);
      }}
    }}

    function changeMonth(delta) {{
      currentMonth += delta;
      if (currentMonth > 12) {{
        currentMonth = 1;
        currentYear++;
      }} else if (currentMonth < 1) {{
        currentMonth = 12;
        currentYear--;
      }}
      renderCalendar();
    }}

    function goToToday() {{
      const d = new Date();
      currentYear = d.getFullYear();
      currentMonth = d.getMonth() + 1;
      renderCalendar();
    }}

    function openModal(dateStr) {{
      const data = marketHistory[dateStr];
      const modal = document.getElementById("detailModal");
      document.getElementById("modalDateTitle").innerText = `📅 [${{dateStr}}] 키움증권 HTS 4종 주도 시장 데이터 리포트`;

      if (!data) {{
        alert(`${{dateStr}} 일자의 HTS 수집 데이터가 아직 없습니다.`);
        return;
      }}

      const container = document.getElementById("themeCardsContainer");
      container.innerHTML = "";
      if (data.themes_0659) {{
        data.themes_0659.forEach((t, idx) => {{
          const medal = idx === 0 ? "🥇 1위 테마" : (idx === 1 ? "🥈 2위 테마" : "🥉 3위 테마");
          const card = document.createElement("div");
          card.className = "bg-slate-950/80 border border-slate-800 rounded-xl p-4";

          let stocksTable = `
            <table class="w-full text-sm text-left mt-3">
              <thead class="text-xs text-slate-400 bg-slate-900 border-b border-slate-800">
                <tr>
                  <th class="p-2 text-center">대장순위</th>
                  <th class="p-2">종목명 (코드)</th>
                  <th class="p-2 text-center">시장</th>
                  <th class="p-2 text-right">현재가</th>
                  <th class="p-2 text-right">등락률</th>
                  <th class="p-2 text-right">거래대금</th>
                  <th class="p-2">주도 사유</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800/50">
          `;

          t.top3_stocks.forEach((s, sIdx) => {{
            stocksTable += `
              <tr>
                <td class="p-2 text-center font-bold text-amber-400">${{sIdx + 1}}등 대장</td>
                <td class="p-2 font-semibold text-slate-200">${{s.name}} <span class="text-xs text-slate-500 font-normal">(${{s.code}})</span></td>
                <td class="p-2 text-center"><span class="px-1.5 py-0.5 text-[10px] font-bold rounded ${{s.market === 'KOSPI' ? 'bg-emerald-900/60 text-emerald-300' : 'bg-blue-900/60 text-blue-300'}}">${{s.market}}</span></td>
                <td class="p-2 text-right">${{s.price.toLocaleString()}}원</td>
                <td class="p-2 text-right font-bold ${{s.rate > 0 ? 'text-red-400' : 'text-blue-400'}}">${{s.rate > 0 ? '+' : ''}}${{s.rate.toFixed(2)}}%</td>
                <td class="p-2 text-right">${{s.trade_value_eok.toLocaleString()}}억원</td>
                <td class="p-2 text-xs text-slate-400">${{s.reason}}</td>
              </tr>
            `;
          }});

          stocksTable += `</tbody></table>`;

          card.innerHTML = `
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5">
              <div>
                <span class="px-2 py-0.5 rounded text-xs font-bold bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">${{medal}}</span>
                <h3 class="text-lg font-bold text-white mt-1">${{t.theme_name}}</h3>
                <p class="text-xs text-slate-400 italic">${{t.description}}</p>
              </div>
              <div class="text-right text-xs">
                <div class="text-slate-400">평균 등락: <span class="font-bold text-red-400">+${{t.avg_rate.toFixed(2)}}%</span></div>
                <div class="text-slate-400">총 거래대금: <span class="font-bold text-slate-200">${{t.total_trade_value.toLocaleString()}}억원</span></div>
              </div>
            </div>
            ${{stocksTable}}
          `;
          container.appendChild(card);
        }});
      }}

      const table0198 = document.getElementById("table_0198_body");
      table0198.innerHTML = "";
      if (data.momentum_0198) {{
        data.momentum_0198.forEach(s => {{
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td class="p-3 text-center font-bold text-amber-400">${{s.rank}}</td>
            <td class="p-3 font-semibold text-white">${{s.name}} <span class="text-xs text-slate-500 font-normal">(${{s.code}})</span></td>
            <td class="p-3 text-center"><span class="px-1.5 py-0.5 text-[10px] font-bold rounded ${{s.market === 'KOSPI' ? 'bg-emerald-900/60 text-emerald-300' : 'bg-blue-900/60 text-blue-300'}}">${{s.market}}</span></td>
            <td class="p-3 text-right">${{s.price.toLocaleString()}}원</td>
            <td class="p-3 text-right font-bold text-red-400">+${{s.rate.toFixed(2)}}%</td>
            <td class="p-3 text-right">${{s.trade_value_eok.toLocaleString()}}억</td>
            <td class="p-3 text-center font-bold text-amber-300">${{s.search_surge_rate}}</td>
            <td class="p-3 text-xs text-slate-400">${{s.reason || '-'}}</td>
          `;
          table0198.appendChild(tr);
        }});
      }}

      const tableKospi = document.getElementById("table_kospi_body");
      tableKospi.innerHTML = "";
      if (data.kospi_0184) {{
        data.kospi_0184.forEach(s => {{
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td class="p-3 text-center font-bold text-emerald-400">${{s.rank}}</td>
            <td class="p-3 font-semibold text-white">${{s.name}} <span class="text-xs text-slate-500 font-normal">(${{s.code}})</span></td>
            <td class="p-3 text-center"><span class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-900/60 text-emerald-300">KOSPI</span></td>
            <td class="p-3 text-right">${{s.price.toLocaleString()}}원</td>
            <td class="p-3 text-right font-bold ${{s.rate >= 0 ? 'text-red-400' : 'text-blue-400'}}">${{s.rate >= 0 ? '+' : ''}}${{s.rate.toFixed(2)}}%</td>
            <td class="p-3 text-right font-bold text-slate-100">${{s.trade_value_eok.toLocaleString()}}억원</td>
          `;
          tableKospi.appendChild(tr);
        }});
      }}

      const tableKosdaq = document.getElementById("table_kosdaq_body");
      tableKosdaq.innerHTML = "";
      if (data.kosdaq_0184) {{
        data.kosdaq_0184.forEach(s => {{
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td class="p-3 text-center font-bold text-blue-400">${{s.rank}}</td>
            <td class="p-3 font-semibold text-white">${{s.name}} <span class="text-xs text-slate-500 font-normal">(${{s.code}})</span></td>
            <td class="p-3 text-center"><span class="px-1.5 py-0.5 text-[10px] font-bold rounded bg-blue-900/60 text-blue-300">KOSDAQ</span></td>
            <td class="p-3 text-right">${{s.price.toLocaleString()}}원</td>
            <td class="p-3 text-right font-bold ${{s.rate >= 0 ? 'text-red-400' : 'text-blue-400'}}">${{s.rate >= 0 ? '+' : ''}}${{s.rate.toFixed(2)}}%</td>
            <td class="p-3 text-right font-bold text-slate-100">${{s.trade_value_eok.toLocaleString()}}억원</td>
          `;
          tableKosdaq.appendChild(tr);
        }});
      }}

      switchTab('tab_0659');
      modal.classList.remove("hidden");
    }}

    function closeModal() {{
      document.getElementById("detailModal").classList.add("hidden");
    }}

    function switchTab(tabId) {{
      const tabs = ['tab_0659', 'tab_0198', 'tab_kospi', 'tab_kosdaq'];
      tabs.forEach(t => {{
        const btn = document.getElementById(`btn_${{t}}`);
        const content = document.getElementById(`content_${{t}}`);
        if (t === tabId) {{
          btn.className = "px-4 py-2.5 text-sm font-semibold border-b-2 border-blue-500 text-blue-400 transition";
          content.classList.remove("hidden");
        }} else {{
          btn.className = "px-4 py-2.5 text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition";
          content.classList.add("hidden");
        }}
      }});
    }}

    renderCalendar();
  </script>
</body>
</html>
"""
        return html

    def _sync_to_google_drive(self, html_file: str, json_file: str):
        target_gdrive = self.gdrive_sync.target_dir
        if not target_gdrive:
            return
        gdrive_cal_dir = os.path.join(target_gdrive, "캘린더")
        os.makedirs(gdrive_cal_dir, exist_ok=True)
        try:
            self.gdrive_sync.sync_file(html_file, "캘린더")
            self.gdrive_sync.sync_file(json_file, "캘린더")
            print(f">> [CalendarGenerator] ☁️ 구글 드라이브 [캘린더] 폴더 동기화 완료: {gdrive_cal_dir}")
        except Exception as e:
            print(f">> [CalendarGenerator] 구글 드라이브 동기화 오류: {e}")

if __name__ == "__main__":
    gen = DesktopCalendarGenerator()
    gen.update_and_build()
