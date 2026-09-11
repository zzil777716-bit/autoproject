# -*- coding: utf-8 -*-
"""
========================================================================================
🪙 [COIN ADAPTER: UPBIT REST API CLIENT]
Supports JWT authentication, account inquiry, market prices, and order execution.
Docs: https://docs.upbit.com/
========================================================================================
"""

import os
import time
import uuid
import hashlib
import urllib.parse
import requests
import jwt
from typing import Dict, Any, List, Optional

class UpbitAdapter:
    def __init__(self, access_key: str = "", secret_key: str = ""):
        self.access_key = access_key or os.getenv("UPBIT_ACCESS_KEY", "")
        self.secret_key = secret_key or os.getenv("UPBIT_SECRET_KEY", "")
        self.server_url = "https://api.upbit.com"

    def _get_headers(self, query: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """JWT 토큰 생성 (Query Hash 포함)"""
        payload = {
            "access_key": self.access_key,
            "nonce": str(uuid.uuid4())
        }
        if query:
            query_string = urllib.parse.urlencode(query).encode("utf-8")
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()
            payload["query_hash"] = query_hash
            payload["query_hash_alg"] = "SHA512"

        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = f"Bearer {jwt_token}"
        return {"Authorization": authorization}

    def get_accounts(self) -> List[Dict[str, Any]]:
        """전체 계좌 잔고 조회"""
        url = f"{self.server_url}/v1/accounts"
        try:
            res = requests.get(url, headers=self._get_headers(), timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f">> [UpbitAdapter] 계좌 조회 에러: {e}")
        return []

    def get_current_price(self, markets: List[str]) -> Dict[str, float]:
        """현재가 조회 (예: ['KRW-BTC', 'KRW-ETH'])"""
        url = f"{self.server_url}/v1/ticker"
        params = {"markets": ",".join(markets)}
        try:
            res = requests.get(url, params=params, timeout=5)
            if res.status_code == 200:
                return {item["market"]: float(item["trade_price"]) for item in res.json()}
        except Exception as e:
            print(f">> [UpbitAdapter] 현재가 조회 에러: {e}")
        return {}

    def get_ohlcv(self, market: str, unit_min: int = 15, count: int = 100) -> List[Dict[str, Any]]:
        """분봉 캔들 조회 (unit_min: 1, 3, 5, 15, 60 등)"""
        url = f"{self.server_url}/v1/candles/minutes/{unit_min}"
        params = {"market": market, "count": count}
        try:
            res = requests.get(url, params=params, timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f">> [UpbitAdapter] 캔들 조회 에러: {e}")
        return []

    def send_order(self, market: str, side: str, volume: float, price: float, ord_type: str = "limit") -> Dict[str, Any]:
        """주문 접수 (side: 'bid' 매수, 'ask' 매도 / ord_type: 'limit' 지정가, 'price' 시장가매수, 'market' 시장가매도)"""
        url = f"{self.server_url}/v1/orders"
        body = {
            "market": market,
            "side": side,
            "ord_type": ord_type
        }
        if ord_type == "limit":
            body["volume"] = str(volume)
            body["price"] = str(price)
        elif ord_type == "price":
            body["price"] = str(price)  # 시장가 매수는 금액 투입
        elif ord_type == "market":
            body["volume"] = str(volume) # 시장가 매도는 수량 투입

        try:
            headers = self._get_headers(body)
            headers["Content-Type"] = "application/json"
            res = requests.post(url, headers=headers, json=body, timeout=5)
            return res.json()
        except Exception as e:
            print(f">> [UpbitAdapter] 주문 에러: {e}")
            return {"error": str(e)}
