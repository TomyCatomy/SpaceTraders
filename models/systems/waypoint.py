from datetime import datetime
from typing import List, Optional, Hashable

from pydantic import BaseModel


class WaypointOrbital(BaseModel):
    symbol: str


class WaypointFaction(BaseModel):
    symbol: str


class WaypointTrait(BaseModel):
    symbol: str
    name: str
    description: str


class WaypointModifier(BaseModel):
    symbol: str
    name: str
    description: str


class WaypointChart(BaseModel):
    waypointSymbol: Optional[str] = None
    submittedBy: str
    submittedOn: datetime


class Waypoint(BaseModel, Hashable):
    symbol: str
    type: str
    systemSymbol: Optional[str] = None
    x: int
    y: int
    orbitals: List[WaypointOrbital] = None
    orbits: Optional[str] = None
    faction: WaypointFaction = None
    traits: List[WaypointTrait] = None
    modifiers: List[WaypointModifier] = None
    chart: WaypointChart = None
    isUnderConstruction: bool = None

    def __hash__(self):
        return hash(self.symbol)
