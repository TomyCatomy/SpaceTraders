from pydantic import BaseModel


class Agent(BaseModel):
    accountId: str
    symbol: str
    headquarters: str
    credits: int
    startingFaction: str
    shipCount: int
