from pydantic import BaseModel

from models.agents.agent import Agent
from models.fleet.ship import Fuel
from models.fleet.market_transaction import MarketTransaction


class RefuelResponse(BaseModel):
    agent: Agent
    fuel: Fuel
    transaction: MarketTransaction
