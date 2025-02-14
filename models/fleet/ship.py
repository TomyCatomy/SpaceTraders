from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from models.fleet.ship_nav import ShipNav


class ShipRegistration(BaseModel):
    name: str
    factionSymbol: str
    role: str


class ShipCrew(BaseModel):
    capacity: int
    required: int
    current: Optional[int] = None
    rotation: Optional[str] = None
    morale: Optional[int] = None
    wages: Optional[int] = None


class Requirements(BaseModel):
    power: Optional[int] = None
    crew: Optional[int] = None
    slots: Optional[int] = None


class ShipFrame(BaseModel):
    symbol: str
    name: str
    description: str
    condition: float
    integrity: float
    moduleSlots: int
    mountingPoints: int
    fuelCapacity: int
    requirements: Requirements


class ShipReactor(BaseModel):
    symbol: str
    name: str
    description: str
    condition: float
    integrity: float
    powerOutput: int
    requirements: Requirements


class ShipEngine(BaseModel):
    symbol: str
    name: str
    description: str
    condition: float
    integrity: float
    speed: int
    requirements: Requirements


class Cooldown(BaseModel):
    shipSymbol: str
    totalSeconds: int
    remainingSeconds: int
    expiration: Optional[datetime] = None


class ShipModule(BaseModel):
    symbol: str
    capacity: Optional[int] = None
    range: Optional[int] = None
    name: str
    description: str
    requirements: Requirements


class Mount(BaseModel):
    symbol: str
    name: str
    description: Optional[str] = None
    strength: Optional[int] = None
    deposits: Optional[List[str]] = None
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
    cooldown: Cooldown
    modules: List[ShipModule]
    mounts: List[Mount]
    cargo: ShipCargo
    fuel: Fuel
