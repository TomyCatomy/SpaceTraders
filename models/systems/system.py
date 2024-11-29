from typing import List

from pydantic import BaseModel

from models.systems.waypoint import Waypoint


class SystemFaction(BaseModel):
    symbol: str


class System(BaseModel):
    symbol: str
    sectorSymbol: str
    type: str
    x: int
    y: int
    waypoints: List[Waypoint]
    factions: List[SystemFaction]
