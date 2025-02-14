from pydantic import BaseModel


class PurchaseShipReq(BaseModel):
    shipType: str
    waypointSymbol: str
    