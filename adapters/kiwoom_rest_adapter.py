# -*- coding: utf-8 -*-
"""
========================================================================================
🌐 [ADAPTER: KIWOOM OFFICIAL REST API CLIENT]
키움증권 공식 REST API 규격 (OAuth 2.0, HTTP POST/GET, 64-bit Python 지원)
참조: https://github.com/Kiwoom-Securities/Kiwoom-REST-API
========================================================================================
"""

import os
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class KiwoomRestAdapter:
    """키움증권 공식 차세대 REST API 어댑터 (64비트 / 모의투자 & 실전 지원)"""

    def __init__(self, is_simulation: bool = True):
        self.is_simulation = is_simulation
        self.host = "https://mockapi.kiwoom.com" if is_simulation else "https://api.kiwoom.com"
        
        self.app_key = os.getenv("KIWOOM_APP_KEY", "")
        self.app_secret = os.getenv("KIWOOM_APP_SECRET", "")
        self.account_no = os.getenv("KIWOOM_ACCOUNT_NO", "")
        
        self.access_token: Optional[str] = None
        self.token_expired_at: Optional[datetime] = None

    def set_credentials(self, app_key: str, app_secret: str, account_no: str, is_simulation: bool = True):
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no
        self.is_simulation = is_simulation
        self.host = "https://mockapi.kiwoom.com" if is_simulation else "https://api.kiwoom.com"
        self.access_token = None

    def issue_token(self) -> bool:
        """[OAuth 2.0] 접근 토큰(Access Token) 발급"""
        if not self.app_key or not self.app_secret:
            print(">> [KiwoomREST] ⚠️ AppKey 또는 SecretKey가 설정되지 않았습니다.")
            return False

        url = f"{self.host}/oauth2/token"
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.app_secret
        }

        try:
            res = requests.post(url, headers=headers, json=body, timeout=10)
            if res.status_code == 200:
                data = res.json()
                self.access_token = data.get("token") or data.get("access_token")
                expires_in = data.get("expires_in", 86400)
                self.token_expired_at = datetime.now() + timedelta(seconds=expires_in - 60)
                env_type = "모의투자" if self.is_simulation else "실전투자"
                print(f">> [KiwoomREST] [OK] OAuth 2.0 Token Issued! ({env_type}, expires_in: {expires_in}s, expires_dt: {data.get('expires_dt')})")
                return True
            else:
                print(f">> [KiwoomREST] [FAIL] Token Request Failed [HTTP {res.status_code}]: {res.text}")
                return False
        except Exception as e:
            print(f">> [KiwoomREST] [FAIL] Token Exception: {e}")
            return False

    def _ensure_token(self) -> bool:
        """토큰 만료 검증 및 자동 갱신"""
        if not self.access_token or (self.token_expired_at and datetime.now() >= self.token_expired_at):
            return self.issue_token()
        return True

    def send_order(self, side: str, code: str, qty: int, price: int, hoga_type: str = "00") -> Dict[str, Any]:
        """
        [국내주식 주문] POST /api/dostk/ordr
        - side: 'BUY' (매수 kt10000), 'SELL' (매도 kt10001)
        - hoga_type: '00' (지정가), '03' (시장가), '06' (최유리지정가)
        """
        if not self._ensure_token():
            return {"success": False, "msg": "토큰 인증 실패"}

        url = f"{self.host}/api/dostk/ordr"
        api_id = "kt10000" if side.upper() == "BUY" else "kt10001"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "api-id": api_id,
            "Content-Type": "application/json;charset=UTF-8"
        }
        body = {
            "dmst_stex_tp": "KRX",
            "stk_cd": code.replace("A", ""),
            "ord_qty": str(qty),
            "ord_uv": str(price) if hoga_type == "00" else "0"
        }

        try:
            res = requests.post(url, headers=headers, json=body, timeout=5)
            data = res.json() if res.status_code == 200 else {}
            if res.status_code == 200 and data.get("rt_cd") == "0":
                ord_no = data.get("ord_no", "-")
                print(f">> [KiwoomREST] [OK] {side} Order Placed: {code} {qty}주 @ {price:,}원 [주문번호: {ord_no}]")
                return {"success": True, "order_no": ord_no, "data": data}
            else:
                msg = data.get("msg1", res.text)
                print(f">> [KiwoomREST] [FAIL] {side} Order Failed [HTTP {res.status_code}]: {msg}")
                return {"success": False, "msg": msg, "data": data}
        except Exception as e:
            print(f">> [KiwoomREST] [FAIL] Order Error: {e}")
            return {"success": False, "msg": str(e)}

    def get_stock_price(self, code: str) -> Dict[str, Any]:
        """[국내주식 시세 조회]"""
        if not self._ensure_token():
            return {}
        # 엔드포인트 호출 규격
        url = f"{self.host}/api/dostk/stk-info"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "api-id": "kt00001",
            "Content-Type": "application/json;charset=UTF-8"
        }
        params = {"stk_cd": code.replace("A", "")}
        try:
            res = requests.get(url, headers=headers, params=params, timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return {}
