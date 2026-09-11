"""
========================================================================================
🔌 [BROKER ADAPTER: KIWOOM OPENAPI+ 32BIT COM IMPLEMENTATION]
Isolates Windows Active-X COM calls, Token-Bucket Rate Limiting (3.5 TPS), and QEventLoop.
Supports opw00001 (Deposit), opw00018 (Account Balance & Holdings), and Real-time Ticks.
========================================================================================
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

from sdk.broker_adapter import BrokerAdapter
from config.settings import config

class KiwoomAdapter(BrokerAdapter):
    def __init__(self, on_tick_callback: Optional[Callable] = None, on_chejan_callback: Optional[Callable] = None):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.event_loop = QEventLoop()
        
        self.on_tick_callback = on_tick_callback
        self.on_chejan_callback = on_chejan_callback
        
        self.last_tr_time = 0.0
        self.min_tr_interval = 0.28  # 3.5 TPS Token-Bucket Rate Limiter
        
        self.temp_tr_data = {}
        self.account_list = []
        self.user_name = ""
        self.user_id = ""
        self.server_name = "모의투자"
        
        self._register_event_handlers()

    def _register_event_handlers(self):
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.ocx.OnReceiveRealData.connect(self._on_receive_real_data)
        self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        self.ocx.OnReceiveMsg.connect(self._on_receive_msg)

    def _wait_for_tr_rate_limit(self):
        elapsed = time.time() - self.last_tr_time
        if elapsed < self.min_tr_interval:
            time.sleep(self.min_tr_interval - elapsed)
        self.last_tr_time = time.time()

    def login(self) -> bool:
        if self.get_connect_state() == 1:
            print(">> [KiwoomAdapter] 🟢 이미 키움 OpenAPI+에 연결되어 있습니다.")
            self._load_login_info()
            return True

        print(">> [KiwoomAdapter] 🔑 키움증권 OpenAPI+ 로그인 요청 중...")
        self.ocx.dynamicCall("CommConnect()")
        self.event_loop.exec_()
        return self.get_connect_state() == 1

    def _load_login_info(self):
        try:
            self.user_name = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_NAME").strip()
            self.user_id = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_ID").strip()
            server_gubun = self.ocx.dynamicCall("GetLoginInfo(QString)", "GetServerGubun").strip()
            self.server_name = "모의투자" if server_gubun == "1" else "실서버"
            acc_str = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO").strip()
            self.account_list = [a.strip() for a in acc_str.split(';') if a.strip()]
        except Exception:
            pass

    def get_connect_state(self) -> int:
        try:
            return int(self.ocx.dynamicCall("GetConnectState()"))
        except Exception:
            return 0

    def _on_event_connect(self, err_code: int):
        if err_code == 0:
            self.user_name = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_NAME").strip()
            self.user_id = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_ID").strip()
            server_gubun = self.ocx.dynamicCall("GetLoginInfo(QString)", "GetServerGubun").strip()
            self.server_name = "모의투자" if server_gubun == "1" else "실서버"
            acc_str = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO").strip()
            self.account_list = [a.strip() for a in acc_str.split(';') if a.strip()]
            
            print(f">> [KiwoomAdapter] ✅ 로그인 성공! 사용자: {self.user_name}({self.user_id}) | {self.server_name} | 계좌: {self.account_list}")
            
            # 로그인 성공 즉시 계좌 상세 상태 조회 및 JSON 저장
            active_acc = self.account_list[0] if self.account_list else config.ACCOUNT_NO
            self.sync_account_state_to_file(active_acc)
        else:
            print(f">> [KiwoomAdapter] ❌ 로그인 실패 (에러코드: {err_code})")
        self.event_loop.exit()

    def get_deposit(self, account_no: str) -> Dict[str, Any]:
        self._wait_for_tr_rate_limit()
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account_no)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00001_req", "opw00001", 0, "3000")
        self.event_loop.exec_()
        return self.temp_tr_data.get("opw00001", {"deposit": 50_000_000, "orderable": 49_250_000})

    def get_account_evaluation(self, account_no: str) -> Dict[str, Any]:
        """opw00018: 계좌평가잔고내역요청"""
        self._wait_for_tr_rate_limit()
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account_no)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00018_req", "opw00018", 0, "3001")
        self.event_loop.exec_()
        return self.temp_tr_data.get("opw00018", {
            "total_buy": 0, "total_eval": 50_000_000, "total_pnl": 0, "total_return": 0.0, "holdings": []
        })

    def sync_account_state_to_file(self, account_no: str):
        """실시간 계좌 정보를 조회하여 data/account_state.json 에 저장 및 콘솔 브리핑"""
        dep = self.get_deposit(account_no)
        eval_data = self.get_account_evaluation(account_no)

        state = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "account_no": account_no,
            "user_name": self.user_name or config.USER_NAME,
            "user_id": self.user_id or config.USER_ID,
            "server_name": self.server_name,
            "deposit": dep.get("deposit", 50_000_000),
            "orderable": dep.get("orderable", 49_250_000),
            "total_buy": eval_data.get("total_buy", 0),
            "total_eval": eval_data.get("total_eval", dep.get("deposit", 50_000_000)),
            "total_pnl": eval_data.get("total_pnl", 0),
            "total_return": eval_data.get("total_return", 0.0),
            "holdings": eval_data.get("holdings", [])
        }

        os.makedirs(os.path.join(config.BASE_DIR, "data"), exist_ok=True)
        file_path = os.path.join(config.BASE_DIR, "data", "account_state.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        print(f">> [KiwoomAdapter] 💳 계좌 상세 현황 조회 완료 [{account_no} / {state['user_name']}({state['user_id']}) - {state['server_name']}]:")
        print(f"   • 예수금: {state['deposit']:,} 원  |  주문가능금액: {state['orderable']:,} 원")
        print(f"   • 총평가: {state['total_eval']:,} 원  |  평가손익: {state['total_pnl']:+,} 원 ({state['total_return']:+.2f}%)")
        if state['holdings']:
            print(f"   • 보유종목: {len(state['holdings'])}개")
            for h in state['holdings']:
                print(f"     - {h['name']}({h['code']}): {h['qty']}주 | 평단 {h['buy_price']:,}원 | 손익 {h['pnl']:+,}원 ({h['return_rate']:+.2f}%)")
        else:
            print("   • 보유종목: 현재 미보유 (현금 100% 대기 중)")

    def get_stock_info(self, code: str) -> Dict[str, Any]:
        self._wait_for_tr_rate_limit()
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10001_req", "opt10001", 0, "3000")
        self.event_loop.exec_()
        return self.temp_tr_data.get("opt10001", {"price": 0.0, "rate": 0.0, "volume": 0})

    def _on_receive_msg(self, scr_no: str, rq_name: str, tr_code: str, msg: str):
        print(f">> [KiwoomAdapter] 📩 서버 메시지 [화면:{scr_no}, RQ:{rq_name}, TR:{tr_code}]: {msg}")

    def send_order(self, rq_name: str, screen_no: str, acc_no: str, order_type: int, code: str, qty: int, price: int, hoga_type: str) -> int:
        self._wait_for_tr_rate_limit()
        int_price = int(round(price)) if price else 0
        ret = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [rq_name, screen_no, acc_no, order_type, code, qty, int_price, hoga_type, ""]
        )
        side_str = "매수" if order_type == 1 else "매도"
        if ret == 0:
            print(f">> [KiwoomAdapter] ✅ {side_str} 주문 접수 성공: {code} {qty}주 @ {int_price:,}원 (호가: {hoga_type})")
        else:
            err_desc = {
                -10: "실패", -20: "통신오류", -106: "계좌비밀번호 미입력",
                -200: "시세조회 과부하", -201: "주문 파라미터 / 호가단위 오류",
                -300: "주문 입력값 오류", -301: "계좌비밀번호 없음",
                -307: "주문조건과 호가구분 불일치", -308: "원주문번호 없음",
                -309: "계좌번호 없음", -311: "종목코드 오류"
            }.get(ret, f"알 수 없는 오류 ({ret})")
            print(f">> [KiwoomAdapter] ❌ {side_str} 주문 전송 실패! [에러코드 {ret}: {err_desc}]")
        return ret

    def subscribe_realtime(self, screen_no: str, code: str, fids: str):
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, code, fids, "0")
        print(f">> [KiwoomAdapter] 📡 실시간 시세 등록: 종목({code}), 화면({screen_no})")

    def _on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next):
        if tr_code == "opw00001":
            deposit_str = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "예수금").strip()
            orderable_str = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "주문가능금액").strip()
            self.temp_tr_data["opw00001"] = {
                "deposit": int(deposit_str) if deposit_str else 0,
                "orderable": int(orderable_str) if orderable_str else 0
            }
        elif tr_code == "opw00018":
            total_buy = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "총매입금액").strip()
            total_eval = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "총평가금액").strip()
            total_pnl = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "총평가손익금액").strip()
            total_ret = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "총수익률(%)").strip()
            
            rows = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
            holdings = []
            for i in range(rows):
                code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "종목번호").strip().replace("A", "")
                name = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "종목명").strip()
                qty = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "보유수량").strip()
                buy_p = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "매입가").strip()
                cur_p = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "현재가").strip()
                pnl = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "평가손익").strip()
                ret_rate = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "수익률(%)").strip()
                if code and int(qty or 0) > 0:
                    holdings.append({
                        "code": code,
                        "name": name,
                        "qty": int(qty or 0),
                        "buy_price": int(buy_p or 0),
                        "current_price": int(cur_p or 0),
                        "pnl": int(pnl or 0),
                        "return_rate": float(ret_rate or 0.0)
                    })

            self.temp_tr_data["opw00018"] = {
                "total_buy": int(total_buy) if total_buy else 0,
                "total_eval": int(total_eval) if total_eval else 0,
                "total_pnl": int(total_pnl) if total_pnl else 0,
                "total_return": float(total_ret) if total_ret else 0.0,
                "holdings": holdings
            }
        elif tr_code == "opt10001":
            price_str = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "현재가").strip()
            rate_str = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "등락율").strip()
            volume_str = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "거래량").strip()
            self.temp_tr_data["opt10001"] = {
                "price": abs(float(price_str)) if price_str else 0.0,
                "rate": float(rate_str) if rate_str else 0.0,
                "volume": int(volume_str) if volume_str else 0
            }
        self.event_loop.exit()

    def _on_receive_real_data(self, code: str, real_type: str, real_data: str):
        if real_type in ["주식체결", "주식시세"]:
            price_str = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()
            vol_str = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, 15).strip()
            intensity_str = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, 228).strip()
            timestr = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, 20).strip()

            price = abs(float(price_str)) if price_str else 0.0
            volume = abs(int(vol_str)) if vol_str else 0
            intensity = abs(float(intensity_str)) if intensity_str else 100.0

            if self.on_tick_callback:
                self.on_tick_callback(code, price, volume, intensity, timestr)

    def _on_receive_chejan_data(self, gubun: str, item_cnt: int, fid_list: str):
        order_no = self.ocx.dynamicCall("GetChejanData(int)", 9203).strip()
        code = self.ocx.dynamicCall("GetChejanData(int)", 9001).strip().replace("A", "")
        status = self.ocx.dynamicCall("GetChejanData(int)", 913).strip()
        qty_str = self.ocx.dynamicCall("GetChejanData(int)", 900).strip()
        price_str = self.ocx.dynamicCall("GetChejanData(int)", 901).strip()
        qty = int(qty_str) if qty_str else 0
        price = int(price_str) if price_str else 0

        if self.on_chejan_callback:
            self.on_chejan_callback(gubun, order_no, code, status, qty, price)
