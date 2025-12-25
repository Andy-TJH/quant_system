from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen = True)
class CommissionModel:
    def calc(self, qty: int, price: float) -> float:
        raise NotImplementedError
    
@dataclass(frozen = True)
class FixedCommission(CommissionModel):
    per_trade: float = 0.0
    commission: float = 0.0
    def calc(self, qty: int, price: float) -> float:
        return float(self.per_trade)
    
@dataclass(frozen = True)
class RateCommission(CommissionModel):
    rate: float = 0.0
    min_fee: float = 0.0

    def calc(self, qty: int, price: float) -> float:
        notional = float(qty) * float(price)
        fee = notional * float(self.rate)
        if fee < float(self.min_fee):
            fee = float(self.min_fee)
        return fee
