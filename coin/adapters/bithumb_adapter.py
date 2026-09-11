# -*- coding: utf-8 -*-
"""
========================================================================================
🪙 [COIN ADAPTER: BITHUMB REST API CLIENT]
Supports HMAC-SHA512 authentication, account balance, public ticker, and order execution.
Docs: https://apidocs.bithumb.com/
========================================================================================
"""

import os
import time
import base64
import hmac
import hashlib
import urllib.parse
import requests
from typing import Dict, Any, List, Optional

class BithumbAdapter:
    def __init__(self, connect_key: str = "", secret_key: str = ""):
        self.connect_key = connect_key or os.getenv("BITHUMB_CONNECT_KEY", "")
        self.secret_key = secret_key or os.getenv("BITHUMB_SECRET_KEY", "")
        self.server_url = "https://api.bithumb.com"

    def _get_headers(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, str]:
        """Bithumb HMAC-SHA512 시그니처 생성"""
        nonce = str(int(time.time() * 1000))
        str_data = urllib.parse.urlencode(params)
        data = f"{endpoint}\x00{str_data}\x00{nonce}"
        utf8_data = data.encode('utf-8')
        key = self.secret_key.encode('utf-8')
        
        signature = hmac.new(key, utf8_data, hashlib.sha512).hexdigest()
        api_sign = base64.b64encode(signature.encode('utf-8')).decode('utf-8')

        return {
            "Api-Key": self.connect_key,
            "Api-Sign": api_sign,
            "Api-Nonce": nonce,
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def get_balance(self, currency: str = "ALL") -> Dict[str, Any]:
        """자산 잔고 조회"""
        endpoint = "/info/balance"
        url = f"{self.server_url}{endpoint}"
        params = {"currency": currency}
        try:
            headers = self._get_headers(endpoint, params)
            res = requests.post(url, headers=headers, data=params, timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f">> [BithumbAdapter] 잔고 조회 에러: {e}")
        return {}

    def get_current_price(self, order_currency: str = "BTC", payment_currency: str = "KRW") -> float:
        """현재가 조회"""
        url = f"{self.server_url}/public/ticker/{order_currency}_{payment_currency}"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json().get("data", {})
                return float(data.get("closing_price", 0.0))
        except Exception as e:
            print(f">> [BithumbAdapter] 현재가 조회 에러: {e}")
        return 0.0

    def send_order(self, order_currency: str, payment_currency: str, units: float, price: int, side: str = "bid") -> Dict[str, Any]:
        """주문 접수 (side: 'bid' 매수, 'ask' 매도)"""
        endpoint = "/trade/place"
        url = f"{self.server_url}{endpoint}"
        params = {
            "order_currency": order_currency,
            "payment_currency": payment_currency,
            "units": str(units),
            "price": str(price),
            "type": side
        }
        try:
            headers = self._get_headers(endpoint, params)
            res = requests.post(url, headers=headers, data=params, timeout=5)
            return res.json()
        except Exception as e:
            print(f">> [BithumbAdapter] 주문 에러: {e}")
            return {"error": str(e)}
