"""
Kiwoom OpenAPI+ Active-X (PyQt5) Wrapper for SK Hynix (000660)
Provides Safe Token-Bucket Rate Limiting (3.5 TPS), Event-driven TR execution,
Historical Minute-Bar Paging Collector (opt10080), Real-time Feed Binding,
Account Deposit (opw00001), Balance (opw00018), and Stock Info (opt10001) queries.
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import pandas as pd

# Windows UTF-8 stdout configuration
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer

from config.settings import config

class KiwoomAPI:
    def __init__(self, on_tick_callback: Optional[Callable] = None, on_chejan_callback: Optional[Callable] = None):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.on_tick_callback = on_tick_callback
        self.on_chejan_callback = on_chejan_callback
        
        self.account_list: List[str] = []
        self.user_id: str = ""
        self.user_name: str = ""
        self.is_connected: bool = False
        
        # Token-Bucket Rate Limiter (Max 3.5 TR/sec)
        self.last_tr_time: float = 0.0
        self.min_tr_interval: float = 1.0 / config.MAX_TR_PER_SECOND
        
        # Event Loop 동기화 객체
        self.login_loop: Optional[QEventLoop] = None
        self.tr_loop: Optional[QEventLoop] = None
        self.tr_received_data: Any = None
        self.tr_prev_next: str = "0"
        
        # 이벤트 시그널 연결
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.ocx.OnReceiveRealData.connect(self._on_receive_real_data)
        self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        self.ocx.OnReceiveMsg.connect(self._on_receive_msg)

    def login(self) -> bool:
        """키움 Open API+ 로그인 창 호출 및 동기 대기"""
        print(">> [KiwoomAPI] 로그인 요청 중...")
        self.ocx.CommConnect()
        self.login_loop = QEventLoop()
        self.login_loop.exec_()
        return self.is_connected

    def _on_event_connect(self, err_code: int):
        if err_code == 0:
            self.is_connected = True
            self.user_id = self.ocx.GetLoginInfo("USER_ID")
            self.user_name = self.ocx.GetLoginInfo("USER_NAME")
            self.account_list = [acc for acc in self.ocx.GetLoginInfo("ACCNO").split(';') if acc]
            
            server_gubun = self.ocx.GetLoginInfo("GetServerGubun")
            server_type = "모의투자 서버" if server_gubun == "1" else "실전투자 서버"
            
            print(f">> [KiwoomAPI] 로그인 성공! 사용자: {self.user_name} ({self.user_id}) | {server_type}")
            print(f">> [KiwoomAPI] 보유 계좌: {self.account_list}")
        else:
            self.is_connected = False
            print(f">> [KiwoomAPI] 로그인 실패 (오류 코드: {err_code})")
            
        if self.login_loop:
            self.login_loop.exit()

    def _wait_rate_limit(self):
        """TR 초당 5회 제한 방어를 위한 Token Bucket 대기 (3.5 TPS)"""
        elapsed = time.time() - self.last_tr_time
        if elapsed < self.min_tr_interval:
            time.sleep(self.min_tr_interval - elapsed)
        self.last_tr_time = time.time()

    def get_deposit(self, account_no: str) -> Dict[str, int]:
        """[opw00001] 예수금 및 주문가능금액 조회"""
        self._wait_rate_limit()
        self.ocx.SetInputValue("계좌번호", account_no)
        self.ocx.SetInputValue("비밀번호", "")
        self.ocx.SetInputValue("비밀번호입력매체구분", "00")
        self.ocx.SetInputValue("조회구분", "2")
        
        self.tr_received_data = {}
        ret = self.ocx.CommRqData("예수금상세현황", "opw00001", 0, config.SCREEN_NO_TR)
        if ret == 0:
            self.tr_loop = QEventLoop()
            self.tr_loop.exec_()
        return self.tr_received_data if isinstance(self.tr_received_data, dict) else {}

    def get_account_balance(self, account_no: str) -> Dict[str, Any]:
        """[opw00018] 계좌평가잔고내역 조회"""
        self._wait_rate_limit()
        self.ocx.SetInputValue("계좌번호", account_no)
        self.ocx.SetInputValue("비밀번호", "")
        self.ocx.SetInputValue("비밀번호입력매체구분", "00")
        self.ocx.SetInputValue("조회구분", "1")
        
        self.tr_received_data = {}
        ret = self.ocx.CommRqData("계좌평가잔고", "opw00018", 0, config.SCREEN_NO_TR)
        if ret == 0:
            self.tr_loop = QEventLoop()
            self.tr_loop.exec_()
        return self.tr_received_data if isinstance(self.tr_received_data, dict) else {}

    def get_stock_info(self, code: str) -> Dict[str, Any]:
        """[opt10001] 주식기본정보 (현재가, 등락율 등) 조회"""
        self._wait_rate_limit()
        self.ocx.SetInputValue("종목코드", code)
        self.tr_received_data = {}
        ret = self.ocx.CommRqData("주식기본정보", "opt10001", 0, config.SCREEN_NO_TR)
        if ret == 0:
            self.tr_loop = QEventLoop()
            self.tr_loop.exec_()
        return self.tr_received_data if isinstance(self.tr_received_data, dict) else {}

    def get_minute_bars(self, code: str, tick_range: int, target_start_date: str = "20250801") -> pd.DataFrame:
        """opt10080(주식분봉조회요청) 연속 조회를 통해 분봉 데이터 수집"""
        all_bars: List[Dict] = []
        prev_next = 0
        page = 1
        
        print(f"\n>> [KiwoomAPI] {code} {tick_range}분봉 데이터 수집 시작 (목표: {target_start_date} ~ 현재)...")
        
        while True:
            self._wait_rate_limit()
            self.ocx.SetInputValue("종목코드", code)
            self.ocx.SetInputValue("틱범위", str(tick_range))
            self.ocx.SetInputValue("수정주가구분", "1")
            
            self.tr_received_data = []
            ret = self.ocx.CommRqData(f"주식분봉_{tick_range}m", "opt10080", prev_next, config.SCREEN_NO_TR)
            if ret != 0:
                break
                
            self.tr_loop = QEventLoop()
            self.tr_loop.exec_()
            
            if not self.tr_received_data or not isinstance(self.tr_received_data, list):
                break
                
            all_bars.extend(self.tr_received_data)
            earliest_dt = self.tr_received_data[-1]['timestamp']
            earliest_str = earliest_dt.strftime('%Y%m%d')
            
            print(f"   • [{tick_range}분봉 Page {page:>2}] {len(self.tr_received_data):>3}개 수신 | 누적: {len(all_bars):,d}개")
            
            if earliest_str <= target_start_date or self.tr_prev_next != "2":
                break
                
            prev_next = 2
            page += 1
            
        if not all_bars:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            
        df = pd.DataFrame(all_bars)
        df.drop_duplicates(subset=['timestamp'], inplace=True)
        df.sort_values('timestamp', inplace=True)
        df.set_index('timestamp', inplace=True)
        
        target_dt = pd.to_datetime(target_start_date)
        df = df[df.index >= target_dt]
        return df

    def set_real_reg(self, screen_no: str, code_list: str, fid_list: str, opt_type: str = "0"):
        """실시간 시세 데이터 등록 (SetRealReg)"""
        self.ocx.SetRealReg(screen_no, code_list, fid_list, opt_type)
        print(f">> [KiwoomAPI] 실시간 시세 등록 완료: 종목({code_list}), 화면({screen_no})")

    def send_order(
        self,
        rq_name: str,
        screen_no: str,
        acc_no: str,
        order_type: int,
        code: str,
        qty: int,
        price: int,
        hoga_type: str = "03",
        org_order_no: str = ""
    ) -> int:
        """키움 Open API+ 주문 발주 (SendOrder)"""
        ret = self.ocx.SendOrder(rq_name, screen_no, acc_no, order_type, code, qty, price, hoga_type, org_order_no)
        if ret == 0:
            order_name = "매수" if order_type == 1 else "매도"
            print(f">> [KiwoomAPI] {order_name} 주문 전송 성공: {code} {qty}주 @ {price if hoga_type=='00' else '시장가'}")
        else:
            print(f">> [KiwoomAPI] 주문 실패 (에러코드: {ret})")
        return ret

    def _on_receive_real_data(self, code: str, real_type: str, real_data: str):
        if real_type == "주식체결":
            try:
                curr_price = abs(int(self.ocx.GetCommRealData(code, 10)))
                volume = abs(int(self.ocx.GetCommRealData(code, 15)))
                intensity = float(self.ocx.GetCommRealData(code, 228))
                time_str = self.ocx.GetCommRealData(code, 20)
                
                if self.on_tick_callback:
                    self.on_tick_callback(code, curr_price, volume, intensity, time_str)
            except Exception as e:
                pass

    def _on_receive_chejan_data(self, gubun: str, item_cnt: int, fid_list: str):
        try:
            order_no = self.ocx.GetChejanData(9203).strip()
            code = self.ocx.GetChejanData(9001).strip().replace("A", "")
            order_status = self.ocx.GetChejanData(913).strip()
            chegual_qty = int(self.ocx.GetChejanData(911).strip() or 0)
            chegual_price = int(self.ocx.GetChejanData(910).strip() or 0)
            
            if self.on_chejan_callback:
                self.on_chejan_callback(gubun, order_no, code, order_status, chegual_qty, chegual_price)
        except Exception as e:
            pass

    def _on_receive_tr_data(self, scr_no: str, rq_name: str, tr_code: str, record_name: str, prev_next: str):
        self.tr_prev_next = prev_next
        
        if tr_code == "opw00001":
            deposit = int(self.ocx.GetCommData(tr_code, rq_name, 0, "예수금").strip() or 0)
            d2_deposit = int(self.ocx.GetCommData(tr_code, rq_name, 0, "d+2추정예수금").strip() or 0)
            withdrawable = int(self.ocx.GetCommData(tr_code, rq_name, 0, "출금가능금액").strip() or 0)
            orderable = int(self.ocx.GetCommData(tr_code, rq_name, 0, "주문가능금액").strip() or 0)
            self.tr_received_data = {
                'deposit': deposit,
                'd2_deposit': d2_deposit,
                'withdrawable': withdrawable,
                'orderable': orderable
            }
            
        elif tr_code == "opw00018":
            total_buy = int(self.ocx.GetCommData(tr_code, rq_name, 0, "총매입금액").strip() or 0)
            total_eval = int(self.ocx.GetCommData(tr_code, rq_name, 0, "총평가금액").strip() or 0)
            total_pnl = int(self.ocx.GetCommData(tr_code, rq_name, 0, "총평가손익금액").strip() or 0)
            total_yield = float(self.ocx.GetCommData(tr_code, rq_name, 0, "총수익률(%)").strip() or 0.0)
            
            items = []
            count = self.ocx.GetRepeatCnt(tr_code, rq_name)
            for i in range(count):
                name = self.ocx.GetCommData(tr_code, rq_name, i, "종목명").strip()
                code = self.ocx.GetCommData(tr_code, rq_name, i, "종목번호").strip().replace("A", "")
                qty = int(self.ocx.GetCommData(tr_code, rq_name, i, "보유수량").strip() or 0)
                eval_pnl = int(self.ocx.GetCommData(tr_code, rq_name, i, "평가손익").strip() or 0)
                item_yield = float(self.ocx.GetCommData(tr_code, rq_name, i, "수익률(%)").strip() or 0.0)
                items.append({
                    'name': name,
                    'code': code,
                    'qty': qty,
                    'eval_pnl': eval_pnl,
                    'yield': item_yield
                })
                
            self.tr_received_data = {
                'total_buy': total_buy,
                'total_eval': total_eval,
                'total_pnl': total_pnl,
                'total_yield': total_yield,
                'items': items
            }
            
        elif tr_code == "opt10001":
            name = self.ocx.GetCommData(tr_code, rq_name, 0, "종목명").strip()
            price = abs(int(self.ocx.GetCommData(tr_code, rq_name, 0, "현재가").strip() or 0))
            diff = self.ocx.GetCommData(tr_code, rq_name, 0, "전일대비").strip()
            rate = float(self.ocx.GetCommData(tr_code, rq_name, 0, "등락율").strip() or 0.0)
            volume = int(self.ocx.GetCommData(tr_code, rq_name, 0, "거래량").strip() or 0)
            self.tr_received_data = {
                'name': name,
                'price': price,
                'diff': diff,
                'rate': rate,
                'volume': volume
            }
            
        elif tr_code == "opt10080":
            count = self.ocx.GetRepeatCnt(tr_code, rq_name)
            bars = []
            for i in range(count):
                timestr = self.ocx.GetCommData(tr_code, rq_name, i, "체결시간").strip()
                close_p = abs(int(self.ocx.GetCommData(tr_code, rq_name, i, "현재가").strip() or 0))
                open_p = abs(int(self.ocx.GetCommData(tr_code, rq_name, i, "시가").strip() or 0))
                high_p = abs(int(self.ocx.GetCommData(tr_code, rq_name, i, "고가").strip() or 0))
                low_p = abs(int(self.ocx.GetCommData(tr_code, rq_name, i, "저가").strip() or 0))
                vol = abs(int(self.ocx.GetCommData(tr_code, rq_name, i, "거래량").strip() or 0))
                
                try:
                    dt = datetime.strptime(timestr, "%Y%m%d%H%M%S")
                    bars.append({
                        'timestamp': dt,
                        'open': float(open_p),
                        'high': float(high_p),
                        'low': float(low_p),
                        'close': float(close_p),
                        'volume': int(vol)
                    })
                except Exception:
                    pass
            self.tr_received_data = bars
            
        if self.tr_loop:
            self.tr_loop.exit()

    def _on_receive_msg(self, scr_no: str, rq_name: str, tr_code: str, msg: str):
        pass
