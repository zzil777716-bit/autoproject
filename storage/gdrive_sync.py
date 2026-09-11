"""
========================================================================================
☁️ [STORAGE: GOOGLE DRIVE CLOUD AUTO-SYNC PIPELINE (ASYNC NON-BLOCKING)]
Non-blocking background thread worker for trade logs and hot-path decoupled synchronization.
Target: G:\내 드라이브\Antigravity (architecture, data, research, 테마, 캘린더, reports)
========================================================================================
"""

import os
import sys
import shutil
import queue
import threading
from typing import Optional, List, Tuple

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

class GDriveSync:
    CANDIDATE_PATHS = [
        r"G:\내 드라이브\Antigravity",
        r"G:\My Drive\Antigravity",
        r"C:\Users\HONG\Google Drive\Antigravity"
    ]

    SUBDIRECTORIES = [
        "architecture",
        "data",
        "research",
        "테마",
        "캘린더",
        "reports"
    ]

    def __init__(self, target_dir: Optional[str] = None):
        self.target_dir = target_dir or self._detect_gdrive_path()
        
        # 핫패스 분리를 위한 비동기 백그라운드 큐 & 워커 스레드
        self._async_queue: queue.Queue = queue.Queue()
        self._is_worker_running = True
        self._worker_thread = threading.Thread(target=self._async_sync_worker, daemon=True)
        self._worker_thread.start()

        if self.target_dir:
            self._init_subdirectories()
            print(f">> [GDriveSync] [OK] 구글 드라이브 연동 활성화: {self.target_dir} (비동기 핫패스 분리 워커 가동)")
        else:
            print(">> [GDriveSync] [INFO] 로컬 구글 드라이브 경로가 감지되지 않아 로컬 모드로 동작합니다.")

    def _detect_gdrive_path(self) -> Optional[str]:
        for path in self.CANDIDATE_PATHS:
            drive = os.path.splitdrive(path)[0]
            if drive and os.path.exists(drive):
                try:
                    os.makedirs(path, exist_ok=True)
                    return path
                except Exception:
                    continue
        return None

    def _init_subdirectories(self):
        if not self.target_dir:
            return
        for sub in self.SUBDIRECTORIES:
            sub_path = os.path.join(self.target_dir, sub)
            os.makedirs(sub_path, exist_ok=True)

    def sync_file_async(self, source_path: str, target_subfolder: str):
        """
        🚀 핫패스 전용 비동기 동기화 (주문/매매 로직에서 0.01ms 내 반환)
        I/O 블로킹 없이 백그라운드 큐에 작업을 위임합니다.
        """
        self._async_queue.put((source_path, target_subfolder))

    def _async_sync_worker(self):
        """백그라운드 스레드에서 파일 복사 수행"""
        while self._is_worker_running:
            try:
                item = self._async_queue.get(timeout=1.0)
                if item is None:
                    break
                source_path, target_subfolder = item
                self.sync_file(source_path, target_subfolder)
                self._async_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f">> [GDriveSync] 비동기 워커 오류: {e}")

    def sync_file(self, source_path: str, target_subfolder: str) -> bool:
        """동기식 파일 복사"""
        if not self.target_dir or not os.path.exists(source_path):
            return False
        try:
            dest_dir = os.path.join(self.target_dir, target_subfolder)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, os.path.basename(source_path))
            shutil.copy2(source_path, dest_path)
            print(f">> [GDriveSync] [SYNC] {os.path.basename(source_path)} -> {dest_path}")
            return True
        except Exception as e:
            print(f">> [GDriveSync] [ERROR] 동기화 실패 ({source_path}): {e}")
            return False

    def sync_all(self, base_dir: str = r"C:\Antigravity"):
        """로컬 전체 하위 산출물 일괄 동기화 (배치/스케줄용)"""
        print(f"\n>> [GDriveSync] 🔄 구글 드라이브 전 계층 자동 동기화 시작...")
        
        # 1. architecture
        arch_file = os.path.join(base_dir, "reports", "architecture_blueprint.md")
        if os.path.exists(arch_file):
            self.sync_file(arch_file, "architecture")

        # 2. research & DB
        res_dir = os.path.join(base_dir, "data", "research")
        if os.path.exists(res_dir):
            for f in os.listdir(res_dir):
                self.sync_file(os.path.join(res_dir, f), "research")

        # 3. 테마
        theme_dir = os.path.join(base_dir, "data", "themes")
        if os.path.exists(theme_dir):
            for f in os.listdir(theme_dir):
                self.sync_file(os.path.join(theme_dir, f), "테마")

        # 4. 캘린더
        cal_dir = os.path.join(base_dir, "data", "calendar")
        if os.path.exists(cal_dir):
            for f in os.listdir(cal_dir):
                self.sync_file(os.path.join(cal_dir, f), "캘린더")
        desktop_cal = r"C:\Users\HONG\Desktop\증시_주도테마_캘린더.html"
        if os.path.exists(desktop_cal):
            self.sync_file(desktop_cal, "캘린더")

        # 5. reports
        rep_dir = os.path.join(base_dir, "reports")
        if os.path.exists(rep_dir):
            for f in os.listdir(rep_dir):
                f_path = os.path.join(rep_dir, f)
                if os.path.isfile(f_path):
                    self.sync_file(f_path, "reports")

        print(f">> [GDriveSync] ✅ 전 계층 구글 드라이브 동기화 완료!\n")

if __name__ == "__main__":
    syncer = GDriveSync()
    syncer.sync_all()
