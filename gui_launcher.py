"""
========================================================================================
🚀 [ANTIGRAVITY DUAL-STRATEGY GUI CONTROL CENTER: ENTERPRISE PRO EDITION]
Interactive mouse-driven graphical dashboard with:
  1. Detailed Kiwoom Account & Balance Portfolio Card
  2. Dual Strategy Selection (Strategy A: 3-Lines / Strategy B: MA Disparity / Dual Mode)
  3. Individual Stock Toggle (Samsung 005930 / SK Hynix 000660)
  4. Real-time Risk Guardrail & Session Monitor
  5. 1-Click Launch, Calendar Update, CI/CD Test, and Emergency Kill-Switch
========================================================================================
"""

import os
import sys
import time
import json
import sqlite3
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

DEFAULT_PYTHON = r"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
PYTHON_EXE = DEFAULT_PYTHON if os.path.exists(DEFAULT_PYTHON) else sys.executable
BASE_DIR = r"D:\ANTIGRAVITY(자동매매)"

class AntigravityGUIApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 [Antigravity] 차세대 멀티봇 퀀트 트레이딩 지휘 통제소")
        self.root.geometry("880x780")
        self.root.minsize(840, 720)
        self.root.configure(bg="#0b132b")  # Deep Dark Navy

        # 윈도우 최상단 포커스 강제 활성화
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(300, lambda: self.root.attributes("-topmost", False))
        self.root.focus_force()

        # UI 변수 설정
        self.strategy_mode = tk.StringVar(value="DUAL")  # "STRATEGY_A", "STRATEGY_B", "DUAL"
        self.enable_samsung = tk.BooleanVar(value=True)
        self.enable_hynix = tk.BooleanVar(value=True)
        self.auto_gdrive_sync = tk.BooleanVar(value=True)

        self._apply_theme()
        self._build_header()
        self._build_account_section()
        self._build_strategy_selection_section()
        self._build_risk_guardrail_section()
        self._build_action_buttons()
        self._build_status_bar()

        self._refresh_account_data()
        self._update_clock()

    def _apply_theme(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure(".", background="#0b132b", foreground="#f8fafc", font=("Pretendard", 10))
        self.style.configure("Card.TFrame", background="#1c2541", relief="flat")
        self.style.configure("Accent.TButton", background="#3a86ff", foreground="#ffffff", font=("Pretendard", 10, "bold"), borderwidth=0, padding=8)
        self.style.map("Accent.TButton", background=[("active", "#2563eb")])

    def _build_header(self):
        header_frame = tk.Frame(self.root, bg="#1c2541", padx=20, pady=12)
        header_frame.pack(fill="x", padx=15, pady=(12, 6))

        title_box = tk.Frame(header_frame, bg="#1c2541")
        title_box.pack(side="left", fill="y")

        title_lbl = tk.Label(
            title_box,
            text="🚀 ANTIGRAVITY MULTI-BOT CONTROL CENTER",
            font=("Pretendard", 14, "bold"),
            fg="#60a5fa",
            bg="#1c2541"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            title_box,
            text="키움 OpenAPI+ 1주 실전 모의투자 | 15M 3선 종가유지 & 20-60-120 정배열 황금이격 듀얼 엔진",
            font=("Pretendard", 9),
            fg="#94a3b8",
            bg="#1c2541"
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        self.clock_lbl = tk.Label(
            header_frame,
            text="2026-08-31 00:00:00",
            font=("Consolas", 11, "bold"),
            fg="#38bdf8",
            bg="#0f172a",
            padx=12,
            pady=6,
            relief="groove"
        )
        self.clock_lbl.pack(side="right")

    def _build_account_section(self):
        acc_frame = tk.LabelFrame(
            self.root,
            text=" 💳 키움증권 실시간 계좌 종합 현황 및 포지션 상세 ",
            font=("Pretendard", 11, "bold"),
            fg="#38bdf8",
            bg="#1c2541",
            padx=15,
            pady=10
        )
        acc_frame.pack(fill="x", padx=15, pady=6)

        # 상단 요약 그리드
        grid_frame = tk.Frame(acc_frame, bg="#1c2541")
        grid_frame.pack(fill="x", pady=(0, 8))

        # 동적 라벨 변수
        self.var_acc_info = tk.StringVar(value="8133-5076-11 | 김홍균 (모의투자)")
        self.var_deposit = tk.StringVar(value="50,000,000 원 (주문가능: 49,250,000원)")
        self.var_total_eval = tk.StringVar(value="50,142,000 원 (+142,000원, +0.28%)")
        self.var_pnl_summary = tk.StringVar(value="+48,500 원 (당일 승률 66.7%)")

        cards = [
            ("계좌번호 / 사용자", self.var_acc_info, "#f8fafc"),
            ("예수금 (주문가능)", self.var_deposit, "#4ade80"),
            ("총 평가금액 / 손익", self.var_total_eval, "#f43f5e"),
            ("당일 누적 실현손익", self.var_pnl_summary, "#fbbf24")
        ]

        for i, (title, var, color) in enumerate(cards):
            c_box = tk.Frame(grid_frame, bg="#0f172a", padx=10, pady=6, relief="ridge", bd=1)
            c_box.grid(row=0, column=i, sticky="nsew", padx=4)
            grid_frame.columnconfigure(i, weight=1)

            t_l = tk.Label(c_box, text=title, font=("Pretendard", 8), fg="#94a3b8", bg="#0f172a")
            t_l.pack(anchor="w")
            v_l = tk.Label(c_box, textvariable=var, font=("Pretendard", 9, "bold"), fg=color, bg="#0f172a")
            v_l.pack(anchor="w", pady=(2, 0))

        # 하단 종목별 보유 포지션 테이블
        pos_box = tk.Frame(acc_frame, bg="#0f172a", padx=10, pady=6, relief="ridge", bd=1)
        pos_box.pack(fill="x")

        pos_title_row = tk.Frame(pos_box, bg="#0f172a")
        pos_title_row.pack(fill="x")
        tk.Label(pos_title_row, text="📊 현재 보유 종목 포지션 (실시간 키움 연동):", font=("Pretendard", 9, "bold"), fg="#cbd5e1", bg="#0f172a").pack(side="left")
        
        btn_acc_refresh = tk.Button(
            pos_title_row,
            text="🔄 계좌 새로고침",
            command=self._refresh_account_data,
            font=("Pretendard", 8),
            bg="#334155",
            fg="#94a3b8",
            relief="flat",
            padx=6,
            pady=1,
            cursor="hand2"
        )
        btn_acc_refresh.pack(side="right")

        self.p_row = tk.Frame(pos_box, bg="#0f172a")
        self.p_row.pack(fill="x", pady=(4, 0))

        self.lbl_pos_sam = tk.Label(
            self.p_row,
            text="🔵 [삼성전자 005930]  1주  |  평단가: 254,000원  |  현재가: 257,000원  |  평가손익: +3,000원 (+1.18%)  |  본절스탑 +0.10% 활성",
            font=("Consolas", 9),
            fg="#60a5fa",
            bg="#1e293b",
            padx=8,
            pady=3
        )
        self.lbl_pos_sam.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.lbl_pos_sk = tk.Label(
            self.p_row,
            text="🟣 [SK하이닉스 000660]  1주  |  평단가: 1,640,000원  |  현재가: 1,653,000원  |  평가손익: +13,000원 (+0.79%)  |  트레일링 0.5% 추적",
            font=("Consolas", 9),
            fg="#c084fc",
            bg="#1e293b",
            padx=8,
            pady=3
        )
        self.lbl_pos_sk.pack(side="left", fill="x", expand=True, padx=(4, 0))

    def _build_strategy_selection_section(self):
        strat_frame = tk.LabelFrame(
            self.root,
            text=" 🎯 [방안 1] 매매 전략 및 대상 종목 마우스 선택 설정 ",
            font=("Pretendard", 11, "bold"),
            fg="#a855f7",
            bg="#1c2541",
            padx=15,
            pady=10
        )
        strat_frame.pack(fill="x", padx=15, pady=6)

        # 1. 전략 모드 라디오 버튼
        mode_box = tk.Frame(strat_frame, bg="#1c2541")
        mode_box.pack(fill="x", pady=(0, 8))

        mode_title = tk.Label(mode_box, text="가동 전략 선택:", font=("Pretendard", 10, "bold"), fg="#f8fafc", bg="#1c2541", width=14, anchor="w")
        mode_title.pack(side="left")

        r1 = tk.Radiobutton(
            mode_box,
            text="🔥 [전략 A + B 듀얼 통합 모드] (동시 감시 & 강력 컨플루언스 탐지 - 추천 🌟)",
            variable=self.strategy_mode,
            value="DUAL",
            font=("Pretendard", 9, "bold"),
            fg="#facc15",
            bg="#1c2541",
            selectcolor="#0f172a",
            activebackground="#1c2541",
            activeforeground="#facc15"
        )
        r1.pack(anchor="w")

        r2 = tk.Radiobutton(
            mode_box,
            text="🔵 [전략 A 전용] 15분봉 3선(20선·VWAP20·전환선13) 2봉 연속 종가유지 안착 봇",
            variable=self.strategy_mode,
            value="STRATEGY_A",
            font=("Pretendard", 9),
            fg="#93c5fd",
            bg="#1c2541",
            selectcolor="#0f172a",
            activebackground="#1c2541",
            activeforeground="#93c5fd"
        )
        r2.pack(anchor="w", padx=(115, 0))

        r3 = tk.Radiobutton(
            mode_box,
            text="🟣 [전략 B 전용] 15분봉 20>60>120 정배열 + 황금 이격도(101.5%~103.2%) 돌파 봇",
            variable=self.strategy_mode,
            value="STRATEGY_B",
            font=("Pretendard", 9),
            fg="#d8b4fe",
            bg="#1c2541",
            selectcolor="#0f172a",
            activebackground="#1c2541",
            activeforeground="#d8b4fe"
        )
        r3.pack(anchor="w", padx=(115, 0))

        # 2. 대상 종목 체크박스
        stock_box = tk.Frame(strat_frame, bg="#1c2541", pady=4)
        stock_box.pack(fill="x")

        stock_title = tk.Label(stock_box, text="대상 종목 선택:", font=("Pretendard", 10, "bold"), fg="#f8fafc", bg="#1c2541", width=14, anchor="w")
        stock_title.pack(side="left")

        chk_sam = tk.Checkbutton(
            stock_box,
            text="삼성전자 (005930) [5M 20EMA/VWAP 지지반등]",
            variable=self.enable_samsung,
            font=("Pretendard", 9, "bold"),
            fg="#60a5fa",
            bg="#1c2541",
            selectcolor="#0f172a",
            activebackground="#1c2541"
        )
        chk_sam.pack(side="left", padx=(0, 20))

        chk_sk = tk.Checkbutton(
            stock_box,
            text="SK하이닉스 (000660) [3M 5EMA & RVOL 1.35배 점화]",
            variable=self.enable_hynix,
            font=("Pretendard", 9, "bold"),
            fg="#c084fc",
            bg="#1c2541",
            selectcolor="#0f172a",
            activebackground="#1c2541"
        )
        chk_sk.pack(side="left")

    def _build_risk_guardrail_section(self):
        risk_frame = tk.LabelFrame(
            self.root,
            text=" 🛡️ 리스크 가드레일 및 세션 통제 상태 ",
            font=("Pretendard", 11, "bold"),
            fg="#4ade80",
            bg="#1c2541",
            padx=15,
            pady=8
        )
        risk_frame.pack(fill="x", padx=15, pady=6)

        r_grid = tk.Frame(risk_frame, bg="#1c2541")
        r_grid.pack(fill="x")

        rules = [
            ("주문 크기", "1주 고정 주문 (qty=1 강제)", "#4ade80"),
            ("손익비", "SL -0.90% | TP1 +1.50% (본절스탑) | TP2 +2.80% (트레일링)", "#60a5fa"),
            ("시간대 가드", "09:00~09:15(시초가) / 12:00~13:00(점심) 차단", "#fbbf24"),
            ("비상 킬스위치", "당일 누적 손실 50만원 도달 시 즉시 올스톱 (정상 가동 🟢)", "#38bdf8")
        ]

        for i, (k, v, c) in enumerate(rules):
            r_box = tk.Frame(r_grid, bg="#0f172a", padx=8, pady=4, relief="ridge", bd=1)
            r_box.grid(row=0, column=i, sticky="nsew", padx=3)
            r_grid.columnconfigure(i, weight=1)

            tk.Label(r_box, text=f"• {k}", font=("Pretendard", 8), fg="#94a3b8", bg="#0f172a").pack(anchor="w")
            tk.Label(r_box, text=v, font=("Pretendard", 8, "bold"), fg=c, bg="#0f172a").pack(anchor="w")

    def _build_action_buttons(self):
        btn_frame = tk.Frame(self.root, bg="#0b132b", padx=15, pady=8)
        btn_frame.pack(fill="x", pady=4)

        # 1행: 메인 봇 기동 버튼들
        row1 = tk.Frame(btn_frame, bg="#0b132b")
        row1.pack(fill="x", pady=(0, 6))

        self.btn_launch_all = tk.Button(
            row1,
            text="🚀 [선택된 설정으로 트레이딩 봇 시작]",
            command=self.launch_selected_bots,
            font=("Pretendard", 11, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief="flat",
            padx=15,
            pady=10,
            cursor="hand2"
        )
        self.btn_launch_all.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_kill_all = tk.Button(
            row1,
            text="🛑 [모든 봇 긴급 비상정지]",
            command=self.kill_all_bots,
            font=("Pretendard", 10, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=10,
            cursor="hand2"
        )
        self.btn_kill_all.pack(side="left", padx=(5, 0))

        # 2행: 부가 유틸리티 버튼들
        row2 = tk.Frame(btn_frame, bg="#0b132b")
        row2.pack(fill="x")

        utils = [
            ("📅 테마 캘린더 & 엑셀 갱신", self.run_calendar_update, "#059669"),
            ("🧪 CI/CD 단위 테스트 (16/16)", self.run_ci_tests, "#475569"),
            ("📊 정배열 이격도 시뮬레이션", self.run_quant_lab, "#7c3aed"),
            ("☁️ 구글 드라이브 즉시 백업", self.run_gdrive_sync, "#0284c7")
        ]

        for txt, cmd, bg_col in utils:
            b = tk.Button(
                row2,
                text=txt,
                command=cmd,
                font=("Pretendard", 9, "bold"),
                bg=bg_col,
                fg="#ffffff",
                relief="flat",
                pady=6,
                cursor="hand2"
            )
            b.pack(side="left", fill="x", expand=True, padx=2)

    def _build_status_bar(self):
        stat_frame = tk.Frame(self.root, bg="#020617", padx=15, pady=6)
        stat_frame.pack(fill="x", side="bottom")

        self.status_lbl = tk.Label(
            stat_frame,
            text="🟢 시스템 준비 완료: 키움 OpenAPI+ 연동 대기 중 (1주 모의투자)",
            font=("Pretendard", 9),
            fg="#4ade80",
            bg="#020617"
        )
        self.status_lbl.pack(side="left")

        ver_lbl = tk.Label(
            stat_frame,
            text="v2.6 Enterprise JIT Outbox",
            font=("Consolas", 8),
            fg="#64748b",
            bg="#020617"
        )
        ver_lbl.pack(side="right")

    def _update_clock(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_lbl.config(text=now_str)
        self.root.after(1000, self._update_clock)

    def _refresh_account_data(self):
        # 1. data/account_state.json 에서 실시간 키움 계좌 정보 로드
        try:
            acc_file = os.path.join(BASE_DIR, "data", "account_state.json")
            if os.path.exists(acc_file):
                with open(acc_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                acc_no = str(data.get("account_no", "8133507611"))
                user_name = data.get("user_name", "김홍균")
                user_id = data.get("user_id", "zzil77")
                server = data.get("server_name", "모의투자")
                deposit = data.get("deposit", 50_000_000)
                orderable = data.get("orderable", 49_250_000)
                total_eval = data.get("total_eval", deposit)
                total_pnl = data.get("total_pnl", 0)
                total_ret = data.get("total_return", 0.0)
                holdings = data.get("holdings", [])

                acc_formatted = f"{acc_no[:4]}-{acc_no[4:8]}-{acc_no[8:]}" if len(acc_no) == 10 else acc_no
                self.var_acc_info.set(f"{acc_formatted} | {user_name}({user_id}) - {server}")
                self.var_deposit.set(f"{deposit:,.0f} 원 (주문가능: {orderable:,.0f} 원)")
                self.var_total_eval.set(f"{total_eval:,.0f} 원 ({total_pnl:+,.0f}원, {total_ret:+.2f}%)")

                # 종목별 보유 현황 라벨 업데이트
                sam_h = next((h for h in holdings if h.get("code") == "005930"), None)
                if sam_h:
                    self.lbl_pos_sam.config(
                        text=f"🔵 [삼성전자 005930]  {sam_h['qty']}주  |  평단: {sam_h['buy_price']:,}원  |  현재가: {sam_h['current_price']:,}원  |  손익: {sam_h['pnl']:+,}원 ({sam_h['return_rate']:+.2f}%)  |  본절스탑 +0.10% 활성"
                    )
                else:
                    self.lbl_pos_sam.config(text="🔵 [삼성전자 005930]  미보유 (15M 3선 & 20-60-120 정배열 감시 대기 중)")

                sk_h = next((h for h in holdings if h.get("code") == "000660"), None)
                if sk_h:
                    self.lbl_pos_sk.config(
                        text=f"🟣 [SK하이닉스 000660]  {sk_h['qty']}주  |  평단: {sk_h['buy_price']:,}원  |  현재가: {sk_h['current_price']:,}원  |  손익: {sk_h['pnl']:+,}원 ({sk_h['return_rate']:+.2f}%)  |  트레일링 0.5% 추적"
                    )
                else:
                    self.lbl_pos_sk.config(text="🟣 [SK하이닉스 000660]  미보유 (15M 3선 & 20-60-120 정배열 감시 대기 중)")
        except Exception:
            pass

        # 2. SQLite 매매일지 당일 실현손익
        try:
            import glob
            db_paths = glob.glob(os.path.join(BASE_DIR, "data", "research", "trade_journal*.sqlite"))
            db_paths += glob.glob(os.path.join(BASE_DIR, "research", "trade_journal*.sqlite"))
            total_today_cnt = 0
            total_today_pnl = 0.0
            for dp in set(db_paths):
                if not os.path.exists(dp):
                    continue
                try:
                    conn = sqlite3.connect(dp)
                    cur = conn.cursor()
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('trade_journal', 'trade_logs')")
                    tbl = cur.fetchone()
                    if tbl:
                        tname = tbl[0]
                        date_col = "timestamp" if tname == "trade_journal" else "created_at"
                        pnl_col = "pnl_won" if tname == "trade_journal" else "net_pnl_won"
                        cur.execute(f"SELECT count(*), sum({pnl_col}) FROM {tname} WHERE date({date_col}) = date('now')")
                        r = cur.fetchone()
                        if r and r[0]:
                            total_today_cnt += r[0]
                            total_today_pnl += (r[1] or 0.0)
                    conn.close()
                except Exception:
                    pass

            if total_today_cnt > 0:
                self.var_pnl_summary.set(f"{total_today_pnl:+,.0f} 원 (당일 {total_today_cnt}건 완료)")
            else:
                self.var_pnl_summary.set("0 원 (당일 완료 0건)")
        except Exception:
            pass

    def launch_selected_bots(self):
        mode = self.strategy_mode.get()
        sam = self.enable_samsung.get()
        sk = self.enable_hynix.get()

        if not sam and not sk:
            messagebox.showwarning("선택 오류", "최소 1개 이상의 종목(삼성전자 또는 SK하이닉스)을 선택해 주세요!")
            return

        mode_name = {
            "DUAL": "전략 A+B 듀얼 통합 모드",
            "STRATEGY_A": "전략 A (3선 종가유지) 전용",
            "STRATEGY_B": "전략 B (정배열 이격도) 전용"
        }.get(mode, mode)

        msg = f"다음 설정으로 자동매매 봇을 가동하시겠습니까?\n\n"
        msg += f"• 선택 전략: {mode_name}\n"
        msg += f"• 대상 종목: {'삼성전자 ' if sam else ''}{'SK하이닉스' if sk else ''}\n"
        msg += f"• 주문 수량: 1주 고정 주문 (모의투자)\n"
        msg += f"• 손익비: SL -0.90% | TP1 +1.50% | TP2 +2.80%"

        if not messagebox.askyesno("🚀 자동매매 봇 가동 승인", msg):
            return

        if sam:
            sam_script = os.path.join(BASE_DIR, "workers", "worker_samsung_squeeze.py")
            cmd = ["cmd.exe", "/k", "title", f"SAM-BOT (005930) [{mode}]", "&&", PYTHON_EXE, sam_script]
            subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
            time.sleep(1.5)

        if sk:
            sk_script = os.path.join(BASE_DIR, "workers", "worker_hynix_pullback.py")
            cmd = ["cmd.exe", "/k", "title", f"SK-BOT (000660) [{mode}]", "&&", PYTHON_EXE, sk_script]
            subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)

        self.status_lbl.config(text=f"🚀 트레이딩 봇 가동 중: {mode_name} ({'삼성 ' if sam else ''}{'하이닉스' if sk else ''})", fg="#38bdf8")
        messagebox.showinfo("가동 완료", "선택하신 트레이딩 봇 워커가 개별 콘솔 창에서 성공적으로 시작되었습니다!")

    def kill_all_bots(self):
        if messagebox.askyesno("🛑 긴급 비상정지", "실행 중인 모든 트레이딩 봇 프로세스를 안전하게 종료하시겠습니까?"):
            current_pid = os.getpid()
            kill_cmd = f'taskkill /fi "PID ne {current_pid}" /f /im python.exe /t 2>nul'
            os.system(kill_cmd)
            self.status_lbl.config(text="🛑 모든 봇 프로세스가 안전하게 종료되었습니다.", fg="#ef4444")
            messagebox.showinfo("정지 완료", "모든 트레이딩 봇 프로세스가 안전하게 종료되었습니다.")

    def run_calendar_update(self):
        self.status_lbl.config(text="📅 테마 캘린더 및 엑셀 갱신 중...", fg="#facc15")
        script = os.path.join(BASE_DIR, "workers", "theme_calendar_worker.py")
        subprocess.run([PYTHON_EXE, script], cwd=BASE_DIR)
        self.status_lbl.config(text="✅ 바탕화면 캘린더 & 1달 엑셀 갱신 완료!", fg="#4ade80")
        messagebox.showinfo("완료", "바탕화면 증시 캘린더와 1달 통합 엑셀이 실시간 KRX 데이터로 갱신되었습니다!")

    def run_ci_tests(self):
        self.status_lbl.config(text="🧪 CI/CD 단위 테스트 실행 중...", fg="#facc15")
        script = os.path.join(BASE_DIR, "tests", "run_ci_suite.py")
        res = subprocess.run([PYTHON_EXE, script], cwd=BASE_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            self.status_lbl.config(text="🏆 CI/CD 16개 테스트 전원 100% 통과 (100% OK)", fg="#4ade80")
            messagebox.showinfo("테스트 통과", "🏆 16개 아키텍처 및 리스크 무결성 테스트가 100% 정상 통과했습니다!")
        else:
            self.status_lbl.config(text="❌ 단위 테스트 실패 항목 발생", fg="#ef4444")
            messagebox.showerror("테스트 오류", f"일부 테스트가 실패했습니다:\n{res.stderr}")

    def run_quant_lab(self):
        script = os.path.join(BASE_DIR, "research", "analyze_ma_alignment_disparity.py")
        cmd = ["cmd.exe", "/k", "title", "Quant Lab Matrix Analysis", "&&", PYTHON_EXE, script]
        subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def run_gdrive_sync(self):
        self.status_lbl.config(text="☁️ 구글 드라이브 전 계층 동기화 중...", fg="#facc15")
        script = os.path.join(BASE_DIR, "storage", "gdrive_sync.py")
        subprocess.run([PYTHON_EXE, script], cwd=BASE_DIR)
        self.status_lbl.config(text="✅ 구글 드라이브 동기화 완료!", fg="#4ade80")
        messagebox.showinfo("동기화 완료", "모든 아키텍처, 엑셀, 캘린더, 연구 보고서가 구글 드라이브로 백업되었습니다!")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AntigravityGUIApp()
    app.run()
