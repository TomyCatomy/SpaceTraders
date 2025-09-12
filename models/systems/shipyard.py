from typing import List, Optional

from pydantic import BaseModel

from models.fleet.ship import Ship
from models.fleet.shipyard_transaction import ShipyardTransaction
from models.systems.shipyard_ship import ShipyardShip


class ShipType(BaseModel):
    type: str



class Shipyard(BaseModel):
    symbol: str
    shipTypes: List[ShipType]
    transactions: Optional[List[ShipyardTransaction]] = None
    ships: Optional[List[ShipyardShip]] = None
    modificationsFee: int
