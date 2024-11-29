from datetime import datetime
from typing import List

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
    waypointSymbol: str = None
    submittedBy: str
    submittedOn: datetime


class Waypoint(BaseModel):
    symbol: str
    type: str
    systemSymbol: str = None
    x: int
    y: int
    orbitals: List[WaypointOrbital] = None
    orbits: str = None
    faction: WaypointFaction = None
    traits: List[WaypointTrait] = None
    modifiers: List[WaypointModifier] = None
    chart: WaypointChart = None
    isUnderConstruction: bool = None
