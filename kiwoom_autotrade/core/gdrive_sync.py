"""
Google Drive Cloud Auto-Sync Module for Antigravity Trading Systems
Automatically mirrors all collected minute bars, trade journals, quant reports,
and research data lakes to Google Drive (G:\내 드라이브\Antigravity).
"""

import os
import sys
import shutil
from datetime import datetime
from typing import Optional, List

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

class GDriveSync:
    def __init__(self):
        self.target_dir = self._detect_gdrive_path()
        if self.target_dir:
            os.makedirs(self.target_dir, exist_ok=True)
            os.makedirs(os.path.join(self.target_dir, "data"), exist_ok=True)
            os.makedirs(os.path.join(self.target_dir, "research"), exist_ok=True)
            os.makedirs(os.path.join(self.target_dir, "reports"), exist_ok=True)
            print(f">> [GDriveSync] [OK] 구글 드라이브 연동 활성화: {self.target_dir}")
        else:
            print(">> [GDriveSync] [WARN] 구글 드라이브 경로를 찾을 수 없습니다. (로컬에만 저장)")

    def _detect_gdrive_path(self) -> Optional[str]:
        candidates = [
            r"G:\내 드라이브\Antigravity",
            r"C:\Users\HONG\Desktop\구글드라이브(집)\Antigravity",
            r"G:\My Drive\Antigravity",
            os.path.join(os.path.expanduser("~"), "Google Drive", "Antigravity")
        ]
        for c in candidates:
            parent = os.path.dirname(c)
            if os.path.exists(parent):
                os.makedirs(c, exist_ok=True)
                return c
        return None

    def sync_file(self, local_file_path: str, subfolder: str = ""):
        """단일 파일 구글 드라이브 동기화"""
        if not self.target_dir or not os.path.exists(local_file_path):
            return

        try:
            dest_dir = os.path.join(self.target_dir, subfolder) if subfolder else self.target_dir
            os.makedirs(dest_dir, exist_ok=True)
            filename = os.path.basename(local_file_path)
            dest_path = os.path.join(dest_dir, filename)
            
            shutil.copy2(local_file_path, dest_path)
            print(f">> [GDriveSync] [SYNC] {filename} -> {dest_path}")
        except Exception as e:
            print(f">> [GDriveSync] 동기화 실패 ({local_file_path}): {e}")

    def sync_all_research_and_data(self, project_root: str = "."):
        """프로젝트 전체 데이터 및 연구 자료 일괄 동기화"""
        if not self.target_dir:
            return

        print(f"\n>> [GDriveSync] 전체 데이터 & 연구 자료 구글 드라이브 동기화 시작 -> {self.target_dir}")
        
        # 1. data 폴더 내 분봉 CSV, SQLite DB, Parquet 파일 동기화
        data_dir = os.path.join(project_root, "data")
        if os.path.exists(data_dir):
            for root, _, files in os.walk(data_dir):
                for f in files:
                    if f.endswith(('.csv', '.parquet', '.sqlite', '.db', '.md')):
                        src = os.path.join(root, f)
                        rel = os.path.relpath(root, data_dir)
                        sub = os.path.join("data", rel) if rel != "." else "data"
                        self.sync_file(src, sub)

        # 2. tasks 폴더 내 전략 보고서 마크다운 동기화
        tasks_dir = os.path.join(project_root, "tasks")
        if os.path.exists(tasks_dir):
            for f in os.listdir(tasks_dir):
                if f.endswith('.md'):
                    src = os.path.join(tasks_dir, f)
                    self.sync_file(src, "reports")

        print(">> [GDriveSync] [DONE] 구글 드라이브 동기화 완료!\n")

if __name__ == "__main__":
    syncer = GDriveSync()
    syncer.sync_all_research_and_data("D:\\ANTIGRAVITY(자동매매)\\kiwoom_autotrade")
    syncer.sync_all_research_and_data("D:\\ANTIGRAVITY(자동매매)\\sk_hynix_autotrade")
