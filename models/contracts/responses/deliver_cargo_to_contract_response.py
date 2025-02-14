from pydantic import BaseModel

from models.contracts.contract import Contract
from models.fleet.ship import ShipCargo


class DeliverCargoToContractResponse(BaseModel):
    contract: Contract
    cargo: ShipCargo
