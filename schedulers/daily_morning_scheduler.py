"""
========================================================================================
⏰ [SCHEDULER: BUSINESS DAY MORNING AUTOMATION DAEMON]
Monitors business day calendar (Mon~Fri) and triggers interactive approval modal at 08:40 AM.
========================================================================================
"""

import os
import sys
import time
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schedulers.interactive_launcher import MorningApprovalDialog, launch_workers
from events.event_bus import global_event_bus, Event

class DailyMorningScheduler:
    def __init__(self, trigger_hour: int = 7, trigger_minute: int = 50):
        self.trigger_hour = trigger_hour
        self.trigger_minute = trigger_minute
        self.last_triggered_date = None
        self.last_calendar_date = None
        self.last_universe_date = None

    @staticmethod
    def is_business_day(dt: datetime = None) -> bool:
        """토/일 주말 제외 영업일 판별 (월:0, 화:1, 수:2, 목:3, 금:4, 토:5, 일:6)"""
        dt = dt or datetime.now()
        return dt.weekday() < 5

    def check_and_trigger(self, force: bool = False):
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        if not force:
            if not self.is_business_day(now):
                return

            # 1. 07:50 장 시작 전 대시보드 팝업
            if self.last_triggered_date != today_str:
                if (now.hour > self.trigger_hour) or (now.hour == self.trigger_hour and now.minute >= self.trigger_minute):
                    self._execute_approval_flow(today_str)

            # 2. 15:35 정규장 마감 후 캘린더 자동 갱신
            if self.last_calendar_date != today_str:
                if (now.hour > 15) or (now.hour == 15 and now.minute >= 35):
                    self._execute_calendar_update(today_str)

            # 3. 21:05 저녁 9시 이후 350종목 데이터 수집 & 2대 검증(윗꼬리/햄버거) 자동 갱신
            if self.last_universe_date != today_str:
                if (now.hour > 21) or (now.hour == 21 and now.minute >= 5):
                    self._execute_universe_collection(today_str)
        else:
            print(">> [DailyScheduler] 🚀 강제 승인 모달 즉시 호출...")
            self._execute_approval_flow(today_str)
            self._execute_calendar_update(today_str)
            self._execute_universe_collection(today_str)

    def _execute_universe_collection(self, today_str: str):
        self.last_universe_date = today_str
        try:
            print(f">> [DailyScheduler] 🚀 [{today_str}] 장 마감 데이터 수집 & 2대 검증(장기이평 윗꼬리 / 햄버거) 파이프라인 가동...")
            from pipelines.daily_market_close_pipeline import run_pipeline
            run_pipeline(today_str)
            print(f">> [DailyScheduler] 📊 [{today_str}] 일일 데이터 수집 및 2대 검증 구글드라이브 업데이트 완료!")
        except Exception as e:
            print(f">> [DailyScheduler] ⚠️ 장 마감 파이프라인 실행 오류: {e}")

    def _execute_calendar_update(self, today_str: str):
        self.last_calendar_date = today_str
        try:
            from workers.theme_calendar_worker import ThemeCalendarWorker
            worker = ThemeCalendarWorker()
            worker.run()
            print(f">> [DailyScheduler] 📅 [{today_str}] 장 마감 바탕화면 캘린더 & 엑셀 자동 갱신 완료!")
        except Exception as e:
            print(f">> [DailyScheduler] ⚠️ 캘린더 갱신 오류: {e}")

    def _execute_approval_flow(self, today_str: str):
        print(f"\n================================================================================")
        print(f">> [DailyScheduler] 🔔 [{today_str}] 영업일 장 시작 알림 모달(PyQt5 대시보드)을 화면에 표시합니다...")
        print(f"================================================================================")
        
        self.last_triggered_date = today_str
        import subprocess
        python_exe = r"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
        dash_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard_app.py")
        subprocess.Popen([python_exe, dash_script])
        
        # 이벤트 버스 및 로그 기록
        global_event_bus.publish_critical("system.scheduler", Event(
            event_type="MORNING_APPROVAL_TRIGGERED",
            payload={"date": today_str, "status": "DASHBOARD_POPPED"}
        ))

    def run_daemon(self):
        """백그라운드 상주 모니터링 루프"""
        print(f">> [DailyScheduler] ⏰ 영업일 모닝 스케줄러 가동 중 (매 영업일 {self.trigger_hour:02d}:{self.trigger_minute:02d} 알림 대기)...")
        while True:
            try:
                self.check_and_trigger(force=False)
                time.sleep(30)  # 30초 주기 확인
            except KeyboardInterrupt:
                print("\n>> [DailyScheduler] 스케줄러 종료.")
                break
            except Exception as e:
                print(f">> [DailyScheduler] 오류 발생: {e}")
                time.sleep(30)

if __name__ == "__main__":
    force_mode = "--force" in sys.argv
    scheduler = DailyMorningScheduler()
    if force_mode:
        scheduler.check_and_trigger(force=True)
    else:
        scheduler.run_daemon()
