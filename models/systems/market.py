from datetime import datetime
from typing import List

from pydantic import BaseModel


class MarketItem(BaseModel):
    symbol: str
    name: str
    description: str


class Transaction(BaseModel):
    waypointSymbol: str
    shipSymbol: str
    tradeSymbol: str
    type: str
    units: int
    pricePerUnit: int
    totalPrice: int
    timestamp: datetime


class TradeGood(BaseModel):
    symbol: str
    type: str
    tradeVolume: int
    supply: str
    activity: str = None
    purchasePrice: int
    sellPrice: int


class Market(BaseModel):
    symbol: str
    exports: List[MarketItem]
    imports: List[MarketItem]
    exchange: List[MarketItem]
    transactions: List[Transaction] = None
    tradeGoods: List[TradeGood] = None
