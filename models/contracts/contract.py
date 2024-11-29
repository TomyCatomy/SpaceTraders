from datetime import datetime
from typing import List

from pydantic import BaseModel


class ContractPayment(BaseModel):
    onAccepted: int
    onFulfilled: int


class ContractOrder(BaseModel):
    tradeSymbol: str
    destinationSymbol: str
    unitsRequired: int
    unitsFulfilled: int


class ContractTerms(BaseModel):
    deadline: datetime
    payment: ContractPayment
    deliver: List[ContractOrder]


class Contract(BaseModel):
    id: str
    factionSymbol: str
    type: str
    terms: ContractTerms
    accepted: bool
    fulfilled: bool
    expiration: datetime
    deadlineToAccept: datetime
