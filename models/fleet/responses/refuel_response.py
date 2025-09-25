from pydantic import BaseModel

from models.agents.agent import Agent
from models.fleet.market_transaction import MarketTransaction
from models.fleet.ship import Fuel


class RefuelResponse(BaseModel):
    agent: Agent
    fuel: Fuel
    transaction: MarketTransaction
