from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ShipyardTransaction(BaseModel):
    waypointSymbol: str
    shipSymbol: Optional[str] = None
    shipType: str
    price: int
    agent_symbol: str
    timestamp: datetime