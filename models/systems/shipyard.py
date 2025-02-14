from typing import List

from pydantic import BaseModel

from models.fleet.ship import Ship
from models.fleet.shipyard_transaction import ShipyardTransaction
from models.systems.shipyard_ship import ShipyardShip


class ShipType(BaseModel):
    type: str



class Shipyard(BaseModel):
    symbol: str
    shipTypes: List[ShipType]
    transactions: List[ShipyardTransaction]
    ships: List[ShipyardShip]
    modificationsFee: int
