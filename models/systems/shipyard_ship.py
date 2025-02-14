from typing import List

from pydantic import BaseModel

from models.fleet.ship import ShipCrew, Mount, ShipModule, ShipEngine, ShipReactor, ShipFrame


class ShipyardShip(BaseModel):
    type: str
    name: str
    description: str
    supply: str
    activity: str
    purchasePrice: int
    frame: ShipFrame
    reactor: ShipReactor
    engine: ShipEngine
    modules: List[ShipModule]
    mounts: List[Mount]
    crew: ShipCrew
