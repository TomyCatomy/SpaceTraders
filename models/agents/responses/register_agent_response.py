from pydantic import BaseModel

from models.agents.agent import Agent
from models.contracts.contract import Contract
from models.factions.faction import Faction
from models.fleet.ship import Ship


class RegisterAgentResponse(BaseModel):
    agent: Agent
    contract: Contract
    faction: Faction
    ship: Ship
    token: str
