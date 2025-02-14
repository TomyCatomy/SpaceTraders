from pydantic import BaseModel


class JettisonCargoReq(BaseModel):
    symbol: str
    units: int
