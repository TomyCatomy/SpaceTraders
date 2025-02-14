from typing import List

from pydantic import BaseModel, Field

from models.fleet.ship import ShipCargo, Cooldown
from models.fleet.ship_condition_event import ShipConditionEvent


class Yield(BaseModel):
    symbol: str
    units: int


class ResourceExtraction(BaseModel):
    shipSymbol: str
    extraction_yield: Yield = Field(..., alias='yield')


class ExtractResourcesResponse(BaseModel):
    cooldown: Cooldown
    extraction: ResourceExtraction
    cargo: ShipCargo
    events: List[ShipConditionEvent]
