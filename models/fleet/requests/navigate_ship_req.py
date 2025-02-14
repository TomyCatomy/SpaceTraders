from pydantic import BaseModel


class NavigateShipReq(BaseModel):
    waypointSymbol: str
