"""
========================================================================================
🔔 [SCHEDULER & INTERACTIVE APPROVAL MODAL: DAILY MORNING TRADING AUTHORIZATION]
Pops up an interactive GUI modal on business day mornings for user decision & approval.
========================================================================================
"""

import os
import sys
import subprocess
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

DEFAULT_PYTHON = r"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
PYTHON_EXE = DEFAULT_PYTHON if os.path.exists(DEFAULT_PYTHON) else sys.executable
BASE_DIR = r"D:\ANTIGRAVITY(자동매매)"

class MorningApprovalDialog:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔔 [Antigravity] 장 시작 전 실전 자동매매 가동 승인")
        self.root.geometry("640x540")
        self.root.configure(bg="#0f172a")  # Slate 900
        self.root.resizable(False, False)
        
        # 화면 중앙 배치
        self.root.eval('tk::PlaceWindow . center')
        # 최상위 윈도우 고정
        self.root.attributes("-topmost", True)

        self.selected_action = None
        self._build_ui()

    def _build_ui(self):
        # 1. 헤더
        header_frame = tk.Frame(self.root, bg="#1e293b", padx=20, pady=15)
        header_frame.pack(fill="x")

        now_str = datetime.now().strftime("%Y년 %m월 %d일 (%a) %H:%M")
        title_label = tk.Label(
            header_frame,
            text=f"📅 {now_str} 증시 장 개장 알림",
            font=("Pretendard", 14, "bold"),
            fg="#60a5fa",
            bg="#1e293b"
        )
        title_label.pack(anchor="w")

        sub_label = tk.Label(
            header_frame,
            text="오늘자 실전 1주 자동매매 봇 가동 여부를 승인해 주세요.",
            font=("Pretendard", 10),
            fg="#94a3b8",
            bg="#1e293b"
        )
        sub_label.pack(anchor="w", pady=(3, 0))

        # 2. 본문 컨테이너 (전략 및 안전 가드레일 요약)
        body_frame = tk.Frame(self.root, bg="#0f172a", padx=20, pady=15)
        body_frame.pack(fill="both", expand=True)

        # 전략 카드
        card_frame = tk.LabelFrame(
            body_frame,
            text=" 🎯 가동 예정 전략 및 안전 세팅 (1주 모의투자) ",
            font=("Pretendard", 10, "bold"),
            fg="#cbd5e1",
            bg="#1e293b",
            padx=15,
            pady=12
        )
        card_frame.pack(fill="x", pady=(0, 15))

        items = [
            ("🔵 전략 A (3선 종가유지)", "15분봉 3선(20선·VWAP20·전환선13) 2봉 연속 종가 안착 확인"),
            ("🟣 전략 B (정배열 이격도)", "15분봉 20>60>120 정배열 + 황금 이격도(101.5%~103.2%) 돌파"),
            ("🎯 서브 실행 트리거", "삼성전자(5M 20EMA/VWAP 지지) / SK하이닉스(3M 5EMA & RVOL 1.35배)"),
            ("🛡️ 손익비 가드레일", "1주 고정(qty=1), SL -0.90%, TP1 +1.50%(본절스탑), TP2 +2.80%(트레일링)"),
            ("⏰ 시간대 블랙아웃", "09:00~09:15(시초가), 12:00~13:00(점심 휩쏘), 15:15(장마감) 차단"),
            ("🛑 비상 킬 스위치", "당일 누적 손실 50만원 도달 또는 2회 연속 손실 시 즉시 동결")
        ]

        for title, desc in items:
            row = tk.Frame(card_frame, bg="#1e293b", pady=3)
            row.pack(fill="x")
            t_lbl = tk.Label(row, text=f"• {title}:", font=("Pretendard", 9, "bold"), fg="#f8fafc", bg="#1e293b", width=18, anchor="w")
            t_lbl.pack(side="left")
            d_lbl = tk.Label(row, text=desc, font=("Pretendard", 9), fg="#94a3b8", bg="#1e293b", anchor="w")
            d_lbl.pack(side="left", fill="x", expand=True)

        # 3. 버튼 영역
        btn_frame = tk.Frame(self.root, bg="#0f172a", padx=20, pady=10)
        btn_frame.pack(fill="x", side="bottom")

        btn_all = tk.Button(
            btn_frame,
            text="🚀 [승인] 전체 봇 (삼성 + 하이닉스) 즉시 가동",
            font=("Pretendard", 11, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            padx=15,
            pady=10,
            cursor="hand2",
            command=lambda: self._on_select("ALL")
        )
        btn_all.pack(fill="x", pady=(0, 8))

        sub_btn_row = tk.Frame(btn_frame, bg="#0f172a")
        sub_btn_row.pack(fill="x", pady=(0, 8))

        btn_sam = tk.Button(
            sub_btn_row,
            text="🤖 삼성전자만",
            font=("Pretendard", 9, "bold"),
            bg="#334155",
            fg="#f1f5f9",
            activebackground="#475569",
            activeforeground="white",
            relief="flat",
            pady=8,
            cursor="hand2",
            command=lambda: self._on_select("SAMSUNG_ONLY")
        )
        btn_sam.pack(side="left", fill="x", expand=True, padx=(0, 4))

        btn_sk = tk.Button(
            sub_btn_row,
            text="⚡ SK하이닉스만",
            font=("Pretendard", 9, "bold"),
            bg="#334155",
            fg="#f1f5f9",
            activebackground="#475569",
            activeforeground="white",
            relief="flat",
            pady=8,
            cursor="hand2",
            command=lambda: self._on_select("SK_ONLY")
        )
        btn_sk.pack(side="left", fill="x", expand=True, padx=(4, 4))

        btn_skip = tk.Button(
            sub_btn_row,
            text="🛑 오늘 매매 건너뛰기",
            font=("Pretendard", 9, "bold"),
            bg="#991b1b",
            fg="white",
            activebackground="#7f1d1d",
            activeforeground="white",
            relief="flat",
            pady=8,
            cursor="hand2",
            command=lambda: self._on_select("SKIP")
        )
        btn_skip.pack(side="left", fill="x", expand=True, padx=(4, 0))

    def _on_select(self, action: str):
        self.selected_action = action
        self.root.destroy()

    def show(self) -> str:
        self.root.mainloop()
        return self.selected_action or "SKIP"

def launch_workers(action: str):
    if action == "ALL":
        print("\n>> [APPROVAL] 🚀 트레이더 승인: 삼성전자 & SK하이닉스 전체 봇 가동 시작...")
        cmd_sam = ["cmd.exe", "/k", "title", "SAM-BOT (005930)", "&&", PYTHON_EXE, os.path.join(BASE_DIR, "workers", "worker_samsung_squeeze.py")]
        cmd_sk = ["cmd.exe", "/k", "title", "SK-BOT (000660)", "&&", PYTHON_EXE, os.path.join(BASE_DIR, "workers", "worker_hynix_pullback.py")]
        subprocess.Popen(cmd_sam, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
        time.sleep(2)
        subprocess.Popen(cmd_sk, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
        print(">> [OK] 전체 봇 워커가 성공적으로 기동되었습니다!")

    elif action == "SAMSUNG_ONLY":
        print("\n>> [APPROVAL] 🤖 트레이더 승인: 삼성전자 봇 가동 시작...")
        cmd_sam = ["cmd.exe", "/k", "title", "SAM-BOT (005930)", "&&", PYTHON_EXE, os.path.join(BASE_DIR, "workers", "worker_samsung_squeeze.py")]
        subprocess.Popen(cmd_sam, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)

    elif action == "SK_ONLY":
        print("\n>> [APPROVAL] ⚡ 트레이더 승인: SK하이닉스 봇 가동 시작...")
        cmd_sk = ["cmd.exe", "/k", "title", "SK-BOT (000660)", "&&", PYTHON_EXE, os.path.join(BASE_DIR, "workers", "worker_hynix_pullback.py")]
        subprocess.Popen(cmd_sk, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)

    elif action == "SKIP":
        print("\n>> [NOTICE] 🛑 트레이더 선택: 오늘의 자동매매를 건너뜁니다.")

if __name__ == "__main__":
    dialog = MorningApprovalDialog()
    user_choice = dialog.show()
    launch_workers(user_choice)
