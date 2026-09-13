"""
========================================================================================
🔬 [QUANT SIMULATION: TP/SL REDESIGN & TIME-OF-DAY FILTER DEBATE]
Simulates:
1. TP/SL Matrix:
   - Baseline: SL -0.90%, TP1 +1.30%, TP2 +2.50%
   - High RR (1:3 / 1:5): SL -0.90%, TP1 +2.70%, TP2 +4.50%
   - MFE Calibrated: SL -0.90%, TP1 +1.50%, TP2 +2.80%
2. Time Filters:
   - Full (09:15~14:45)
   - Exclude Lunch (12:00~13:00)
   - Exclude 10~11h & 12~13h (Golden Zones Only)
========================================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_data(code: str):
    base_dir = r"D:\ANTIGRAVITY(자동매매)\data\timeseries"
    df_15m = pd.read_csv(os.path.join(base_dir, f"{code}_15m.csv"))
    df_3m = pd.read_csv(os.path.join(base_dir, f"{code}_3m.csv"))
    df_15m['timestamp'] = pd.to_datetime(df_15m['timestamp'])
    df_3m['timestamp'] = pd.to_datetime(df_3m['timestamp'])
    return df_15m, df_3m

def prepare_merged(df_15m, df_3m):
    # 15M 지표
    c15 = df_15m['close']
    ma20 = c15.rolling(20).mean()
    vwap20 = (c15 * df_15m['volume']).rolling(20).sum() / (df_15m['volume'].rolling(20).sum() + 1e-9)
    tenkan13 = (df_15m['high'].rolling(13).max() + df_15m['low'].rolling(13).min()) / 2.0
    all_3lines = (c15 > ma20) & (c15 > vwap20) & (c15 > tenkan13)
    df_15m['sustained_2bars'] = all_3lines & all_3lines.shift(1).fillna(False)

    # 3M 지표
    c3 = df_3m['close']
    ema5 = c3.ewm(span=5, adjust=False).mean()
    rvol = df_3m['volume'] / (df_3m['volume'].rolling(5).mean() + 1e-9)
    df_3m['ema5_cross'] = (c3 > ema5) & (c3.shift(1) <= ema5.shift(1))
    df_3m['rvol_surge'] = rvol >= 1.35

    m15 = df_15m[['timestamp', 'sustained_2bars']]
    merged = pd.merge_asof(df_3m, m15, on='timestamp', direction='backward')
    merged['sustained_2bars'] = merged['sustained_2bars'].fillna(False)
    merged['signal'] = merged['sustained_2bars'] & merged['ema5_cross'] & merged['rvol_surge']
    return merged

def simulate(merged, sl_pct, tp1_pct, tp2_pct, time_filter_mode="all"):
    closes = merged['close'].values
    opens = merged['open'].values
    highs = merged['high'].values
    lows = merged['low'].values
    signals = merged['signal'].values
    time_strs = merged['timestamp'].dt.strftime("%H:%M:%S").values
    hours = merged['timestamp'].dt.hour.values
    n = len(merged)

    trades = []
    in_position = False
    entry_price = 0.0
    highest_price = 0.0
    lowest_price = 0.0
    is_tp1_hit = False
    is_trailing_active = False
    active_sl = sl_pct
    pending_entry = False

    for i in range(20, n):
        cur_price = closes[i]
        cur_open = opens[i]
        cur_high = highs[i]
        cur_low = lows[i]
        time_str = time_strs[i]
        cur_hour = hours[i]

        if pending_entry and not in_position:
            in_position = True
            # 다음 봉 시가 체결 + 슬리피지/수수료 0.065%
            entry_price = cur_open * 1.00065
            highest_price = entry_price
            lowest_price = entry_price
            is_tp1_hit = False
            is_trailing_active = False
            active_sl = sl_pct
            pending_entry = False

        if in_position:
            if cur_high > highest_price: highest_price = cur_high
            if cur_low < lowest_price: lowest_price = cur_low

            high_pnl = ((highest_price - entry_price) / entry_price) * 100.0
            low_pnl = ((cur_low - entry_price) / entry_price) * 100.0

            exit_trade = False
            exit_price = cur_price

            # 손절
            if low_pnl <= active_sl:
                exit_trade = True
                exit_price = entry_price * (1.0 + active_sl / 100.0)

            # 1차 익절 -> 본절 스탑 전환
            elif high_pnl >= tp1_pct and not is_tp1_hit:
                is_tp1_hit = True
                active_sl = 0.10

            # 2차 트레일링
            if high_pnl >= tp2_pct:
                is_trailing_active = True

            if is_trailing_active and not exit_trade:
                trail_price = highest_price * 0.995
                if cur_low <= trail_price:
                    exit_trade = True
                    exit_price = trail_price

            if time_str >= "15:15:00" and not exit_trade:
                exit_trade = True
                exit_price = cur_price

            if exit_trade:
                # 매도시 거래세 + 수수료 + 슬리피지 0.245%
                net_exit = exit_price * 0.99755
                net_pnl = ((net_exit - entry_price) / entry_price) * 100.0
                trades.append(net_pnl)
                in_position = False
            continue

        # 진입 시간대 필터링
        allowed_time = False
        if time_filter_mode == "all":
            allowed_time = "09:15:00" <= time_str <= "14:45:00"
        elif time_filter_mode == "no_lunch":
            allowed_time = ("09:15:00" <= time_str < "12:00:00") or ("13:00:00" <= time_str <= "14:45:00")
        elif time_filter_mode == "golden_zones":
            # 10~11h 및 12~13h 제외
            allowed_time = ("09:15:00" <= time_str < "10:00:00") or ("11:00:00" <= time_str < "12:00:00") or ("13:00:00" <= time_str <= "14:45:00")

        if allowed_time and signals[i]:
            pending_entry = True

    if not trades:
        return {"trades": 0, "win_rate": 0, "net_return": 0, "pf": 0}

    arr = np.array(trades)
    wins = arr[arr > 0]
    losses = arr[arr <= 0]
    wr = (len(wins) / len(arr)) * 100.0
    tot_ret = arr.sum()
    gp = wins.sum() if len(wins) > 0 else 0.0
    gl = abs(losses.sum()) if len(losses) > 0 else 1.0
    pf = gp / (gl + 1e-9)

    return {
        "trades": len(arr),
        "win_rate": wr,
        "net_return": tot_ret,
        "pf": pf
    }

def main():
    sam_15, sam_3 = load_data("005930")
    sk_15, sk_3 = load_data("000660")

    sam_merged = prepare_merged(sam_15, sam_3)
    sk_merged = prepare_merged(sk_15, sk_3)

    configs = [
        ("기존 Baseline (TP1 +1.30% / TP2 +2.50%)", -0.90, 1.30, 2.50),
        ("이론적 고RR (TP1 +2.70% / TP2 +4.50%)", -0.90, 2.70, 4.50),
        ("MFE 현실형 (TP1 +1.50% / TP2 +2.80%)", -0.90, 1.50, 2.80)
    ]

    time_modes = [
        ("전체 시간대 (09:15~14:45)", "all"),
        ("점심 제외 (12~13시 제외)", "no_lunch"),
        ("골든존만 (10~11시 & 12~13시 제외)", "golden_zones")
    ]

    print("=== SK하이닉스 시뮬레이션 결과 (비용 차감 후 Net) ===")
    for c_name, sl, tp1, tp2 in configs:
        for t_name, t_mode in time_modes:
            res = simulate(sk_merged, sl, tp1, tp2, t_mode)
            print(f"[{c_name}] + [{t_name}] ➔ 매매: {res['trades']}회 | 승률: {res['win_rate']:.1f}% | 순수익: {res['net_return']:+.2f}% | PF: {res['pf']:.2f}")

    print("\n=== 삼성전자 시뮬레이션 결과 (비용 차감 후 Net) ===")
    for c_name, sl, tp1, tp2 in configs:
        for t_name, t_mode in time_modes:
            res = simulate(sam_merged, sl, tp1, tp2, t_mode)
            print(f"[{c_name}] + [{t_name}] ➔ 매매: {res['trades']}회 | 승률: {res['win_rate']:.1f}% | 순수익: {res['net_return']:+.2f}% | PF: {res['pf']:.2f}")

if __name__ == "__main__":
    main()
