from pydantic import BaseModel


class DeliverCargoToContractReq(BaseModel):
    shipSymbol: str
    tradeSymbol: str
    units: int