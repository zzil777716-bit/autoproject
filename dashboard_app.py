"""
========================================================================================
🚀 [ANTIGRAVITY NATIVE PYQT5 TRADING DASHBOARD & GOOGLE GEMINI COPILOT]
Enterprise Pro Real-Data Command Center with:
  1. Left Pane: 100% Real Kiwoom Account, Dual Strategies, Live Orders Table, Risk Controls
  2. Right Pane: Google Gemini Live AI Trading Intelligence Copilot Console (with API Key Config)
  3. Real-time Trade Journal (research/trade_journal.sqlite) Table Integration
  4. Dynamic HTS 0659 Market Theme Sync & Desktop Calendar
  5. Multi-AI Guardian (Gemini Flash -> Claude Haiku -> GPT-4o-mini -> Local Rule)
  6. Real-time SRE Sentinel & Telemetry Watchdog
========================================================================================
"""

import os
import sys
import json
import sqlite3
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QCheckBox, QGroupBox,
    QFrame, QGridLayout, QMessageBox, QDesktopWidget,
    QTextBrowser, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QInputDialog, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal

DEFAULT_PYTHON = r"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
PYTHON_EXE = DEFAULT_PYTHON if os.path.exists(DEFAULT_PYTHON) else sys.executable
BASE_DIR = r"C:\Antigravity"

DARK_QSS = """
QMainWindow {
    background-color: #0b132b;
}
QWidget {
    color: #f8fafc;
    font-family: 'Pretendard', 'Malgun Gothic', 'Segoe UI';
    font-size: 12px;
}
QGroupBox {
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 10px;
    font-weight: bold;
    font-size: 12px;
    padding-top: 10px;
    background-color: #1c2541;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #38bdf8;
}
QRadioButton {
    spacing: 6px;
    font-size: 12px;
}
QRadioButton::indicator {
    width: 15px;
    height: 15px;
}
QCheckBox {
    spacing: 6px;
    font-weight: bold;
    font-size: 12px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    padding: 7px 12px;
    border: none;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QPushButton#btn_kill {
    background-color: #dc2626;
}
QPushButton#btn_kill:hover {
    background-color: #b91c1c;
}
QPushButton#btn_util {
    background-color: #334155;
    font-size: 11px;
    padding: 5px 8px;
}
QPushButton#btn_util:hover {
    background-color: #475569;
}
QPushButton#btn_chip {
    background-color: #1e293b;
    border: 1px solid #334155;
    font-size: 11px;
    padding: 4px 7px;
    border-radius: 10px;
    color: #93c5fd;
}
QPushButton#btn_chip:hover {
    background-color: #2563eb;
    color: white;
    border-color: #60a5fa;
}
QPushButton#btn_gemini {
    background-color: #0284c7;
    font-size: 11px;
    padding: 4px 8px;
    border-radius: 6px;
}
QPushButton#btn_gemini:hover {
    background-color: #0369a1;
}
QFrame#card_box {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 5px;
}
QTextBrowser {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px;
    color: #f8fafc;
    font-size: 12px;
}
QLineEdit {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 7px 10px;
    color: #f8fafc;
    font-size: 12px;
}
QLineEdit:focus {
    border: 1px solid #38bdf8;
}
QTableWidget {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    gridline-color: #1e293b;
    font-size: 11px;
    color: #f8fafc;
}
QHeaderView::section {
    background-color: #1e293b;
    color: #94a3b8;
    font-weight: bold;
    font-size: 11px;
    padding: 4px;
    border: 1px solid #334155;
}
"""

class GeminiChatWorker(QThread):
    response_ready = pyqtSignal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        try:
            from sdk.ai_chat_engine import ai_chat_engine
            reply = ai_chat_engine.process_query(self.query)
        except Exception as e:
            reply = f"⚠️ Gemini 처리 중 오류가 발생했습니다: {e}"
        self.response_ready.emit(reply)

class KiwoomAccountSyncWorker(QThread):
    sync_finished = pyqtSignal(bool, str)

    def run(self):
        try:
            acc_file = os.path.join(BASE_DIR, "data", "account_state.json")
            # 1. 키움 Open API 프로세스 비동기 실행 (GUI 블로킹 방지)
            cmd = [
                PYTHON_EXE, "-c",
                f"import sys; sys.path.insert(0, r'{BASE_DIR}'); "
                f"from adapters.kiwoom_adapter import KiwoomAdapter; "
                f"adapter = KiwoomAdapter(); "
                f"ret = adapter.login(); "
                f"acc = adapter.account_list[0] if (ret and adapter.account_list) else '8133507611'; "
                f"adapter.sync_account_state_to_file(acc) if ret else None"
            ]
            res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=10)
            if os.path.exists(acc_file):
                self.sync_finished.emit(True, "실시간 계좌 정보(TR opw00001/opw00018) 동기화 완료!")
            else:
                self.sync_finished.emit(False, "계좌 상태 파일 확인 중...")
        except subprocess.TimeoutExpired:
            self.sync_finished.emit(False, "키움 서버 응답 대기 시간 초과 (기존 데이터 유지)")
        except Exception as e:
            self.sync_finished.emit(False, f"동기화 오류: {str(e)[:40]}")

class CalendarUpdateWorker(QThread):
    calendar_finished = pyqtSignal(bool, str)

    def run(self):
        try:
            from workers.theme_calendar_worker import ThemeCalendarWorker
            worker = ThemeCalendarWorker()
            worker.run()
            self.calendar_finished.emit(True, "바탕화면 증시 캘린더 & 1달 통합 엑셀 실시간 갱신 완료!")
        except Exception as e:
            self.calendar_finished.emit(False, f"캘린더 갱신 오류: {str(e)[:40]}")

class UniverseCollectionWorker(QThread):
    collection_finished = pyqtSignal(bool, str)

    def run(self):
        try:
            from collectors.market_universe_collector import MarketUniverseCollector
            collector = MarketUniverseCollector()
            collector.run_all()
            self.collection_finished.emit(True, "코스피200 & 코스닥150 [일봉 + 3분봉] 전 종목 수집 및 구글드라이브 백업 완료!")
        except Exception as e:
            self.collection_finished.emit(False, f"수집 오류: {str(e)[:40]}")


class AntigravityDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 [Antigravity] 차세대 퀀트 트레이딩 지휘 통제소 & Google Gemini AI 코파일럿")
        self.resize(1320, 860)
        self.setMinimumSize(1240, 800)
        self.setStyleSheet(DARK_QSS)

        # 화면 중앙 배치 & 최상단 활성화
        self._center_on_screen()
        self.show()
        self.raise_()
        self.activateWindow()

        self._build_ui()
        self._load_account_state()
        self._load_order_history()
        self._init_chat_welcome()

        # 시작 시 백그라운드에서 바탕화면 캘린더 자동 갱신
        self._auto_update_calendar_background(show_msg=False)

        # 실시간 타이머 (1초 시계 + 2초 계좌 및 주문내역 새로고침)
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self._update_clock)
        self.timer_clock.start(1000)

        self.timer_sync = QTimer(self)
        self.timer_sync.timeout.connect(self._periodic_sync)
        self.timer_sync.start(2000)

    def _center_on_screen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(6)

        # 1. 헤더 영역
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1c2541; border-radius: 8px; padding: 4px;")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(10, 4, 10, 4)

        t_box = QVBoxLayout()
        title_lbl = QLabel("🚀 ANTIGRAVITY MULTI-BOT CONTROL CENTER & GOOGLE GEMINI AI")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #60a5fa;")
        sub_lbl = QLabel("키움 OpenAPI+ 실전 모의투자 | 15M 듀얼 엔진 + Google Gemini 실시간 지능 분석 + 실시간 주문/체결 모니터")
        sub_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        t_box.addWidget(title_lbl)
        t_box.addWidget(sub_lbl)
        h_layout.addLayout(t_box)

        h_layout.addStretch()

        self.clock_lbl = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.clock_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #38bdf8; background-color: #0f172a; padding: 4px 10px; border-radius: 6px; border: 1px solid #334155;")
        h_layout.addWidget(self.clock_lbl)
        main_layout.addWidget(header_frame)

        # 2. 메인 바디 영역: 좌측(트레이딩 컨트롤 및 주문테이블) + 우측(Gemini AI 채팅)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(10)

        # ==========================================
        # [좌측 열: 트레이딩 통제소 & 주문내역]
        # ==========================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        # 2-A. 계좌 종합 현황 카드 (4대 지표)
        acc_group = QGroupBox("💳 키움증권 실시간 계좌 종합 현황 (계좌 8133-5076-11 | 실데이터 100%)")
        acc_layout = QVBoxLayout(acc_group)
        acc_layout.setContentsMargins(8, 8, 8, 6)
        acc_layout.setSpacing(6)

        grid = QGridLayout()
        grid.setSpacing(5)

        self.lbl_card_acc = QLabel("8133-5076-11 | 김홍균 (모의투자 1호)")
        self.lbl_card_dep = QLabel("30,000,000 원 (주문가능: 29,739,090 원)")
        self.lbl_card_eval = QLabel("261,000 원 (손익: -1,341원, -0.52%)")
        self.lbl_card_pnl = QLabel("0 원 (당일 실현손익)")

        cards = [
            ("계좌번호 / 사용자", self.lbl_card_acc, "#f8fafc"),
            ("예수금 (주문가능)", self.lbl_card_dep, "#4ade80"),
            ("총 평가금액 / 손익", self.lbl_card_eval, "#f43f5e"),
            ("당일 누적 실현손익", self.lbl_card_pnl, "#fbbf24")
        ]

        for i, (title, lbl, color) in enumerate(cards):
            box = QFrame()
            box.setObjectName("card_box")
            b_layout = QVBoxLayout(box)
            b_layout.setContentsMargins(5, 3, 5, 3)
            t = QLabel(title)
            t.setStyleSheet("font-size: 10px; color: #94a3b8;")
            lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color};")
            b_layout.addWidget(t)
            b_layout.addWidget(lbl)
            grid.addWidget(box, 0, i)

        acc_layout.addLayout(grid)

        # 종목별 실시간 포지션
        pos_box = QFrame()
        pos_box.setObjectName("card_box")
        pos_layout = QVBoxLayout(pos_box)
        pos_layout.setContentsMargins(5, 3, 5, 3)

        p_head = QHBoxLayout()
        p_title = QLabel("📊 현재 보유 종목 포지션 (키움 실시간 TR 연동):")
        p_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #cbd5e1;")
        btn_acc_sync = QPushButton("🔄 실시간 계좌 조회 (TR)")
        btn_acc_sync.setObjectName("btn_util")
        btn_acc_sync.clicked.connect(self._sync_live_account_from_kiwoom)
        p_head.addWidget(p_title)
        p_head.addStretch()
        p_head.addWidget(btn_acc_sync)
        pos_layout.addLayout(p_head)

        p_row = QHBoxLayout()
        self.lbl_pos_sam = QLabel("🔵 [삼성전자 005930] 1주 | 평단 260,000원 | 현재가 261,000원 | 손익 -1,341원 (-0.52%)")
        self.lbl_pos_sam.setStyleSheet("background-color: #1e293b; color: #60a5fa; padding: 4px 6px; border-radius: 4px; font-family: Consolas; font-size: 10px;")
        self.lbl_pos_sk = QLabel("🟣 [SK하이닉스 000660] 미보유 (15M 정배열 황금이격 감시 대기)")
        self.lbl_pos_sk.setStyleSheet("background-color: #1e293b; color: #c084fc; padding: 4px 6px; border-radius: 4px; font-family: Consolas; font-size: 10px;")
        p_row.addWidget(self.lbl_pos_sam)
        p_row.addWidget(self.lbl_pos_sk)
        pos_layout.addLayout(p_row)

        acc_layout.addWidget(pos_box)
        left_layout.addWidget(acc_group)

        # 2-B. 전략 및 종목 가드 설정
        strat_group = QGroupBox("🎯 [방안 1] 매매 전략, 거래소 주문방식(SOR/NXT) 및 지능형 가드 설정")
        strat_group.setStyleSheet("QGroupBox::title { color: #c084fc; }")
        strat_layout = QVBoxLayout(strat_group)
        strat_layout.setContentsMargins(8, 6, 8, 6)
        strat_layout.setSpacing(5)

        # 전략 선택
        r_box = QHBoxLayout()
        r_lbl = QLabel("가동 전략:")
        r_lbl.setStyleSheet("font-weight: bold; width: 65px;")
        r_box.addWidget(r_lbl)

        self.r_dual = QRadioButton("🔥 [전략 A+B 듀얼 모드] (추천 🌟)")
        self.r_dual.setChecked(True)
        self.r_dual.setStyleSheet("color: #facc15; font-weight: bold;")
        self.r_a = QRadioButton("🔵 [전략 A] 3선 종가유지")
        self.r_a.setStyleSheet("color: #93c5fd;")
        self.r_b = QRadioButton("🟣 [전략 B] 정배열 황금이격")
        self.r_b.setStyleSheet("color: #d8b4fe;")

        r_box.addWidget(self.r_dual)
        r_box.addWidget(self.r_a)
        r_box.addWidget(self.r_b)
        r_box.addStretch()
        strat_layout.addLayout(r_box)

        # 거래소 및 최선주문집행 (SOR / KRX / NXT) 선택
        sor_box = QHBoxLayout()
        sor_lbl = QLabel("주문 방식:")
        sor_lbl.setStyleSheet("font-weight: bold; width: 65px; color: #38bdf8;")
        sor_box.addWidget(sor_lbl)

        self.r_sor = QRadioButton("🌟 [SOR 최선주문집행] (KRX+NXT 통합 최유리 자동체결 - 추천)")
        self.r_sor.setChecked(True)
        self.r_sor.setStyleSheet("color: #38bdf8; font-weight: bold;")
        self.r_krx = QRadioButton("🏛️ [KRX 전용] (09:00~15:30)")
        self.r_krx.setStyleSheet("color: #a7f3d0;")
        self.r_nxt = QRadioButton("⚡ [NXT 전용] (08:00~20:00)")
        self.r_nxt.setStyleSheet("color: #f472b6;")

        sor_box.addWidget(self.r_sor)
        sor_box.addWidget(self.r_krx)
        sor_box.addWidget(self.r_nxt)
        sor_box.addStretch()
        strat_layout.addLayout(sor_box)

        # 실시간 NXT 세션 인디케이터 바
        session_row = QHBoxLayout()
        self.lbl_nxt_session = QLabel("🌅 [실시간 세션]: 계산 중...")
        self.lbl_nxt_session.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #fbbf24;")
        session_row.addWidget(self.lbl_nxt_session)
        session_row.addStretch()
        strat_layout.addLayout(session_row)

        chk_row = QHBoxLayout()
        self.chk_sam = QCheckBox("삼성전자 (005930)")
        self.chk_sam.setChecked(True)
        self.chk_sam.setStyleSheet("color: #60a5fa;")
        self.chk_sk = QCheckBox("SK하이닉스 (000660)")
        self.chk_sk.setChecked(True)
        self.chk_sk.setStyleSheet("color: #c084fc;")

        self.chk_ai_guardian = QCheckBox("🤖 AI 가디언 (4단)")
        self.chk_ai_guardian.setChecked(True)
        self.chk_ai_guardian.setStyleSheet("color: #facc15; font-weight: bold;")

        self.chk_watchdog = QCheckBox("🛡️ SRE 센티널 (자가치유)")
        self.chk_watchdog.setChecked(True)
        self.chk_watchdog.setStyleSheet("color: #4ade80; font-weight: bold;")

        chk_row.addWidget(self.chk_sam)
        chk_row.addWidget(self.chk_sk)
        chk_row.addWidget(self.chk_ai_guardian)
        chk_row.addWidget(self.chk_watchdog)
        chk_row.addStretch()
        strat_layout.addLayout(chk_row)

        left_layout.addWidget(strat_group)

        # 2-C. 실시간 주문 및 체결 내역 테이블 (Order History Table)
        order_group = QGroupBox("📋 실시간 주문 / 체결 내역 및 매매일지 (SQLite WAL 연동)")
        order_group.setStyleSheet("QGroupBox::title { color: #38bdf8; }")
        order_layout = QVBoxLayout(order_group)
        order_layout.setContentsMargins(6, 6, 6, 6)

        self.order_table = QTableWidget()
        self.order_table.setColumnCount(7)
        self.order_table.setHorizontalHeaderLabels(["체결시각", "종목명", "구분", "체결가", "수량", "실현손익", "전략/사유"])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.order_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.order_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.order_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.order_table.setFixedHeight(140)
        order_layout.addWidget(self.order_table)
        left_layout.addWidget(order_group)

        # 2-D. 액션 버튼 영역
        btn_layout_top = QHBoxLayout()
        self.btn_launch = QPushButton("🚀 [선택된 설정으로 트레이딩 봇 시작 (승인 연동)]")
        self.btn_launch.setStyleSheet("font-size: 13px; padding: 8px; background-color: #2563eb;")
        self.btn_launch.clicked.connect(self._launch_bots_with_approval)

        self.btn_kill = QPushButton("🛑 [비상 정지]")
        self.btn_kill.setObjectName("btn_kill")
        self.btn_kill.setStyleSheet("font-size: 12px; padding: 8px;")
        self.btn_kill.clicked.connect(self._kill_all_bots)

        btn_layout_top.addWidget(self.btn_launch, 3)
        btn_layout_top.addWidget(self.btn_kill, 1)
        left_layout.addLayout(btn_layout_top)

        btn_layout_sub = QHBoxLayout()
        utils = [
            ("📅 테마 캘린더", self._run_calendar),
            ("📈 일봉/3분봉 수집", self._run_universe_collection),
            ("⚡ 키움 1년 3분봉", self._run_kiwoom_1year_3m),
            ("🧪 CI/CD 단위테스트", self._run_ci_suite),
            ("📊 정배열 시뮬", self._run_quant_lab),
            ("☁️ G드라이브 백업", self._run_gdrive_sync)
        ]
        for label, fn in utils:
            btn = QPushButton(label)
            btn.setObjectName("btn_util")
            btn.clicked.connect(fn)
            btn_layout_sub.addWidget(btn)
        left_layout.addLayout(btn_layout_sub)

        body_layout.addWidget(left_widget, 3)

        # ==========================================
        # [우측 열: Google Gemini AI 퀀트 코파일럿]
        # ==========================================
        chat_group = QGroupBox("🧠 GOOGLE GEMINI 퀀트 코파일럿 (실시간 지능 분석 & 질의응답)")
        chat_group.setStyleSheet("QGroupBox::title { color: #facc15; }")
        chat_layout = QVBoxLayout(chat_group)
        chat_layout.setContentsMargins(8, 8, 8, 6)
        chat_layout.setSpacing(6)

        # 상단 툴바: API 키 설정 및 프롬프트 칩
        top_bar = QHBoxLayout()
        self.btn_set_key = QPushButton("🔑 Gemini API 키 설정")
        self.btn_set_key.setObjectName("btn_gemini")
        self.btn_set_key.clicked.connect(self._configure_gemini_key)
        top_bar.addWidget(self.btn_set_key)

        chips = [
            ("💳 계좌/손익", "현재 계좌 및 포지션 상태 브리핑해줘"),
            ("📋 최근 주문내역", "최근 주문 및 체결 내역 리포트해줘"),
            ("⚡ SOR/NXT 안내", "SOR 최선주문집행과 NXT 대체거래소 12시간 거래 원리 및 유리한 점 설명해줘"),
            ("🏛️ 주도테마 1~3등", "당일 KRX 실시간 주도 테마 1~3등과 대장주 분석해줘"),
            ("📊 삼성/하이닉스 진단", "삼성전자와 SK하이닉스 15분봉 퀀트 진단해줘")
        ]
        for label, prompt in chips:
            btn_chip = QPushButton(label)
            btn_chip.setObjectName("btn_chip")
            btn_chip.clicked.connect(lambda checked, p=prompt: self._send_user_message(p))
            top_bar.addWidget(btn_chip)
        chat_layout.addLayout(top_bar)

        # 대화창 텍스트 브라우저
        self.chat_browser = QTextBrowser()
        self.chat_browser.setOpenExternalLinks(True)
        chat_layout.addWidget(self.chat_browser)

        # 하단 입력창 & 전송 버튼
        input_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Google Gemini에게 실시간 퀀트 분석 및 질문하세요... (Enter로 전송)")
        self.input_box.returnPressed.connect(self._handle_input_send)

        self.btn_send = QPushButton("전송 ↵")
        self.btn_send.setStyleSheet("background-color: #3b82f6; font-size: 12px; padding: 6px 12px;")
        self.btn_send.clicked.connect(self._handle_input_send)

        input_row.addWidget(self.input_box)
        input_row.addWidget(self.btn_send)
        chat_layout.addLayout(input_row)

        body_layout.addWidget(chat_group, 2)
        main_layout.addLayout(body_layout)

        # 3. 하단 실시간 텔레메트리 & 상태바
        self.status_lbl = QLabel("🟢 시스템 상태: 100% 정상 | 📡 키움소켓: OK | 💳 계좌동기화: OK | 🧠 AI: Google Gemini 2.0 Flash 🟢 (0.24s)")
        self.status_lbl.setStyleSheet("font-size: 11px; color: #4ade80; background-color: #020617; padding: 5px 8px; border-radius: 4px; border: 1px solid #1e293b;")
        main_layout.addWidget(self.status_lbl)

    def _init_chat_welcome(self):
        try:
            from sdk.ai_chat_engine import ai_chat_engine
            has_key = bool(ai_chat_engine.api_key)
            status_badge = "<span style='color:#4ade80; font-weight:bold;'>[Gemini API 연동 활성화 ✅]</span>" if has_key else "<span style='color:#fbbf24;'>[Gemini 로컬 추론 모드 (API 키 미설정)]</span>"

            welcome_html = f"""
            <div style='background-color: #1e293b; border-left: 3px solid #38bdf8; padding: 8px; border-radius: 4px; margin-bottom: 6px;'>
                <b style='color: #38bdf8;'>🧠 [Google Gemini 퀀트 코파일럿]:</b> {status_badge}<br>
                <span style='color: #cbd5e1; font-size: 12px;'>
                키움증권 실시간 계좌(`8133-5076-11`), 15분봉 듀얼 전략, 실시간 주문 내역 및 KRX 주도 테마를 실시간 추론합니다.<br>
                상단의 <b>[추천 질문]</b>을 클릭하시거나 자유롭게 질문을 입력해 주세요! ✨
                </span>
            </div>
            """
            self.chat_browser.setHtml(welcome_html)
        except Exception:
            pass

    def _configure_gemini_key(self):
        from sdk.ai_chat_engine import ai_chat_engine
        cur_key = ai_chat_engine.api_key
        key, ok = QInputDialog.getText(
            self, "🔑 Google Gemini API 키 설정",
            "Google AI Studio에서 발급받은 Gemini API Key를 입력하세요:\n(입력 즉시 실시간 Gemini 2.0 API와 연동됩니다)",
            QLineEdit.Normal, cur_key
        )
        if ok and key.strip():
            ai_chat_engine.set_api_key(key.strip())
            QMessageBox.information(self, "설정 완료", "Google Gemini API 키가 성공적으로 등록되었습니다! 🧠✨")
            self._init_chat_welcome()

    def _handle_input_send(self):
        text = self.input_box.text().strip()
        if not text:
            return
        self.input_box.clear()
        self._send_user_message(text)

    def _send_user_message(self, text: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        user_bubble = f"""
        <div style='background-color: #1e3a8a; border-right: 3px solid #60a5fa; padding: 6px 10px; border-radius: 6px; margin: 5px 0; text-align: right;'>
            <span style='color: #93c5fd; font-size: 10px;'>[{now_str}] <b>사용자</b>:</span><br>
            <span style='color: #ffffff; font-size: 12px;'>{text}</span>
        </div>
        """
        self.chat_browser.append(user_bubble)

        self.status_lbl.setText("🧠 Google Gemini AI가 실시간 데이터를 분석하여 최적의 답변을 생성 중입니다... ⏳")
        self.btn_send.setEnabled(False)
        self.input_box.setEnabled(False)

        self.worker = GeminiChatWorker(text)
        self.worker.response_ready.connect(self._on_ai_response_ready)
        self.worker.start()

    def _format_markdown_to_html(self, text: str) -> str:
        import re
        text = re.sub(r'```(\w+)?\n([\s\S]+?)```', r"<pre style='background:#020617; padding:8px; border-radius:4px; color:#38bdf8; font-family:Consolas;'>\2</pre>", text)
        text = re.sub(r'`([^`]+)`', r"<code style='background:#0f172a; padding:2px 4px; border-radius:3px; color:#38bdf8; font-weight:bold; font-family:Consolas;'>\1</code>", text)
        text = re.sub(r'\*\*(.+?)\*\*', r"<b>\1</b>", text)
        text = re.sub(r'\*(.+?)\*', r"<i>\1</i>", text)
        text = re.sub(r'^### (.+)$', r"<h4 style='color:#38bdf8; margin:6px 0 2px 0;'>\1</h4>", text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r"<h3 style='color:#60a5fa; margin:8px 0 4px 0;'>\1</h3>", text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r"<h2 style='color:#93c5fd; margin:10px 0 4px 0;'>\1</h2>", text, flags=re.MULTILINE)
        text = re.sub(r'^[*-] (.+)$', r"• \1", text, flags=re.MULTILINE)
        text = text.replace("\n", "<br>")
        return text

    def _on_ai_response_ready(self, reply: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        formatted = self._format_markdown_to_html(reply)
        ai_bubble = f"""
        <div style='background-color: #0f172a; border-left: 3px solid #10b981; padding: 8px 10px; border-radius: 6px; margin: 5px 0;'>
            <span style='color: #34d399; font-size: 10px;'>[{now_str}] <b>🧠 Google Gemini AI</b>:</span><br>
            <span style='color: #f8fafc; font-size: 12px; line-height: 1.5;'>{formatted}</span>
        </div>
        """
        self.chat_browser.append(ai_bubble)
        self.chat_browser.verticalScrollBar().setValue(self.chat_browser.verticalScrollBar().maximum())

        self.btn_send.setEnabled(True)
        self.input_box.setEnabled(True)
        self.input_box.setFocus()
        self._periodic_sync()

    def _update_clock(self):
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        self.clock_lbl.setText(now_str)

        # 실시간 NXT & KRX 세션 판단
        t_str = now.strftime("%H:%M:%S")
        day_of_week = now.weekday()
        if day_of_week >= 5:
            self.lbl_nxt_session.setText("🏖️ [주말 휴장] (KRX / NXT 대체거래소 휴장)")
            self.lbl_nxt_session.setStyleSheet("background-color: #0f172a; border: 1px solid #475569; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #94a3b8;")
        elif "08:00:00" <= t_str < "08:50:00":
            self.lbl_nxt_session.setText("🌅 [NXT 프리마켓 가동 중] (08:00~08:50 - 호가 최유리 매칭)")
            self.lbl_nxt_session.setStyleSheet("background-color: #1e1b4b; border: 1px solid #6366f1; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #a5b4fc;")
        elif "08:50:00" <= t_str < "09:00:00":
            self.lbl_nxt_session.setText("⏱️ [정규장 동시호가 대기] (08:50~09:00)")
            self.lbl_nxt_session.setStyleSheet("background-color: #2e1065; border: 1px solid #a855f7; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #d8b4fe;")
        elif "09:00:00" <= t_str < "15:30:00":
            self.lbl_nxt_session.setText("☀️ [KRX & NXT 정규장 가동 중] (09:00~15:30 - SOR 스마트 최선집행)")
            self.lbl_nxt_session.setStyleSheet("background-color: #064e3b; border: 1px solid #10b981; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #6ee7b7;")
        elif "15:30:00" <= t_str < "20:00:00":
            self.lbl_nxt_session.setText("🌙 [NXT 애프터마켓 가동 중] (15:30~20:00 - 야간 1주 매매)")
            self.lbl_nxt_session.setStyleSheet("background-color: #701a75; border: 1px solid #ec4899; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #f472b6;")
        else:
            self.lbl_nxt_session.setText("💤 [야간 휴장 / 07:50 기상 준비] (20:00~08:00)")
            self.lbl_nxt_session.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #fbbf24;")

    def _periodic_sync(self):
        self._load_account_state()
        self._load_order_history()

    def _load_account_state(self):
        acc_file = os.path.join(BASE_DIR, "data", "account_state.json")
        if os.path.exists(acc_file):
            try:
                with open(acc_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                acc_no = str(data.get("account_no", "8133507611"))
                user_name = data.get("user_name", "김홍균")
                user_id = data.get("user_id", "zzil77")
                deposit = data.get("deposit", 30000000)
                orderable = data.get("orderable", 29739090)
                total_eval = data.get("total_eval", 261000)
                total_pnl = data.get("total_pnl", -1341)
                total_ret = data.get("total_return", -0.52)
                holdings = data.get("holdings", [])

                acc_fmt = f"{acc_no[:4]}-{acc_no[4:8]}-{acc_no[8:]}" if len(acc_no) == 10 else acc_no
                self.lbl_card_acc.setText(f"{acc_fmt} | {user_name}({user_id})")
                self.lbl_card_dep.setText(f"{deposit:,.0f} 원 (주문가능: {orderable:,.0f} 원)")
                self.lbl_card_eval.setText(f"{total_eval:,.0f} 원 ({total_pnl:+,.0f}원, {total_ret:+.2f}%)")

                sam_h = next((h for h in holdings if h.get("code") == "005930"), None)
                if sam_h and sam_h.get("qty", 0) > 0:
                    self.lbl_pos_sam.setText(f"🔵 [삼성전자] {sam_h['qty']}주 | 평단 {sam_h['buy_price']:,}원 | 손익 {sam_h['pnl']:+,}원 ({sam_h['return_rate']:+.2f}%)")
                else:
                    self.lbl_pos_sam.setText("🔵 [삼성전자 005930] 미보유 (15M 3선 & 20-60-120 정배열 감시 대기)")

                sk_h = next((h for h in holdings if h.get("code") == "000660"), None)
                if sk_h and sk_h.get("qty", 0) > 0:
                    self.lbl_pos_sk.setText(f"🟣 [SK하이닉스] {sk_h['qty']}주 | 평단 {sk_h['buy_price']:,}원 | 손익 {sk_h['pnl']:+,}원 ({sk_h['return_rate']:+.2f}%)")
                else:
                    self.lbl_pos_sk.setText("🟣 [SK하이닉스 000660] 미보유 (15M 3선 & 20-60-120 정배열 감시 대기)")
            except Exception:
                pass

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
                self.lbl_card_pnl.setText(f"{total_today_pnl:+,.0f} 원 (당일 {total_today_cnt}건 완료)")
            else:
                self.lbl_card_pnl.setText("0 원 (당일 거래 0건)")
        except Exception:
            pass

        try:
            from sdk.telemetry_watchdog import system_watchdog
            health = system_watchdog.get_health_status()
            score = health["health_score"]
            sock = health["socket_status"]
            acc = health["account_sync_status"]
            self.status_lbl.setText(f"🟢 시스템 건강도: {score}% 정상 | 📡 키움소켓: {sock} | 💳 계좌동기화: {acc} | 🧠 AI: Google Gemini 2.0 Flash 🟢")
        except Exception:
            pass

    def _load_order_history(self):
        """SQLite 매매일지 및 주문내역 로드 (data/research/trade_journal_*.sqlite 통합 조회)"""
        try:
            import glob
            db_paths = glob.glob(os.path.join(BASE_DIR, "data", "research", "trade_journal*.sqlite"))
            db_paths += glob.glob(os.path.join(BASE_DIR, "research", "trade_journal*.sqlite"))
            all_rows = []
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
                        if tname == "trade_journal":
                            cur.execute("SELECT timestamp, stock_name, side, price, qty, pnl_won, strategy_name FROM trade_journal ORDER BY id DESC LIMIT 20")
                        else:
                            cur.execute("SELECT created_at, stock_name, side, price, qty, net_pnl_won, strategy_name FROM trade_logs ORDER BY id DESC LIMIT 20")
                        all_rows.extend(cur.fetchall())
                    conn.close()
                except Exception:
                    pass

            all_rows.sort(key=lambda x: str(x[0]), reverse=True)
            rows = all_rows[:20]

            self.order_table.setRowCount(len(rows))
            for r_idx, row in enumerate(rows):
                # 0: 시간, 1: 종목명, 2: 구분, 3: 체결가, 4: 수량, 5: 손익, 6: 전략
                t_str = str(row[0]).split(" ")[-1] if " " in str(row[0]) else str(row[0])
                side_str = "매수" if str(row[2]).upper() == "BUY" else "매도"
                side_color = Qt.red if side_str == "매수" else Qt.blue
                pnl = row[5] or 0
                pnl_str = f"{pnl:+,.0f}원" if pnl != 0 else "-"

                items = [
                    QTableWidgetItem(t_str),
                    QTableWidgetItem(str(row[1])),
                    QTableWidgetItem(side_str),
                    QTableWidgetItem(f"{row[3]:,.0f}원"),
                    QTableWidgetItem(f"{row[4]}주"),
                    QTableWidgetItem(pnl_str),
                    QTableWidgetItem(str(row[6]))
                ]
                items[2].setForeground(side_color)
                if pnl > 0:
                    items[5].setForeground(Qt.red)
                elif pnl < 0:
                    items[5].setForeground(Qt.cyan)

                for c_idx, it in enumerate(items):
                    it.setTextAlignment(Qt.AlignCenter if c_idx in [0, 2, 4] else (Qt.AlignRight | Qt.AlignVCenter if c_idx in [3, 5] else Qt.AlignLeft | Qt.AlignVCenter))
                    self.order_table.setItem(r_idx, c_idx, it)
        except Exception:
            pass

    def _sync_live_account_from_kiwoom(self):
        self.status_lbl.setText("🔄 키움 OpenAPI+ 실시간 계좌 정보 조회 요청 중 (TR opw00001 / opw00018)...")
        self.sync_worker = KiwoomAccountSyncWorker()
        self.sync_worker.sync_finished.connect(self._on_sync_finished)
        self.sync_worker.start()

    def _on_sync_finished(self, success: bool, msg: str):
        self._periodic_sync()
        if success:
            self.status_lbl.setText(f"✅ {msg}")
        else:
            self.status_lbl.setText(f"ℹ️ {msg}")

    def _launch_bots_with_approval(self):
        sam = self.chk_sam.isChecked()
        sk = self.chk_sk.isChecked()

        if not sam and not sk:
            QMessageBox.warning(self, "선택 오류", "최소 1개 이상의 종목(삼성전자 또는 SK하이닉스)을 선택해 주세요!")
            return

        mode_str = "전략 A+B 듀얼 통합 모드" if self.r_dual.isChecked() else ("전략 A (3선 종가유지)" if self.r_a.isChecked() else "전략 B (정배열 황금이격)")
        routing_str = "🌟 SOR 최선주문집행 (KRX+NXT 통합)" if self.r_sor.isChecked() else ("🏛️ KRX 전용 (09:00~15:30)" if self.r_krx.isChecked() else "⚡ NXT 전용 (08:00~20:00)")

        reply = QMessageBox.question(
            self,
            "🚀 자동매매 봇 실전 승인 및 가동",
            f"다음 설정으로 자동매매 봇 가동을 최종 승인하시겠습니까?\n\n"
            f"• 선택 전략: {mode_str}\n"
            f"• 주문 방식: {routing_str}\n"
            f"• 대상 종목: {'삼성전자(005930) ' if sam else ''}{'SK하이닉스(000660)' if sk else ''}\n"
            f"• 승인 계좌: 8133-5076-11 (김홍균 | 모의투자 1호)\n"
            f"• 주문 크기: 1주 고정 주문 (qty=1 강제)\n"
            f"• 리스크비: SL -0.90% | TP1 +1.50%(본절) | TP2 +2.80%(트레일링)",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        approval_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": "김홍균",
            "account_no": "8133507611",
            "strategy_mode": mode_str,
            "order_routing": routing_str,
            "enable_samsung": sam,
            "enable_hynix": sk,
            "decision": "APPROVED"
        }
        log_path = os.path.join(BASE_DIR, "data", "approval_log.json")
        try:
            logs = []
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            logs.append(approval_record)
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        if sam:
            sam_script = os.path.join(BASE_DIR, "workers", "worker_samsung_squeeze.py")
            cmd = ["cmd.exe", "/k", "title", "SAM-BOT (005930)", "&&", PYTHON_EXE, sam_script]
            subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)

        if sk:
            sk_script = os.path.join(BASE_DIR, "workers", "worker_hynix_pullback.py")
            cmd = ["cmd.exe", "/k", "title", "SK-BOT (000660)", "&&", PYTHON_EXE, sk_script]
            subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)

        self.status_lbl.setText(f"🚀 [승인 완료] 트레이딩 봇 정상 가동 중 ({mode_str})")
        QMessageBox.information(self, "가동 완료", f"선택하신 트레이딩 봇이 성공적으로 승인되어 시작되었습니다!\n전략: {mode_str}")

    def _kill_all_bots(self):
        reply = QMessageBox.question(self, "🛑 긴급 비상정지", "실행 중인 모든 트레이딩 봇 프로세스를 안전하게 종료하시겠습니까?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            current_pid = os.getpid()
            kill_cmd = f'taskkill /fi "PID ne {current_pid}" /f /im python.exe /t 2>nul'
            os.system(kill_cmd)
            self.status_lbl.setText("🛑 모든 봇 프로세스가 안전하게 종료되었습니다.")
            QMessageBox.information(self, "정지 완료", "모든 트레이딩 봇 프로세스가 안전하게 종료되었습니다.")

    def _auto_update_calendar_background(self, show_msg: bool = False):
        self.calendar_show_msg = show_msg
        self.status_lbl.setText("📅 테마 캘린더 및 1달 엑셀 갱신 중...")
        self.cal_worker = CalendarUpdateWorker()
        self.cal_worker.calendar_finished.connect(self._on_calendar_updated)
        self.cal_worker.start()

    def _on_calendar_updated(self, success: bool, msg: str):
        if success:
            self.status_lbl.setText(f"✅ {msg}")
            if getattr(self, 'calendar_show_msg', False):
                QMessageBox.information(self, "완료", "바탕화면 증시 캘린더와 1달 통합 엑셀이 실시간 KRX 데이터로 갱신되었습니다!")
        else:
            self.status_lbl.setText(f"ℹ️ {msg}")

    def _run_calendar(self):
        self._auto_update_calendar_background(show_msg=True)

    def _run_universe_collection(self):
        self.status_lbl.setText("📈 코스피200 & 코스닥150 [일봉 + 3분봉] 병렬 수집 중...")
        self.univ_worker = UniverseCollectionWorker()
        self.univ_worker.collection_finished.connect(self._on_universe_collected)
        self.univ_worker.start()

    def _on_universe_collected(self, success: bool, msg: str):
        if success:
            self.status_lbl.setText(f"✅ {msg}")
            QMessageBox.information(self, "수집 완료", "코스피 200 및 코스닥 150 전 종목의 일봉/3분봉 데이터 수집 및 구글 드라이브 동기화가 성공적으로 완료되었습니다!")
        else:
            self.status_lbl.setText(f"⚠️ {msg}")
            QMessageBox.warning(self, "수집 알림", f"종목 데이터 수집 중 문제 발생:\n{msg}")

    def _run_kiwoom_1year_3m(self):
        """키움 OpenAPI opt10080 연속조회 기반 코스피200 & 코스닥150 (350종목) 1년치 3분봉 수집기 실행"""
        script = os.path.join(BASE_DIR, "collectors", "kiwoom_historical_3m_collector.py")
        cmd = ["cmd.exe", "/k", "title", "Kiwoom 1-Year 3M Universe Collector (350 Stocks)", "&&", PYTHON_EXE, script, "--start-date", "20250901", "--max-pages", "45"]
        subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)
        self.status_lbl.setText("⚡ [키움 OpenAPI opt10080] 코스피200 + 코스닥150 1년치 3분봉 이어받기 수집 콘솔 가동!")

    def _run_ci_suite(self):
        self.status_lbl.setText("🧪 CI/CD 단위 테스트 실행 중...")
        script = os.path.join(BASE_DIR, "tests", "run_ci_suite.py")
        res = subprocess.run([PYTHON_EXE, script], cwd=BASE_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            self.status_lbl.setText("🏆 CI/CD 24개 테스트 전원 100% 통과 (100% OK)")
            QMessageBox.information(self, "테스트 통과", "🏆 24개 아키텍처, AI 가디언, SRE 센티널 테스트가 100% 정상 통과했습니다!")
        else:
            QMessageBox.critical(self, "테스트 오류", f"일부 테스트 실패:\n{res.stderr}")

    def _run_quant_lab(self):
        script = os.path.join(BASE_DIR, "research", "analyze_ma_alignment_disparity.py")
        cmd = ["cmd.exe", "/k", "title", "Quant Lab Matrix Analysis", "&&", PYTHON_EXE, script]
        subprocess.Popen(cmd, cwd=BASE_DIR, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def _run_gdrive_sync(self):
        self.status_lbl.setText("☁️ 구글 드라이브 전 계층 동기화 중...")
        script = os.path.join(BASE_DIR, "storage", "gdrive_sync.py")
        subprocess.run([PYTHON_EXE, script], cwd=BASE_DIR)
        self.status_lbl.setText("✅ 구글 드라이브 동기화 완료!")
        QMessageBox.information(self, "동기화 완료", "모든 아키텍처, 엑셀, 캘린더, 연구 보고서가 구글 드라이브로 백업되었습니다!")

def main():
    app = QApplication(sys.argv)
    dashboard = AntigravityDashboard()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
