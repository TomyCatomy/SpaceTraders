from pydantic import BaseModel

from models.contracts.contract import Contract


class NegotiateContractResponse(BaseModel):
    contract: Contract