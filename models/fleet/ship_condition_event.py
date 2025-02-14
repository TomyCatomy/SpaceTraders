from pydantic import BaseModel


class ShipConditionEvent(BaseModel):
    symbol: str
    component: str
    name: str
    description: str
