import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QTimer

class KiwoomWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("키움 OpenAPI+ 동기화 테스트")
        self.resize(400, 200)

        # 중앙 위젯 구성
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("Active-X 로드 중...", self)
        layout.addWidget(self.status_label)

        self.btn_login = QPushButton("로그인 창 다시 띄우기", self)
        self.btn_login.clicked.connect(self.request_login)
        layout.addWidget(self.btn_login)

        # Active-X 컨트롤 로드
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1", self)
        self.ocx.OnEventConnect.connect(self.on_event_connect)

        self.status_label.setText("Active-X 로드 완료. 1초 후 로그인 요청...")
        print("[Step 1] GUI Window 생성 및 Active-X 바인딩 완료", flush=True)

        # 1초 후 로그인 창 호출
        QTimer.singleShot(1000, self.request_login)

    def request_login(self):
        print("[Step 2] CommConnect 호출 시도...", flush=True)
        self.status_label.setText("키움증권 로그인 창을 띄우는 중입니다...")
        ret = self.ocx.dynamicCall("CommConnect()")
        print(f"[Step 2] CommConnect 반환값: {ret}", flush=True)

    def on_event_connect(self, err_code):
        print(f"[Step 3] OnEventConnect 이벤트 수신: {err_code}", flush=True)
        if err_code == 0:
            user_name = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_NAME")
            user_id = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_ID")
            accounts = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO").split(';')
            accounts = [a for a in accounts if a]
            
            msg = f"로그인 성공!\n사용자: {user_name} ({user_id})\n계좌: {', '.join(accounts)}"
            self.status_label.setText(msg)
            print(f"[Step 3] [SUCCESS] {msg}", flush=True)
        else:
            self.status_label.setText(f"로그인 실패 (오류 코드: {err_code})")
            print(f"[Step 3] [FAIL] 로그인 실패 (코드: {err_code})", flush=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KiwoomWindow()
    window.show()
    sys.exit(app.exec_())
