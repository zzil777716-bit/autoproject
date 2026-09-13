# -*- coding: utf-8 -*-
"""
D:/ANTIGRAVITY(자동매매)/strategies/upper_wick_breakout_strategy.py
================================================================================
🏛️ [Antigravity Quant Core]
전략명: 윗꼬리 매집봉 후 장대양봉 돌파 전략 (Upper Wick Bullish Breakout Strategy)
================================================================================
• 핵심 설계 원리:
  1. 사전 매집 확인 (Pre-condition):
     - 최근 N거래일(1~5일) 내 장기이평(60/112/120/224/240일선)을 터치하고 윗꼬리를 형성한 매집봉 발생
  2. 당일 장중 돌파 포착 (Intraday Breakout):
     - 당일 현재가가 전일 윗꼬리 고가 돌파 (또는 전일 종가 대비 +3.0% 이상 장대양봉 전개)
     - 순간 체결강도 >= 115% ~ 120%
     - 거래량 중심축(VWAP) 상향 지지
  3. 청산 룰 (규칙 1 & 2 연동):
     - 목표가 1차: 진입가 대비 +2.5% MFE 도달 시 50% 분할 익절 & 본절 스탑(0.0%) 상향
     - 목표가 2차: +5.0% 이상 또는 5일선 이탈 시 잔여 50% 전량 익절
     - 손절선: 진입가 대비 -3.0% 또는 당일 시초가 이탈 시 즉시 손절
================================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

class UpperWickBreakoutStrategy:
    def __init__(self, target_wick_stocks: Optional[Dict[str, Dict[str, Any]]] = None):
        self.target_wick_stocks = target_wick_stocks or {}

    def load_latest_upper_wick_candidates(self, excel_path: str):
        """최근 장기이평 윗꼬리 포착 종목 엑셀 로드"""
        if not os.path.exists(excel_path):
            return {}
        
        xl = pd.ExcelFile(excel_path)
        df = xl.parse(xl.sheet_names[0])
        candidates = {}
        for idx, row in df.iterrows():
            code = str(row.iloc[1]).strip().zfill(6)
            name = str(row.iloc[2]).strip()
            grade = str(row.iloc[4]).strip()
            score = float(row.iloc[5]) if not pd.isna(row.iloc[5]) else 0.0
            touch_ma = str(row.iloc[6]).strip()
            signal_close = float(row.iloc[8]) if not pd.isna(row.iloc[8]) else 0.0
            upper_wick_pct = float(row.iloc[9]) if not pd.isna(row.iloc[9]) else 0.0
            inst_buy = float(row.iloc[16]) if len(row) > 16 and not pd.isna(row.iloc[16]) else 0.0
            foreign_buy = float(row.iloc[17]) if len(row) > 17 and not pd.isna(row.iloc[17]) else 0.0
            
            prev_high = signal_close * (1.0 + (upper_wick_pct / 100.0))

            candidates[code] = {
                'code': code,
                'name': name,
                'grade': grade,
                'score': score,
                'touch_ma': touch_ma,
                'signal_close': signal_close,
                'upper_wick_pct': upper_wick_pct,
                'prev_high': prev_high,
                'inst_buy': inst_buy,
                'foreign_buy': foreign_buy
            }
        self.target_wick_stocks = candidates
        return candidates

    def evaluate_breakout_tick(self, code: str, current_price: float, current_volume: float, 
                              chegyeol_gangdo: float, vwap: float, open_price: float) -> Optional[Dict[str, Any]]:
        """핫패스용 초고속(0ms) 정량 돌파 감별 함수"""
        if code not in self.target_wick_stocks:
            return None

        info = self.target_wick_stocks[code]
        prev_high = info['prev_high']
        signal_close = info['signal_close']

        # 1. 가격 돌파 조건: 전일 윗꼬리 고가 돌파 or 전일종가 대비 +3% 이상 장대양봉
        is_high_breakout = current_price >= prev_high
        day_return_pct = (current_price - signal_close) / signal_close * 100.0
        is_bullish_bar = day_return_pct >= 3.0 and current_price > open_price

        if not (is_high_breakout or is_bullish_bar):
            return None

        # 2. 체결강도 필터: 115% 이상 매수세 우위
        if chegyeol_gangdo < 115.0:
            return None

        # 3. VWAP 지지 여부: 가격이 거래량 가중평균가 위에 위치
        if vwap > 0 and current_price < vwap:
            return None

        target_tp1 = round(current_price * 1.025, 0)
        target_tp2 = round(current_price * 1.050, 0)
        hard_stop = round(max(current_price * 0.970, open_price * 0.995), 0)

        return {
            'event_type': 'UPPER_WICK_BULLISH_BREAKOUT',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'code': code,
            'name': info['name'],
            'grade': info['grade'],
            'score': info['score'],
            'touch_ma': info['touch_ma'],
            'current_price': current_price,
            'open_price': open_price,
            'prev_high': prev_high,
            'signal_close': signal_close,
            'day_return_pct': round(day_return_pct, 2),
            'chegyeol_gangdo': chegyeol_gangdo,
            'vwap': vwap,
            'target_tp1': target_tp1,
            'target_tp2': target_tp2,
            'hard_stop': hard_stop,
            'risk_reward_ratio': round((target_tp1 - current_price) / max(1, (current_price - hard_stop)), 2),
            'inst_buy_prev': info['inst_buy'],
            'foreign_buy_prev': info['foreign_buy']
        }
