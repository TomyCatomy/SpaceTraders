from datetime import datetime
from typing import List

from pydantic import BaseModel

from models.systems.waypoint import Waypoint


class ShipRegistration(BaseModel):
    name: str
    factionSymbol: str
    role: str


class ShipRoute(BaseModel):
    destination: Waypoint
    origin: Waypoint
    departureTime: datetime
    arrival: datetime


class ShipNav(BaseModel):
    systemSymbol: str
    waypointSymbol: str
    route: ShipRoute
    status: str
    flightMode: str


class ShipCrew(BaseModel):
    current: int
    required: int
    capacity: int
    rotation: str
    morale: int
    wages: int


class Requirements(BaseModel):
    power: int = None
    crew: int = None
    slots: int = None


class ShipFrame(BaseModel):
    symbol: str
    name: str
    description: str
    condition: int
    integrity: int
    moduleSlots: int
    mountingPoints: int
    fuelCapacity: int
    requirements: Requirements


class ShipReactor(BaseModel):
    symbol: str
    name: str
    description: str
    condition: int
    integrity: int
    powerOutput: int
    requirements: Requirements


class ShipEngine(BaseModel):
    symbol: str
    name: str
    description: str
    condition: int
    integrity: int
    speed: int
    requirements: Requirements


class ShipCooldown(BaseModel):
    shipSymbol: str
    totalSeconds: int
    remainingSeconds: int
    expiration: datetime = None


class ShipModule(BaseModel):
    symbol: str
    capacity: int = None
    range: int = None
    name: str
    description: str
    requirements: Requirements


class Mount(BaseModel):
    symbol: str
    name: str
    description: str = None
    strength: int = None
    deposits: List[str] = None
    requirements: Requirements


class ShipInventoryItem(BaseModel):
    symbol: str
    name: str
    description: str
    units: int


class ShipCargo(BaseModel):
    capacity: int
    units: int
    inventory: List[ShipInventoryItem]


class ConsumedFuel(BaseModel):
    amount: int
    timestamp: datetime


class Fuel(BaseModel):
    current: int
    capacity: int
    consumed: ConsumedFuel


class Ship(BaseModel):
    symbol: str
    registration: ShipRegistration
    nav: ShipNav
    crew: ShipCrew
    frame: ShipFrame
    reactor: ShipReactor
    engine: ShipEngine
    cooldown: ShipCooldown
    modules: List[ShipModule]
    mounts: List[Mount]
    cargo: ShipCargo
    fuel: Fuel
