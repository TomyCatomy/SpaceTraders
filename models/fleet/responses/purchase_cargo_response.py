from pydantic import BaseModel

from models.agents.agent import Agent
from models.fleet.market_transaction import MarketTransaction
from models.fleet.ship import ShipCargo


class PurchaseCargoResponse(BaseModel):
    agent: Agent
    cargo: ShipCargo
    transaction: MarketTransaction
