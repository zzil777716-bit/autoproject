"""
========================================================================================
📊 [QUANT RESEARCH ANALYZER] 일일 매매 일지 & 전략 최적화 연구 리포트 생성기
Analyzes MFE/MAE excursions, Win Rate, Profit Factor, and Parameter Sensitivities.
Automatically mirrors generated reports to Google Drive (G:\내 드라이브\Antigravity).
========================================================================================
"""

import os
import sys
import sqlite3
from datetime import datetime
import pandas as pd
import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from core.gdrive_sync import GDriveSync

def generate_report(base_dir: str = "."):
    db_path = os.path.join(base_dir, "data", "research", "trade_journal.sqlite")
    if not os.path.exists(db_path):
        print(f">> [Info] 매매 일지 데이터베이스가 아직 생성되지 않았습니다. ({db_path})")
        return

    with sqlite3.connect(db_path) as conn:
        df_trades = pd.read_sql_query("SELECT * FROM trade_journal WHERE exit_time IS NOT NULL", conn)

    if df_trades.empty:
        print(">> [Info] 완료된 매매 내역이 없습니다. (실시간 트레이딩 완료 후 실행해 주세요)")
        return

    total_trades = len(df_trades)
    winning_trades = df_trades[df_trades['pnl_won'] > 0]
    losing_trades = df_trades[df_trades['pnl_won'] < 0]
    win_rate = (len(winning_trades) / total_trades) * 100.0 if total_trades > 0 else 0.0

    total_pnl = df_trades['pnl_won'].sum()
    gross_profit = winning_trades['pnl_won'].sum() if not winning_trades.empty else 0
    gross_loss = abs(losing_trades['pnl_won'].sum()) if not losing_trades.empty else 0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)

    avg_mfe = df_trades['mfe_pct'].mean()
    avg_mae = df_trades['mae_pct'].mean()
    avg_hold_min = (df_trades['holding_seconds'].mean()) / 60.0

    today_str = datetime.now().strftime('%Y-%m-%d')
    report_file = os.path.join(base_dir, "data", "research", f"quant_analysis_report_{today_str}.md")

    report_content = f"""# 📈 [{today_str}] 퀀트 트레이딩 실전 성과 & 전략 개선 연구 리포트

## 1. 📊 종합 성과 요약 (Executive Performance Summary)

| 지표 항목 | 성과 수치 | 평가 및 분석 |
| :--- | :---: | :--- |
| **총 매매 횟수** | **{total_trades}회** | 일일 한도(3회) 내 규칙 준수 |
| **승률 (Win Rate)** | **{win_rate:.1f}%** | ({len(winning_trades)}승 {len(losing_trades)}패) |
| **총 실현 손익** | **{total_pnl:+,.0f}원** | 1주 모의투자 누적 손익 |
| **손익비 (Profit Factor)** | **{profit_factor:.2f}** | 총수익 / 총손실 비율 |
| **평균 MFE (최대 유리 수익률)** | **+{avg_mfe:.2f}%** | 진입 후 주가가 가장 높이 올라갔던 평균치 |
| **평균 MAE (최대 불리 손실률)** | **{avg_mae:.2f}%** | 진입 후 주가가 가장 깊이 하락했던 평균치 |
| **평균 보유 시간** | **{avg_hold_min:.1f}분** | 단기 스캘핑/데이 모멘텀 사이클 |

---

## 2. 🎯 전략 파라미터 최적화 연구 (Quant Optimization Insights)

### 💡 MFE / MAE 분석을 통한 파라미터 개선 가이드:
1. **손절선(-0.90%) 유효성**:
   - 실제 승리한 매매들의 평균 MAE가 `{abs(winning_trades['mae_pct'].mean()):.2f}%` 수준이라면, 일시적 노이즈를 견뎌내고 반등한 것입니다.
2. **익절선(+1.30% / +2.50%) 확장 여력**:
   - 평균 MFE가 `+{avg_mfe:.2f}%`에 달한다면, 트레일링 스탑 개시 시점을 상향하여 초과 수익을 더 길게 추종할 수 있습니다.

---

## 3. 📝 상세 매매 일지 내역 (Trade Journal)

| 매매 ID | 종목명 | 진입시각 | 진입가 | 청산시각 | 청산가 | 손익금 | 수익률 | 청산 사유 | MFE | MAE |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: |
"""

    for _, row in df_trades.iterrows():
        report_content += f"| `{row['trade_id']}` | **{row['stock_name']}** | {row['entry_time']} | {row['entry_price']:,.0f}원 | {row['exit_time']} | {row['exit_price']:,.0f}원 | **{row['pnl_won']:+,.0f}원** | `{row['pnl_pct']:+.2f}%` | {row['exit_reason']} | `+{row['mfe_pct']:.2f}%` | `{row['mae_pct']:.2f}%` |\n"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f">> [QuantReport] ✅ 일일 분석 리포트 생성 완료: {os.path.abspath(report_file)}")
    print(f"   • 총 매매: {total_trades}회 | 승률: {win_rate:.1f}% | 총손익: {total_pnl:+,.0f}원 | PF: {profit_factor:.2f}")

    # 구글 드라이브 동기화
    gdrive = GDriveSync()
    gdrive.sync_file(report_file, "reports")

if __name__ == "__main__":
    generate_report()
