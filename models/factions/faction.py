from typing import List

from pydantic import BaseModel


class FactionTrait(BaseModel):
    symbol: str
    name: str
    description: str


class Faction(BaseModel):
    symbol: str
    name: str
    description: str
    headquarters: str
    traits: List[FactionTrait]
    isRecruiting: bool
