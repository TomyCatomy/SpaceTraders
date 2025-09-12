from pydantic import BaseModel

from models.fleet.ship import ShipCargo


class JettisonCargoResponse(BaseModel):
    cargo: ShipCargo