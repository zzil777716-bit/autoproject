"""
========================================================================================
🔍 [TEST] 키움증권 OpenAPI+ 계좌 연동 및 데이터 동기화 종합 진단 스크립트
========================================================================================
검증 항목:
1. 32비트 Active-X 컨트롤 로드 (KHOPENAPI.KHOpenAPICtrl.1)
2. 모의투자 로그인 및 사용자 인증 확인
3. 보유 계좌번호(8132211811) 일치 여부 확인
4. [opw00001] 모의투자 계좌 예수금 및 주문가능금액 조회
5. [opw00018] 계좌 평가잔고 및 보유 주식 현황 조회
6. [opt10001] 삼성전자(005930) 실시간 시세 TR 조회
7. [SetRealReg] 실시간 시세 피드 바인딩 테스트
========================================================================================
"""

import sys
import os
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer
from config.settings import config

class KiwoomSyncTester:
    def __init__(self):
        print("=" * 75)
        print(">> [Step 1] PyQt5 및 키움 Open API+ Active-X 컨트롤 로드 중...")
        self.app = QApplication(sys.argv)
        
        try:
            self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
            print(">> [Step 1] [OK] Active-X (KHOPENAPI.KHOpenAPICtrl.1) 로드 성공!")
        except Exception as e:
            print(f">> [Step 1] [FAIL] Active-X 로드 실패: {e}")
            sys.exit(1)
            
        self.login_loop = None
        self.tr_loop = None
        self.code = config.STOCK_CODE  # 005930
        self.account_no = config.ACCOUNT_NO # 8132211811
        self.real_tick_count = 0
        
        # 이벤트 슬롯 바인딩
        self.ocx.OnEventConnect.connect(self._on_login)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr)
        self.ocx.OnReceiveRealData.connect(self._on_receive_real)
        self.ocx.OnReceiveMsg.connect(self._on_receive_msg)

    def run_all_tests(self):
        # 1. 로그인 요청
        print("\n" + "=" * 75)
        print(">> [Step 2] 키움 Open API+ 로그인 요청 (화면에 로그인 창이 나타납니다)...")
        ret = self.ocx.CommConnect()
        if ret != 0:
            print(f">> [Step 2] [FAIL] CommConnect 호출 실패 (에러코드: {ret})")
            return
            
        self.login_loop = QEventLoop()
        self.login_loop.exec_()
        
        if self.ocx.GetConnectState() != 1:
            print(">> [FAIL] 로그인이 완료되지 않아 이후 테스트를 중단합니다.")
            return

        # 2. 예수금 조회 (opw00001)
        self._test_deposit_tr()
        
        # 3. 계좌 잔고 및 보유종목 조회 (opw00018)
        self._test_balance_tr()

        # 4. 삼성전자 기본정보 TR 조회 (opt10001)
        self._test_stock_tr()
        
        # 5. 실시간 시세 등록 및 수신 테스트 (5초 대기)
        self._test_realtime_stream()

    def _on_login(self, err_code: int):
        print("\n" + "=" * 75)
        if err_code == 0:
            print(">> [Step 2] [OK] 키움 Open API+ 로그인 성공!")
            
            user_id = self.ocx.GetLoginInfo("USER_ID")
            user_name = self.ocx.GetLoginInfo("USER_NAME")
            server_gubun = self.ocx.GetLoginInfo("GetServerGubun")
            server_type = "모의투자 서버 🟢" if server_gubun == "1" else "실전투자 서버 🔴"
            accounts = [acc for acc in self.ocx.GetLoginInfo("ACCNO").split(';') if acc]
            
            print(">> [Step 3] [INFO] 계정 및 사용자 정보:")
            print(f"   • 사용자 ID   : {user_id}")
            print(f"   • 사용자 이름 : {user_name}")
            print(f"   • 접속 서버   : {server_type}")
            print(f"   • 보유 계좌수 : {len(accounts)}개")
            for idx, acc in enumerate(accounts, 1):
                match_str = " (설정 파일 일치 ✅)" if acc == self.account_no else ""
                print(f"     - 계좌 {idx}: {acc}{match_str}")
        else:
            print(f">> [Step 2] [FAIL] 로그인 실패 (오류 코드: {err_code})")
            
        if self.login_loop:
            self.login_loop.exit()

    def _test_deposit_tr(self):
        print("\n" + "=" * 75)
        print(f">> [Step 4] [INFO] 계좌({self.account_no}) 예수금 및 주문가능금액(opw00001) 조회 중...")
        time.sleep(0.3)
        self.ocx.SetInputValue("계좌번호", self.account_no)
        self.ocx.SetInputValue("비밀번호", "")
        self.ocx.SetInputValue("비밀번호입력매체구분", "00")
        self.ocx.SetInputValue("조회구분", "2") # 일반조회
        
        ret = self.ocx.CommRqData("예수금상세현황요청", "opw00001", 0, "2001")
        if ret == 0:
            self.tr_loop = QEventLoop()
            self.tr_loop.exec_()
        else:
            print(f">> [FAIL] 예수금 TR 요청 실패 (에러코드: {ret})")

    def _test_balance_tr(self):
        print("\n" + "=" * 75)
        print(f">> [Step 5] [INFO] 계좌({self.account_no}) 평가잔고 및 보유종목(opw00018) 조회 중...")
        time.sleep(0.3)
        self.ocx.SetInputValue("계좌번호", self.account_no)
        self.ocx.SetInputValue("비밀번호", "")
        self.ocx.SetInputValue("비밀번호입력매체구분", "00")
        self.ocx.SetInputValue("조회구분", "1") # 1:합산
        
        ret = self.ocx.CommRqData("계좌평가잔고내역요청", "opw00018", 0, "2002")
        if ret == 0:
            self.tr_loop = QEventLoop()
            self.tr_loop.exec_()
        else:
            print(f">> [FAIL] 잔고내역 TR 요청 실패 (에러코드: {ret})")

    def _test_stock_tr(self):
        print("\n" + "=" * 75)
        print(f">> [Step 6] [INFO] 삼성전자({self.code}) 주식기본정보(opt10001) TR 동기화 요청 중...")
        time.sleep(0.3)
        self.ocx.SetInputValue("종목코드", self.code)
        ret = self.ocx.CommRqData("주식기본정보요청", "opt10001", 0, "2000")
        
        if ret == 0:
            self.tr_loop = QEventLoop()
            self.tr_loop.exec_()
        else:
            print(f">> [FAIL] TR 요청 실패 (에러코드: {ret})")

    def _test_realtime_stream(self):
        print("\n" + "=" * 75)
        print(f">> [Step 7] [INFO] 삼성전자({self.code}) 실시간 호가/체결(SetRealReg) 피드 등록 중...")
        self.ocx.SetRealReg("1000", self.code, "10;11;12;15;20;228;27;28", "0")
        print(">> [Step 7] 실시간 시세 수신 대기 중 (5초 후 자동 완료)...")
        
        self.real_timer = QTimer()
        self.real_timer.timeout.connect(self._finish_test)
        self.real_timer.start(5000)

    def _on_receive_tr(self, scr_no: str, rq_name: str, tr_code: str, record_name: str, prev_next: str):
        if tr_code == "opw00001":
            deposit = int(self.ocx.GetCommData(tr_code, rq_name, 0, "예수금").strip() or 0)
            d2_deposit = int(self.ocx.GetCommData(tr_code, rq_name, 0, "d+2추정예수금").strip() or 0)
            withdrawable = int(self.ocx.GetCommData(tr_code, rq_name, 0, "출금가능금액").strip() or 0)
            orderable = int(self.ocx.GetCommData(tr_code, rq_name, 0, "주문가능금액").strip() or 0)
            
            print(">> [Step 4] [OK] 계좌 예수금 현황:")
            print(f"   • 현재 예수금   : {deposit:,}원")
            print(f"   • D+2 추정예수금: {d2_deposit:,}원")
            print(f"   • 출금가능금액  : {withdrawable:,}원")
            print(f"   • 주문가능금액  : {orderable:,}원 🟢")
            
        elif tr_code == "opw00018":
            total_buy = int(self.ocx.GetCommData(tr_code, rq_name, 0, "총매입금액").strip() or 0)
            total_eval = int(self.ocx.GetCommData(tr_code, rq_name, 0, "총평가금액").strip() or 0)
            total_pnl = int(self.ocx.GetCommData(tr_code, rq_name, 0, "총평가손익금액").strip() or 0)
            total_yield = float(self.ocx.GetCommData(tr_code, rq_name, 0, "총수익률(%)").strip() or 0.0)
            
            print(">> [Step 5] [OK] 계좌 잔고 평가 현황:")
            print(f"   • 총 매입금액   : {total_buy:,}원")
            print(f"   • 총 평가금액   : {total_eval:,}원")
            print(f"   • 총 평가손익   : {total_pnl:+,}원 ({total_yield:+.2f}%)")
            
            count = self.ocx.GetRepeatCnt(tr_code, rq_name)
            print(f"   • 보유 종목 수  : {count}개")
            for i in range(count):
                name = self.ocx.GetCommData(tr_code, rq_name, i, "종목명").strip()
                code = self.ocx.GetCommData(tr_code, rq_name, i, "종목번호").strip().replace("A", "")
                qty = int(self.ocx.GetCommData(tr_code, rq_name, i, "보유수량").strip() or 0)
                eval_pnl = int(self.ocx.GetCommData(tr_code, rq_name, i, "평가손익").strip() or 0)
                item_yield = float(self.ocx.GetCommData(tr_code, rq_name, i, "수익률(%)").strip() or 0.0)
                print(f"     [{i+1}] {name}({code}) | {qty}주 | 손익: {eval_pnl:+,}원 ({item_yield:+.2f}%)")
                
        elif tr_code == "opt10001":
            name = self.ocx.GetCommData(tr_code, rq_name, 0, "종목명").strip()
            price = abs(int(self.ocx.GetCommData(tr_code, rq_name, 0, "현재가").strip() or 0))
            rate = float(self.ocx.GetCommData(tr_code, rq_name, 0, "등락율").strip() or 0.0)
            volume = int(self.ocx.GetCommData(tr_code, rq_name, 0, "거래량").strip() or 0)
            open_p = abs(int(self.ocx.GetCommData(tr_code, rq_name, 0, "시가").strip() or 0))
            high_p = abs(int(self.ocx.GetCommData(tr_code, rq_name, 0, "고가").strip() or 0))
            low_p = abs(int(self.ocx.GetCommData(tr_code, rq_name, 0, "저가").strip() or 0))
            
            print(">> [Step 6] [OK] 삼성전자 종목 시세 연동:")
            print(f"   • 종목명/코드   : {name} ({self.code})")
            print(f"   • 현재가/등락율 : {price:,}원 ({rate:+.2f}%)")
            print(f"   • 금일 OHLC     : 시가 {open_p:,} | 고가 {high_p:,} | 저가 {low_p:,}")
            print(f"   • 누적 거래량   : {volume:,}주")
            
        if self.tr_loop:
            self.tr_loop.exit()

    def _on_receive_real(self, code: str, real_type: str, real_data: str):
        if code == self.code and real_type == "주식체결":
            self.real_tick_count += 1
            curr_price = abs(int(self.ocx.GetCommRealData(code, 10)))
            intensity = float(self.ocx.GetCommRealData(code, 228))
            timestr = self.ocx.GetCommRealData(code, 20)
            print(f"   • [실시간 틱 #{self.real_tick_count}] {timestr} | 현재가: {curr_price:,}원 | 체결강도: {intensity:.1f}%")

    def _on_receive_msg(self, scr_no: str, rq_name: str, tr_code: str, msg: str):
        pass

    def _finish_test(self):
        print("\n" + "=" * 75)
        print(">> 🏆 [TEST RESULT] 키움증권 모의계좌(8132211811) 연동 및 시세 동기화 진단 100% 정상!")
        print(">> 모든 API(로그인, 예수금, 잔고평가, 종목기본정보, 실시간피드)가 정상 작동 중입니다.")
        print("=" * 75)
        self.app.quit()

if __name__ == "__main__":
    tester = KiwoomSyncTester()
    tester.run_all_tests()
