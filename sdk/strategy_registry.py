"""
========================================================================================
🏛️ [SDK: STRATEGY REGISTRY & PLUGIN EXTENSION FRAMEWORK]
Allows seamless addition of new quant strategies, ML models, and universe scalpers.
1. Decorator-based Strategy Registration (@register_strategy)
2. Dynamic Strategy Discovery & Factory instantiation
3. Multi-Stock Universe Scalability (Supports KOSPI 200, KOSDAQ 150, or custom baskets)
4. Full backward-compatibility with existing Strategy A & Strategy B
========================================================================================
"""

import inspect
from typing import Dict, Type, List, Optional, Any
from sdk.base_strategy import BaseStrategy, DualStrategyEngine

_STRATEGY_REGISTRY: Dict[str, Type[BaseStrategy]] = {}
_STRATEGY_METADATA: Dict[str, Dict[str, Any]] = {}

def register_strategy(name: str, description: str = "", default_stocks: Optional[List[str]] = None):
    """
    데코레이터: 신규 퀀트 전략 클래스를 글로벌 레지스트리에 자동 등록.
    
    사용 예시:
    @register_strategy(name="RSI_DIVERGENCE", description="15M RSI 다이버전스 반등 전략", default_stocks=["005930", "000660"])
    class RSIDivergenceStrategy(BaseStrategy):
        ...
    """
    def decorator(cls: Type[BaseStrategy]):
        if not issubclass(cls, BaseStrategy):
            raise TypeError(f"전략 클래스 '{cls.__name__}'는 BaseStrategy를 상속해야 합니다.")
        
        strategy_key = name.upper().strip()
        _STRATEGY_REGISTRY[strategy_key] = cls
        _STRATEGY_METADATA[strategy_key] = {
            "name": strategy_key,
            "class_name": cls.__name__,
            "description": description or (cls.__doc__ or "").strip(),
            "default_stocks": default_stocks or ["005930", "000660"],
            "module": cls.__module__
        }
        return cls
    return decorator

class StrategyRegistry:
    """전략 팩토리 및 플러그인 관리자"""
    
    @classmethod
    def get_registered_strategies(cls) -> Dict[str, Dict[str, Any]]:
        """등록된 모든 전략의 메타데이터 조회"""
        return _STRATEGY_METADATA.copy()

    @classmethod
    def create_strategy(cls, strategy_name: str, code: str, stock_name: str, **kwargs) -> Optional[BaseStrategy]:
        """등록된 전략 이름으로 인스턴스 팩토리 생성"""
        key = strategy_name.upper().strip()
        strategy_cls = _STRATEGY_REGISTRY.get(key)
        if not strategy_cls:
            return None
        return strategy_cls(code=code, stock_name=stock_name, **kwargs)

    @classmethod
    def list_strategy_names(cls) -> List[str]:
        """등록된 전략 키 목록 반환"""
        return list(_STRATEGY_REGISTRY.keys())

# ========================================================================================
# 기본 내장 4대 핵심 전략 자동 등록
# ========================================================================================
from sdk.base_strategy import (
    Samsung3LinesSustainedStrategy,
    SKHynix3LinesMomentumStrategy,
    SamsungAlignmentDisparityStrategy,
    SKHynixAlignmentDisparityStrategy
)

register_strategy(
    name="STRATEGY_A_3LINES_SAM",
    description="삼성전자 15M 3선 2봉 연속 종가유지 안착 전략",
    default_stocks=["005930"]
)(Samsung3LinesSustainedStrategy)

register_strategy(
    name="STRATEGY_A_3LINES_SK",
    description="SK하이닉스 15M 3선 유지 + 3M 5EMA 돌파 및 RVOL 점화 전략",
    default_stocks=["000660"]
)(SKHynix3LinesMomentumStrategy)

register_strategy(
    name="STRATEGY_B_MA_ALIGNMENT_SAM",
    description="삼성전자 15M 20-60-120 정배열 황금이격(101.5%~103.0%) 전략",
    default_stocks=["005930"]
)(SamsungAlignmentDisparityStrategy)

register_strategy(
    name="STRATEGY_B_MA_ALIGNMENT_SK",
    description="SK하이닉스 15M 20-60-120 정배열 황금이격(101.5%~104.0%) 전략",
    default_stocks=["000660"]
)(SKHynixAlignmentDisparityStrategy)
