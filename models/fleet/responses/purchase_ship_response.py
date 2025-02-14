from pydantic import BaseModel

from models.agents.agent import Agent
from models.fleet.ship import Ship
from models.fleet.shipyard_transaction import ShipyardTransaction


class PurchaseShipResponse(BaseModel):
    agent: Agent
    ship: Ship
    transaction: ShipyardTransaction
