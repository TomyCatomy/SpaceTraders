from pydantic import BaseModel


class RefuelReq(BaseModel):
    units: int = 100
    fromCargo: bool = False
