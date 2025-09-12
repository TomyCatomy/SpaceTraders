from pydantic import BaseModel


class PurchaseCargoReq(BaseModel):
    symbol: str
    units: int
