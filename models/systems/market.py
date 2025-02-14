from typing import List, Optional

from pydantic import BaseModel

from models.fleet.market_transaction import MarketTransaction


class MarketItem(BaseModel):
    symbol: str
    name: str
    description: str


class TradeGood(BaseModel):
    symbol: str
    type: str
    tradeVolume: int
    supply: str
    activity: Optional[str] = None
    purchasePrice: int
    sellPrice: int


class Market(BaseModel):
    symbol: str
    exports: List[MarketItem]
    imports: List[MarketItem]
    exchange: List[MarketItem]
    transactions: List[MarketTransaction] = None
    tradeGoods: List[TradeGood] = None
