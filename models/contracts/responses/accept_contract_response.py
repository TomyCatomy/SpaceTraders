from pydantic import BaseModel

from models.agents.agent import Agent
from models.contracts.contract import Contract


class AcceptContractResponse(BaseModel):
    agent: Agent
    contract: Contract
