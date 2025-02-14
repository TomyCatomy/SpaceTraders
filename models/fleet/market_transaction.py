from datetime import datetime

from pydantic import BaseModel


class MarketTransaction(BaseModel):
    waypointSymbol: str
    shipSymbol: str
    tradeSymbol: str
    type: str
    units: int
    pricePerUnit: int
    totalPrice: int
    timestamp: datetime
